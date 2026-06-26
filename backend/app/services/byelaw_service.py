"""Bye-law upload & validation service (FR-02, FR-03) and basic retrieval.

Upload pipeline:
    1. Validate file extension (configurable allow-list) and size.
    2. Reject exact duplicates (same society registration no. + version).
    3. Persist the file under a structured, collision-free path.
    4. Create the Head (byelaw_master) record in 'Pending' status (FR-02).
    5. Validate document readability and move to 'Validated' or 'Failed' (FR-03).
All steps are logged and audited via upload_history; a failed DB write rolls back
the transaction and removes the orphaned file.
"""
from datetime import datetime, time
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import file_storage
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.logging_config import get_logger
from app.models.byelaw import ByelawMaster, UploadHistory
from app.models.user import User
from app.repositories import byelaw_repository
from app.schemas.byelaw import (
    ByelawListItem,
    ByelawMasterResponse,
    ByelawUploadMetadata,
    ByelawUploadResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.document_validation import validate_document

logger = get_logger(__name__)


def _to_datetime(value) -> Optional[datetime]:
    """Normalize an optional date to a datetime for DateTime columns."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.min)


async def _record_upload_history(
    db: AsyncSession,
    *,
    file_name: str,
    file_size: int,
    status: str,
    uploaded_by: int,
    master_id: Optional[int] = None,
    error_message: Optional[str] = None,
) -> None:
    await byelaw_repository.add_upload_history(
        db,
        UploadHistory(
            master_id=master_id,
            file_name=file_name,
            file_size=file_size,
            upload_status=status,
            error_message=error_message,
            uploaded_by=uploaded_by,
        ),
    )


async def upload_byelaw(
    db: AsyncSession,
    metadata: ByelawUploadMetadata,
    *,
    file_bytes: bytes,
    original_filename: str,
    actor: User,
) -> ByelawUploadResponse:
    file_size = len(file_bytes)
    extension = file_storage.get_extension(original_filename)

    # --- FR-02: extension allow-list ---
    if extension not in settings.allowed_extensions:
        msg = (
            f"Unsupported file type '.{extension or '?'}'. "
            f"Allowed types: {', '.join(sorted(settings.allowed_extensions))}."
        )
        await _record_upload_history(
            db, file_name=original_filename, file_size=file_size,
            status="Failed", uploaded_by=actor.user_id, error_message=msg,
        )
        await db.commit()
        raise BadRequestError(msg)

    # --- FR-02: size limit ---
    if file_size == 0:
        await _record_upload_history(
            db, file_name=original_filename, file_size=0,
            status="Failed", uploaded_by=actor.user_id, error_message="Empty file.",
        )
        await db.commit()
        raise BadRequestError("The uploaded file is empty.")
    if file_size > settings.max_upload_bytes:
        msg = f"File exceeds the maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB."
        await _record_upload_history(
            db, file_name=original_filename, file_size=file_size,
            status="Failed", uploaded_by=actor.user_id, error_message=msg,
        )
        await db.commit()
        raise BadRequestError(msg)

    # --- FR-02: duplicate handling (same society + version) ---
    duplicate = await byelaw_repository.find_duplicate(
        db, metadata.society_registration_no, metadata.byelaw_version
    )
    if duplicate is not None:
        msg = (
            f"A bye-law for society '{metadata.society_registration_no}' "
            f"version '{metadata.byelaw_version}' already exists (id {duplicate.master_id})."
        )
        await _record_upload_history(
            db, file_name=original_filename, file_size=file_size,
            status="Failed", uploaded_by=actor.user_id, error_message=msg,
        )
        await db.commit()
        raise ConflictError(msg)

    # --- FR-09 groundwork: is this a new version for an existing society? ---
    existing_versions = await byelaw_repository.count_versions(db, metadata.society_registration_no)
    is_new_version = existing_versions > 0

    # --- Persist the file to structured storage ---
    target_path = file_storage.build_target_path(metadata.society_registration_no, original_filename)
    stored_path = file_storage.save_bytes(target_path, file_bytes)

    try:
        master = ByelawMaster(
            society_name=metadata.society_name,
            society_registration_no=metadata.society_registration_no,
            society_type=metadata.society_type,
            byelaw_title=metadata.byelaw_title,
            byelaw_version=metadata.byelaw_version,
            is_active=False,
            effective_date=_to_datetime(metadata.effective_date),
            registrar_approval_no=metadata.registrar_approval_no,
            approval_date=_to_datetime(metadata.approval_date),
            source_file_name=original_filename,
            source_file_type=extension.upper(),
            source_file_path=stored_path,
            extraction_status="Pending",
            workflow_status="Draft",
            uploaded_by=actor.user_id,
            uploaded_date=datetime.utcnow(),
            remarks=metadata.remarks,
            created_by=actor.user_id,
            updated_by=actor.user_id,
        )
        master = await byelaw_repository.create_master(db, master)

        await _record_upload_history(
            db, file_name=original_filename, file_size=file_size,
            status="Success", uploaded_by=actor.user_id, master_id=master.master_id,
        )

        # --- FR-03: readability validation ---
        result = validate_document(stored_path, extension.upper())
        if result.is_valid:
            master.extraction_status = "Validated"
        else:
            master.extraction_status = "Failed"
            master.remarks = (master.remarks + " | " if master.remarks else "") + result.message
        master.updated_by = actor.user_id

        await db.commit()
        await db.refresh(master)
    except SQLAlchemyError:
        await db.rollback()
        file_storage.delete_quietly(stored_path)
        logger.exception("Persistence failed during upload; rolled back and removed orphaned file.")
        raise

    logger.info(
        "Bye-law uploaded: id=%s society='%s' version='%s' status=%s by '%s'.",
        master.master_id, master.society_registration_no, master.byelaw_version,
        master.extraction_status, actor.username,
    )

    total_versions = existing_versions + 1
    message = "Bye-law uploaded successfully."
    if not result.is_valid:
        message = "Bye-law uploaded, but document validation failed; the file was retained for review."
    elif is_new_version:
        message = f"Bye-law uploaded as version {total_versions} for this society."

    return ByelawUploadResponse(
        byelaw=ByelawMasterResponse.model_validate(master),
        validation_passed=result.is_valid,
        validation_message=result.message,
        total_versions=total_versions,
        is_new_version=is_new_version,
        message=message,
    )


async def get_byelaw(db: AsyncSession, master_id: int) -> ByelawMasterResponse:
    master = await byelaw_repository.get_master_by_id(db, master_id)
    if master is None:
        raise NotFoundError(f"Bye-law with id {master_id} was not found.")
    return ByelawMasterResponse.model_validate(master)


async def list_byelaws(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    search: Optional[str],
    registration_no: Optional[str],
    extraction_status: Optional[str],
    workflow_status: Optional[str],
) -> PaginatedResponse[ByelawListItem]:
    rows, total = await byelaw_repository.list_masters(
        db, page=page, page_size=page_size, search=search, registration_no=registration_no,
        extraction_status=extraction_status, workflow_status=workflow_status,
    )
    items = [ByelawListItem.model_validate(r) for r in rows]
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)
