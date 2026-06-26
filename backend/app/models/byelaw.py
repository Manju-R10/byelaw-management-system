from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Enum, Index
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import relationship
from app.database import Base

class ByelawMaster(Base):
    __tablename__ = "byelaw_master"

    master_id = Column(Integer, primary_key=True, autoincrement=True)
    society_name = Column(String(255), nullable=False)
    society_registration_no = Column(String(100), nullable=False, index=True)
    society_type = Column(String(100), nullable=True)
    byelaw_title = Column(String(255), nullable=False)
    byelaw_version = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    effective_date = Column(DateTime, nullable=True)
    registrar_approval_no = Column(String(100), nullable=True)
    approval_date = Column(DateTime, nullable=True)
    source_file_name = Column(String(255), nullable=False)
    source_file_type = Column(Enum("PDF", "DOCX", "DOC", name="file_type_enum"), nullable=False)
    source_file_path = Column(String(500), nullable=False)
    total_chapters = Column(Integer, default=0, nullable=False)
    total_clauses = Column(Integer, default=0, nullable=False)
    
    extraction_status = Column(
        Enum("Pending", "Validated", "Processing", "Completed", "Failed", "Reviewed", name="extraction_status_enum"),
        default="Pending",
        nullable=False,
        index=True
    )
    workflow_status = Column(
        Enum("Draft", "Submitted", "Under Review", "Verified", "Approved", "Rejected", "Published", name="workflow_status_enum"),
        default="Draft",
        nullable=False,
        index=True
    )

    uploaded_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    uploaded_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    reviewed_date = Column(DateTime, nullable=True)
    remarks = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    clauses = relationship("ByelawClause", back_populates="master", cascade="all, delete-orphan")
    comments = relationship("ByelawComment", back_populates="master", cascade="all, delete-orphan")
    workflow_history = relationship("WorkflowHistory", back_populates="master", cascade="all, delete-orphan")
    uploads = relationship("UploadHistory", back_populates="master")

class ByelawClause(Base):
    __tablename__ = "byelaw_clause"
    __table_args__ = (
        # FULLTEXT index backing clause keyword search (FR-08). Declared so the model
        # metadata matches the index created by the initial migration.
        Index("ft_clause_text", "clause_text", mysql_prefix="FULLTEXT"),
        # Composite index for fast, correctly ordered clause reconstruction (FR-06/FR-10).
        Index("ix_clause_master_display", "master_id", "display_order"),
    )

    clause_id = Column(Integer, primary_key=True, autoincrement=True)
    master_id = Column(Integer, ForeignKey("byelaw_master.master_id", ondelete="CASCADE"), nullable=False, index=True)
    parent_clause_id = Column(Integer, ForeignKey("byelaw_clause.clause_id", ondelete="CASCADE"), nullable=True, index=True)
    clause_level = Column(Integer, nullable=False) # 1=Chapter, 2=Clause, 3=Sub-clause, 4+=Nested
    chapter_no = Column(String(50), nullable=True)
    clause_no = Column(String(50), nullable=True)
    clause_title = Column(String(255), nullable=True)
    # MEDIUMTEXT (16 MB) rather than TEXT (64 KB): a single extracted clause can be
    # large when long passages lie between detected headings in a source document.
    clause_text = Column(MEDIUMTEXT, nullable=False)
    display_order = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    master = relationship("ByelawMaster", back_populates="clauses")
    parent = relationship("ByelawClause", remote_side=[clause_id], backref="sub_clauses")

class ByelawComment(Base):
    __tablename__ = "byelaw_comments"

    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    master_id = Column(Integer, ForeignKey("byelaw_master.master_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    comment_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    master = relationship("ByelawMaster", back_populates="comments")

class WorkflowHistory(Base):
    __tablename__ = "workflow_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    master_id = Column(Integer, ForeignKey("byelaw_master.master_id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(
        Enum("Draft", "Submitted", "Under Review", "Verified", "Approved", "Rejected", "Published", name="workflow_status_enum"),
        nullable=True
    )
    new_status = Column(
        Enum("Draft", "Submitted", "Under Review", "Verified", "Approved", "Rejected", "Published", name="workflow_status_enum"),
        nullable=False
    )
    changed_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    remarks = Column(Text, nullable=True)

    # Relationships
    master = relationship("ByelawMaster", back_populates="workflow_history")

class UploadHistory(Base):
    __tablename__ = "upload_history"

    upload_id = Column(Integer, primary_key=True, autoincrement=True)
    master_id = Column(Integer, ForeignKey("byelaw_master.master_id", ondelete="SET NULL"), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_status = Column(Enum("Success", "Failed", name="upload_status_enum"), nullable=False)
    error_message = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    master = relationship("ByelawMaster", back_populates="uploads")
