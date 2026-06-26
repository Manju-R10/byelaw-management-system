from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    table_name = Column(String(100), nullable=True)
    record_id = Column(Integer, nullable=True)
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(255), nullable=True)

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
