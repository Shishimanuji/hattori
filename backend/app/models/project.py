"""Project database model"""
from sqlalchemy import Column, String, Text, Numeric, Date, DateTime, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
import uuid
import enum

from app.core.database import Base


class ProjectStatus(str, enum.Enum):
    """Project status enumeration"""
    ACTIVE = "Active"
    PENDING = "Pending"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"


class Project(Base):
    """Project model for organizing resources"""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default=ProjectStatus.ACTIVE)
    budget = Column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    allocated_budget = Column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="projects")
    resources = relationship("Resource", back_populates="project", cascade="all, delete-orphan")
    allocations = relationship("Allocation", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_projects_owner_id", "owner_id"),
        Index("idx_projects_status", "status"),
        Index("idx_projects_deleted_at", "deleted_at"),
        Index("idx_projects_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def remaining_budget(self) -> Decimal:
        """Calculate remaining budget"""
        return Decimal(str(self.budget)) - Decimal(str(self.allocated_budget))

    @property
    def utilization_percentage(self) -> float:
        """Calculate budget utilization percentage"""
        budget_float = float(self.budget)
        if budget_float == 0:
            return 0.0
        allocated_float = float(self.allocated_budget)
        return (allocated_float / budget_float) * 100

    def is_deleted(self) -> bool:
        """Check if project is soft deleted"""
        return self.deleted_at is not None

    def can_add_resources(self) -> bool:
        """Check if project can receive new resources"""
        return not self.is_deleted() and self.status == ProjectStatus.ACTIVE
