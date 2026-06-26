"""Bye-law master request/response schemas (FR-02, FR-03)."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ByelawUploadMetadata(BaseModel):
    """Descriptive metadata captured alongside an uploaded bye-law document (FR-02)."""

    society_name: str = Field(..., min_length=1, max_length=255)
    society_registration_no: str = Field(..., min_length=1, max_length=100)
    society_type: Optional[str] = Field(None, max_length=100)
    byelaw_title: str = Field(..., min_length=1, max_length=255)
    byelaw_version: str = Field(..., min_length=1, max_length=50)
    effective_date: Optional[date] = None
    registrar_approval_no: Optional[str] = Field(None, max_length=100)
    approval_date: Optional[date] = None
    remarks: Optional[str] = None


class ByelawMasterResponse(BaseModel):
    """Full representation of a bye-law Head record."""

    model_config = ConfigDict(from_attributes=True)

    master_id: int
    society_name: str
    society_registration_no: str
    society_type: Optional[str] = None
    byelaw_title: str
    byelaw_version: str
    is_active: bool
    effective_date: Optional[datetime] = None
    registrar_approval_no: Optional[str] = None
    approval_date: Optional[datetime] = None
    source_file_name: str
    source_file_type: str
    total_chapters: int
    total_clauses: int
    extraction_status: str
    workflow_status: str
    uploaded_by: int
    uploaded_date: datetime
    reviewed_by: Optional[int] = None
    reviewed_date: Optional[datetime] = None
    remarks: Optional[str] = None
    created_at: datetime


class ByelawListItem(BaseModel):
    """Compact representation for list views."""

    model_config = ConfigDict(from_attributes=True)

    master_id: int
    society_name: str
    society_registration_no: str
    byelaw_title: str
    byelaw_version: str
    is_active: bool
    source_file_type: str
    total_clauses: int
    extraction_status: str
    workflow_status: str
    uploaded_by: int
    uploaded_date: datetime


class ByelawUploadResponse(BaseModel):
    """Result of an upload: the created record plus validation and versioning info."""

    byelaw: ByelawMasterResponse
    validation_passed: bool
    validation_message: str
    total_versions: int
    is_new_version: bool
    message: str
