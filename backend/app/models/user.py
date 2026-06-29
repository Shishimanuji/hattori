"""User database model"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class UserStatus(str, enum.Enum):
    """User status enumeration"""
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "Admin"
    MANAGER = "Manager"
    ANALYST = "Analyst"
    VIEWER = "Viewer"


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    employee_id = Column(String(50), unique=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    designation = Column(String(100), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    status = Column(String(20), nullable=False, default=UserStatus.ACTIVE)
    is_active = Column(Boolean, nullable=False, default=True)
    force_password_change = Column(Boolean, nullable=False, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    role = relationship("Role", back_populates="users")
    owned_projects = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    created_projects = relationship("Project", back_populates="creator", foreign_keys="Project.created_by")
    created_assets = relationship("Asset", back_populates="creator", foreign_keys="Asset.created_by")
    custodial_assets = relationship("Asset", back_populates="custodian", foreign_keys="Asset.custodian_id")
    uploaded_documents = relationship("Document", back_populates="uploader")
    resolved_alerts = relationship("Alert", back_populates="resolver")
    import_history = relationship("ImportHistory", back_populates="uploader", foreign_keys="ImportHistory.uploaded_by")
    report_templates = relationship("ReportTemplate", back_populates="creator")

    __table_args__ = (
        Index("idx_users_employee_id", "employee_id"),
        Index("idx_users_role_id", "role_id"),
        Index("idx_users_status", "status"),
        Index("idx_users_department", "department"),
        Index("idx_users_deleted_at", "deleted_at"),
        Index("idx_users_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, full_name={self.full_name})>"

    @property
    def display_name(self) -> str:
        """Get user's display name"""
        return self.full_name or self.username

    def has_permission(self, required_level: int) -> bool:
        """Check if user has required permission level"""
        return self.role and self.role.has_permission_level(required_level)

    def is_admin(self) -> bool:
        """Check if user has admin privileges"""
        return self.role and self.role.role_name in ["Super Admin", "Admin"]

    def can_manage_projects(self) -> bool:
        """Check if user can manage projects"""
        return self.role and self.role.role_name in ["Super Admin", "Admin", "Project Manager"]
