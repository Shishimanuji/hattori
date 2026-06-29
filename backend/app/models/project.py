"""Project database model"""
from sqlalchemy import Column, String, Text, Numeric, Date, DateTime, ForeignKey, Index, CheckConstraint, Integer
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
    """Project model for organizing resources and assets"""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False, unique=True)  # project_name in new schema
    description = Column(Text, nullable=True)
    client = Column(String(255), nullable=True)
    vendor = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default=ProjectStatus.ACTIVE)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=True)
    
    # Legacy fields (kept for backward compatibility)
    budget = Column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    allocated_budget = Column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # User relationships
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_projects")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_projects")
    template = relationship("Template", back_populates="projects")
    project_summary = relationship("ProjectSummary", back_populates="project", uselist=False)
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project")
    alerts = relationship("Alert", back_populates="project")
    import_history = relationship("ImportHistory", back_populates="project")
    
    # Legacy relationships (to be deprecated)
    resources = relationship("Resource", back_populates="project", cascade="all, delete-orphan")
    allocations = relationship("Allocation", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_projects_project_code", "project_code"),
        Index("idx_projects_template_id", "template_id"),
        Index("idx_projects_created_by", "created_by"),
        Index("idx_projects_client", "client"),
        Index("idx_projects_owner_id", "owner_id"),
        Index("idx_projects_status", "status"),
        Index("idx_projects_deleted_at", "deleted_at"),
        Index("idx_projects_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, code={self.project_code}, name={self.name}, status={self.status})>"

    @property
    def remaining_budget(self) -> Decimal:
        """Calculate remaining budget (legacy property)"""
        return Decimal(str(self.budget)) - Decimal(str(self.allocated_budget))

    @property
    def utilization_percentage(self) -> float:
        """Calculate budget utilization percentage (legacy property)"""
        budget_float = float(self.budget)
        if budget_float == 0:
            return 0.0
        allocated_float = float(self.allocated_budget)
        return (allocated_float / budget_float) * 100

    def is_deleted(self) -> bool:
        """Check if project is soft deleted"""
        return self.deleted_at is not None

    def can_add_assets(self) -> bool:
        """Check if project can receive new assets"""
        return not self.is_deleted() and self.status == ProjectStatus.ACTIVE

    @property
    def total_assets(self) -> int:
        """Get total number of active assets"""
        return len([asset for asset in self.assets if asset.deleted_at is None])

    @property
    def asset_summary(self) -> dict:
        """Get summary of assets by resource type"""
        summary = {}
        active_assets = [asset for asset in self.assets if asset.deleted_at is None]
        
        for asset in active_assets:
            rt_name = asset.resource_type.display_name if asset.resource_type else "Unknown"
            if rt_name not in summary:
                summary[rt_name] = {"count": 0, "total_cost": Decimal("0")}
            summary[rt_name]["count"] += 1
            summary[rt_name]["total_cost"] += asset.cost or Decimal("0")
        
        return summary


class ProjectSummary(Base):
    """Project summary model for SEAW sheet data"""
    __tablename__ = "project_summary"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, unique=True)
    prepared_by = Column(String(255), nullable=True)
    approved_by = Column(String(255), nullable=True)
    project_duration = Column(Integer, nullable=True)  # in days
    remarks = Column(Text, nullable=True)
    total_budget = Column(Numeric(15, 2), nullable=True)
    completion_percentage = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    version = Column(String(20), nullable=False, default="1.0")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="project_summary")

    __table_args__ = (
        Index("idx_project_summary_project_id", "project_id"),
        CheckConstraint("completion_percentage >= 0 AND completion_percentage <= 100", 
                       name="ck_project_summary_completion_percentage"),
    )

    def __repr__(self) -> str:
        return f"<ProjectSummary(project_id={self.project_id}, completion={self.completion_percentage}%)>"
