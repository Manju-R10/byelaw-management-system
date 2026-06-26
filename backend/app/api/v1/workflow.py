"""Approval-workflow, version and notification endpoints (FR-07/FR-09)."""
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_permission
from app.database import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.workflow import (
    NotificationListResponse,
    SocietyVersionsResponse,
    WorkflowActionRequest,
    WorkflowHistoryItem,
    WorkflowStatusResponse,
)
from app.services import workflow_service

router = APIRouter(prefix="/byelaws", tags=["Approval Workflow"])
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _remarks(payload: Optional[WorkflowActionRequest]) -> Optional[str]:
    return payload.remarks if payload else None


@router.post("/{master_id}/workflow/submit", response_model=WorkflowStatusResponse,
             summary="Submit a Draft bye-law for review")
async def submit(
    master_id: int = Path(..., ge=1),
    payload: Optional[WorkflowActionRequest] = Body(None),
    actor: User = Depends(require_permission("BYELAW_EDIT")),
    db: AsyncSession = Depends(get_db),
) -> WorkflowStatusResponse:
    return await workflow_service.transition(db, master_id, "submit", actor, _remarks(payload))


@router.post("/{master_id}/workflow/start-review", response_model=WorkflowStatusResponse,
             summary="Begin reviewing a submitted bye-law")
async def start_review(
    master_id: int = Path(..., ge=1),
    payload: Optional[WorkflowActionRequest] = Body(None),
    actor: User = Depends(require_permission("BYELAW_VERIFY")),
    db: AsyncSession = Depends(get_db),
) -> WorkflowStatusResponse:
    return await workflow_service.transition(db, master_id, "start_review", actor, _remarks(payload))


@router.post("/{master_id}/workflow/verify", response_model=WorkflowStatusResponse,
             summary="Verify an under-review bye-law")
async def verify(
    master_id: int = Path(..., ge=1),
    payload: Optional[WorkflowActionRequest] = Body(None),
    actor: User = Depends(require_permission("BYELAW_VERIFY")),
    db: AsyncSession = Depends(get_db),
) -> WorkflowStatusResponse:
    return await workflow_service.transition(db, master_id, "verify", actor, _remarks(payload))


@router.post("/{master_id}/workflow/approve", response_model=WorkflowStatusResponse,
             summary="Approve a verified bye-law")
async def approve(
    master_id: int = Path(..., ge=1),
    payload: Optional[WorkflowActionRequest] = Body(None),
    actor: User = Depends(require_permission("BYELAW_VERIFY")),
    db: AsyncSession = Depends(get_db),
) -> WorkflowStatusResponse:
    return await workflow_service.transition(db, master_id, "approve", actor, _remarks(payload))


@router.post("/{master_id}/workflow/reject", response_model=WorkflowStatusResponse,
             summary="Reject a bye-law back to the uploader (remarks required)")
async def reject(
    master_id: int = Path(..., ge=1),
    payload: Optional[WorkflowActionRequest] = Body(None),
    actor: User = Depends(require_permission("BYELAW_VERIFY")),
    db: AsyncSession = Depends(get_db),
) -> WorkflowStatusResponse:
    # Remarks are mandatory for rejection; enforced in the service for a consistent 400.
    return await workflow_service.transition(db, master_id, "reject", actor, _remarks(payload))


@router.post("/{master_id}/workflow/publish", response_model=WorkflowStatusResponse,
             summary="Publish an approved bye-law as the active version (FR-09)")
async def publish(
    master_id: int = Path(..., ge=1),
    payload: Optional[WorkflowActionRequest] = Body(None),
    actor: User = Depends(require_permission("BYELAW_PUBLISH")),
    db: AsyncSession = Depends(get_db),
) -> WorkflowStatusResponse:
    return await workflow_service.transition(db, master_id, "publish", actor, _remarks(payload))


@router.post("/{master_id}/workflow/return-to-draft", response_model=WorkflowStatusResponse,
             summary="Return a rejected bye-law to Draft for correction")
async def return_to_draft(
    master_id: int = Path(..., ge=1),
    payload: Optional[WorkflowActionRequest] = Body(None),
    actor: User = Depends(require_permission("BYELAW_EDIT")),
    db: AsyncSession = Depends(get_db),
) -> WorkflowStatusResponse:
    return await workflow_service.transition(db, master_id, "return_to_draft", actor, _remarks(payload))


@router.get("/{master_id}/workflow/history", response_model=List[WorkflowHistoryItem],
            summary="Workflow transition history for a bye-law")
async def workflow_history(
    master_id: int = Path(..., ge=1),
    _: User = Depends(require_permission("BYELAW_SEARCH")),
    db: AsyncSession = Depends(get_db),
) -> List[WorkflowHistoryItem]:
    return await workflow_service.get_history(db, master_id)


@router.get("/{master_id}/versions", response_model=SocietyVersionsResponse,
            summary="All versions for the bye-law's society, with the active one (FR-09)")
async def society_versions(
    master_id: int = Path(..., ge=1),
    _: User = Depends(require_permission("BYELAW_SEARCH")),
    db: AsyncSession = Depends(get_db),
) -> SocietyVersionsResponse:
    return await workflow_service.get_versions(db, master_id)


# --- Notifications (any authenticated user, for their own notifications) ---------------

@notifications_router.get("", response_model=NotificationListResponse,
                          summary="List my notifications")
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    return await workflow_service.list_notifications(
        db, current_user, unread_only=unread_only, page=page, page_size=page_size
    )


@notifications_router.post("/{notification_id}/read", response_model=MessageResponse,
                           summary="Mark a notification as read")
async def mark_read(
    notification_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await workflow_service.mark_notification_read(db, notification_id, current_user)
    return MessageResponse(message="Notification marked as read.")


@notifications_router.post("/read-all", response_model=MessageResponse,
                           summary="Mark all my notifications as read")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    count = await workflow_service.mark_all_notifications_read(db, current_user)
    return MessageResponse(message=f"{count} notification(s) marked as read.")
