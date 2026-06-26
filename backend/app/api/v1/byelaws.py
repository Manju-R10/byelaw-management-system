"""Bye-law upload, validation and retrieval endpoints (FR-02, FR-03)."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Path, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_permission
from app.database import get_db
from app.models.user import User
from app.schemas.byelaw import (
    ByelawListItem,
    ByelawMasterResponse,
    ByelawUploadMetadata,
    ByelawUploadResponse,
)
from app.schemas.common import PaginatedResponse
from app.services import byelaw_service

router = APIRouter(prefix="/byelaws", tags=["Bye-law Upload"])


@router.post(
    "/upload",
    response_model=ByelawUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a bye-law document with metadata (FR-02/FR-03)",
)
async def upload_byelaw(
    file: UploadFile = File(..., description="Bye-law document (.pdf/.doc/.docx)"),
    society_name: str = Form(..., min_length=1, max_length=255),
    society_registration_no: str = Form(..., min_length=1, max_length=100),
    byelaw_title: str = Form(..., min_length=1, max_length=255),
    byelaw_version: str = Form(..., min_length=1, max_length=50),
    society_type: Optional[str] = Form(None, max_length=100),
    effective_date: Optional[date] = Form(None),
    registrar_approval_no: Optional[str] = Form(None, max_length=100),
    approval_date: Optional[date] = Form(None),
    remarks: Optional[str] = Form(None),
    actor: User = Depends(require_permission("BYELAW_UPLOAD")),
    db: AsyncSession = Depends(get_db),
) -> ByelawUploadResponse:
    """Accept a bye-law file plus society/bye-law metadata, validate and store it."""
    metadata = ByelawUploadMetadata(
        society_name=society_name,
        society_registration_no=society_registration_no,
        society_type=society_type,
        byelaw_title=byelaw_title,
        byelaw_version=byelaw_version,
        effective_date=effective_date,
        registrar_approval_no=registrar_approval_no,
        approval_date=approval_date,
        remarks=remarks,
    )
    file_bytes = await file.read()
    return await byelaw_service.upload_byelaw(
        db,
        metadata,
        file_bytes=file_bytes,
        original_filename=file.filename or "upload",
        actor=actor,
    )


@router.get(
    "",
    response_model=PaginatedResponse[ByelawListItem],
    summary="List uploaded bye-laws (paginated, filterable)",
)
async def list_byelaws(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Match society name, title or registration no."),
    registration_no: Optional[str] = Query(None, description="All versions for a society"),
    extraction_status: Optional[str] = Query(None, description="Pending/Validated/Processing/Completed/Failed/Reviewed"),
    workflow_status: Optional[str] = Query(None, description="Draft/Submitted/Under Review/Verified/Approved/Rejected/Published"),
    _: User = Depends(require_permission("BYELAW_SEARCH")),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ByelawListItem]:
    return await byelaw_service.list_byelaws(
        db, page=page, page_size=page_size, search=search, registration_no=registration_no,
        extraction_status=extraction_status, workflow_status=workflow_status,
    )


@router.get(
    "/{master_id}",
    response_model=ByelawMasterResponse,
    summary="Get a single bye-law Head record by id",
)
async def get_byelaw(
    master_id: int = Path(..., ge=1),
    _: User = Depends(require_permission("BYELAW_SEARCH")),
    db: AsyncSession = Depends(get_db),
) -> ByelawMasterResponse:
    return await byelaw_service.get_byelaw(db, master_id)
