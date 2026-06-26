"""Approval-workflow, version and notification schemas (FR-07/FR-09)."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkflowActionRequest(BaseModel):
    """Optional remarks accompanying a workflow transition (required for rejection)."""

    remarks: Optional[str] = Field(None, max_length=2000)


class WorkflowStatusResponse(BaseModel):
    master_id: int
    workflow_status: str
    extraction_status: str
    is_active: bool
    message: str


class WorkflowHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    previous_status: Optional[str] = None
    new_status: str
    changed_by: int
    changed_at: datetime
    remarks: Optional[str] = None


class VersionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    master_id: int
    byelaw_version: str
    is_active: bool
    workflow_status: str
    extraction_status: str
    effective_date: Optional[datetime] = None
    uploaded_date: datetime


class SocietyVersionsResponse(BaseModel):
    society_registration_no: str
    active_master_id: Optional[int] = None
    total_versions: int
    versions: List[VersionItem]


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notification_id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
