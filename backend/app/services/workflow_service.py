"""Approval-workflow service (FR-07 verification/approval, FR-09 version activation).

State machine (workflow_status):

    Draft ──submit──> Submitted ──start_review──> Under Review ──verify──> Verified
      ^                  │                │                                  │
      │ return_to_draft  └──reject──┐     └──reject──┐                approve │
      │                             v                v                        v
    Rejected <───────────────── (reject) ────────────────────────────── (from Verified)
      │                                                                       │
      └──submit──> Submitted                                            Approved ──publish──> Published (active)

Publishing makes a version the single active one for its society (FR-09); all other
versions of the same society are deactivated in the same transaction.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.logging_config import get_logger
from app.models.audit import Notification
from app.models.byelaw import ByelawMaster, WorkflowHistory
from app.models.user import User
from app.repositories import byelaw_repository, clause_repository, workflow_repository
from app.schemas.workflow import (
    NotificationListResponse,
    NotificationResponse,
    SocietyVersionsResponse,
    VersionItem,
    WorkflowHistoryItem,
    WorkflowStatusResponse,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class Transition:
    action: str
    from_states: tuple
    to_state: str
    permission: str
    notify_roles: tuple = ()      # roles to notify (e.g. reviewers)
    notify_uploader: bool = False
    require_remarks: bool = False


# The authoritative transition table — the single source of truth for the state machine.
TRANSITIONS: dict[str, Transition] = {
    "submit": Transition(
        "submit", ("Draft", "Rejected"), "Submitted", "BYELAW_EDIT",
        notify_roles=("Verifying Officer", "Administrator"),
    ),
    "start_review": Transition(
        "start_review", ("Submitted",), "Under Review", "BYELAW_VERIFY", notify_uploader=True,
    ),
    "verify": Transition(
        "verify", ("Under Review",), "Verified", "BYELAW_VERIFY", notify_uploader=True,
    ),
    "approve": Transition(
        "approve", ("Verified",), "Approved", "BYELAW_VERIFY",
        notify_roles=("Administrator",), notify_uploader=True,
    ),
    "reject": Transition(
        "reject", ("Submitted", "Under Review", "Verified"), "Rejected", "BYELAW_VERIFY",
        notify_uploader=True, require_remarks=True,
    ),
    "publish": Transition(
        "publish", ("Approved",), "Published", "BYELAW_PUBLISH", notify_uploader=True,
    ),
    "return_to_draft": Transition(
        "return_to_draft", ("Rejected",), "Draft", "BYELAW_EDIT",
    ),
}


async def _get_master_or_404(db: AsyncSession, master_id: int) -> ByelawMaster:
    master = await byelaw_repository.get_master_by_id(db, master_id)
    if master is None:
        raise NotFoundError(f"Bye-law with id {master_id} was not found.")
    return master


async def _notify(db: AsyncSession, user_ids: Sequence[int], title: str, message: str) -> None:
    seen = set()
    for uid in user_ids:
        if uid is None or uid in seen:
            continue
        seen.add(uid)
        await workflow_repository.add_notification(
            db, Notification(user_id=uid, title=title, message=message)
        )


async def transition(
    db: AsyncSession, master_id: int, action: str, actor: User, remarks: Optional[str]
) -> WorkflowStatusResponse:
    spec = TRANSITIONS[action]
    master = await _get_master_or_404(db, master_id)

    if master.workflow_status not in spec.from_states:
        raise ConflictError(
            f"Action '{action}' is not allowed from status '{master.workflow_status}'. "
            f"Allowed from: {', '.join(spec.from_states)}."
        )
    if spec.require_remarks and not (remarks and remarks.strip()):
        raise BadRequestError(f"Remarks are required when performing '{action}'.")

    # Submitting requires that clauses have actually been extracted.
    if action == "submit":
        if await clause_repository.count_by_master(db, master_id) == 0:
            raise BadRequestError("Cannot submit a bye-law that has no extracted clauses.")
        if master.extraction_status not in ("Completed", "Reviewed"):
            raise BadRequestError(
                "Cannot submit until extraction is completed (and ideally reviewed)."
            )

    previous = master.workflow_status
    master.workflow_status = spec.to_state
    master.updated_by = actor.user_id

    # FR-09: publishing activates this version and deactivates all others for the society.
    if action == "publish":
        master.is_active = True
        deactivated = await workflow_repository.deactivate_other_versions(
            db, master.society_registration_no, master.master_id
        )
        logger.info("Published master_id=%s; deactivated %s prior active version(s).", master_id, deactivated)
    if action == "return_to_draft":
        master.is_active = False

    await workflow_repository.add_history(
        db,
        WorkflowHistory(
            master_id=master_id,
            previous_status=previous,
            new_status=spec.to_state,
            changed_by=actor.user_id,
            remarks=remarks,
        ),
    )

    # Notifications.
    title = f"Bye-law '{master.byelaw_title}' ({master.society_registration_no}) — {spec.to_state}"
    msg = f"Status changed from '{previous}' to '{spec.to_state}' by {actor.full_name}."
    if remarks:
        msg += f" Remarks: {remarks}"
    recipients: List[int] = []
    if spec.notify_uploader:
        recipients.append(master.uploaded_by)
    if spec.notify_roles:
        role_ids = await workflow_repository.get_active_user_ids_by_roles(db, spec.notify_roles)
        recipients.extend(role_ids)
    # Never notify the actor about their own action.
    recipients = [r for r in recipients if r != actor.user_id]
    if recipients:
        await _notify(db, recipients, title, msg)

    await db.commit()
    await db.refresh(master)
    logger.info("Workflow %s: master_id=%s %s->%s by '%s'.", action, master_id, previous, spec.to_state, actor.username)

    return WorkflowStatusResponse(
        master_id=master.master_id,
        workflow_status=master.workflow_status,
        extraction_status=master.extraction_status,
        is_active=master.is_active,
        message=f"Bye-law moved to '{master.workflow_status}'.",
    )


async def get_history(db: AsyncSession, master_id: int) -> List[WorkflowHistoryItem]:
    await _get_master_or_404(db, master_id)
    rows = await workflow_repository.list_history(db, master_id)
    return [WorkflowHistoryItem.model_validate(r) for r in rows]


async def get_versions(db: AsyncSession, master_id: int) -> SocietyVersionsResponse:
    master = await _get_master_or_404(db, master_id)
    rows = await workflow_repository.list_versions(db, master.society_registration_no)
    active = next((r.master_id for r in rows if r.is_active), None)
    return SocietyVersionsResponse(
        society_registration_no=master.society_registration_no,
        active_master_id=active,
        total_versions=len(rows),
        versions=[VersionItem.model_validate(r) for r in rows],
    )


# --- Notifications ---------------------------------------------------------------------

async def list_notifications(
    db: AsyncSession, user: User, *, unread_only: bool, page: int, page_size: int
) -> NotificationListResponse:
    rows, total, unread = await workflow_repository.list_notifications(
        db, user.user_id, unread_only=unread_only, page=page, page_size=page_size
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(r) for r in rows],
        total=total,
        unread_count=unread,
        page=page,
        page_size=page_size,
    )


async def mark_notification_read(db: AsyncSession, notification_id: int, user: User) -> None:
    notif = await workflow_repository.get_notification(db, notification_id)
    if notif is None or notif.user_id != user.user_id:
        raise NotFoundError("Notification not found.")
    await workflow_repository.mark_notification_read(db, notification_id, user.user_id)
    await db.commit()


async def mark_all_notifications_read(db: AsyncSession, user: User) -> int:
    count = await workflow_repository.mark_all_read(db, user.user_id)
    await db.commit()
    return count
