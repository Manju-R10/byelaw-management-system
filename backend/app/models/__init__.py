from app.database import Base
from app.models.user import Role, Permission, User, UserSession, role_permissions
from app.models.byelaw import ByelawMaster, ByelawClause, ByelawComment, WorkflowHistory, UploadHistory
from app.models.audit import AuditLog, Notification

# Ensure all models are loaded onto the Base.metadata
__all__ = [
    "Base",
    "Role",
    "Permission",
    "User",
    "UserSession",
    "role_permissions",
    "ByelawMaster",
    "ByelawClause",
    "ByelawComment",
    "WorkflowHistory",
    "UploadHistory",
    "AuditLog",
    "Notification"
]
