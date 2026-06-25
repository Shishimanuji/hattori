"""Audit log database model"""
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class AuditOperation(str, enum.Enum):
    """Audit operation type enumeration"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
    REPORT_DOWNLOAD = "REPORT_DOWNLOAD"
    ROLE_CHANGE = "ROLE_CHANGE"
    CONFIG_CHANGE = "CONFIG_CHANGE"


class AuditLogStatus(str, enum.Enum):
    """Audit log status enumeration"""
    SUCCESS = "success"
    FAILURE = "failure"


class AuditLog(Base):
    """Audit log model for tracking all system changes"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    operation = Column(String(20), nullable=False)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default=AuditLogStatus.SUCCESS)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_operation", "operation"),
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_audit_logs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, operation={self.operation}, entity={self.entity_type})>"
