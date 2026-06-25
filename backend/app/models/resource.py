"""Resource and allocation database models"""
from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ResourceStatus(str, enum.Enum):
    """Resource status enumeration"""
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class Resource(Base):
    """Resource model for tracking assets within projects"""
    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    asset_type_id = Column(UUID(as_uuid=True), ForeignKey("asset_types.id"), nullable=False)
    name = Column(String(255), nullable=False)
    cost = Column(Numeric(15, 2), nullable=False)
    allocation_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default=ResourceStatus.ACTIVE)
    custom_field_values = Column(JSONB, nullable=False, default={})
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="resources")
    asset_type = relationship("AssetType", back_populates="resources")
    creator = relationship("User", foreign_keys=[created_by])
    allocations = relationship("Allocation", back_populates="resource", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_resources_project_id", "project_id"),
        Index("idx_resources_asset_type_id", "asset_type_id"),
        Index("idx_resources_status", "status"),
        Index("idx_resources_deleted_at", "deleted_at"),
        Index("idx_resources_allocation_date", "allocation_date"),
    )

    def __repr__(self) -> str:
        return f"<Resource(id={self.id}, name={self.name}, status={self.status})>"


class Allocation(Base):
    """Allocation model for tracking resource allocation history and budget"""
    __tablename__ = "allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    cost_at_allocation = Column(Numeric(15, 2), nullable=False)
    allocated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    deallocated_at = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    resource = relationship("Resource", back_populates="allocations")
    project = relationship("Project", back_populates="allocations")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_allocations_resource_id", "resource_id"),
        Index("idx_allocations_project_id", "project_id"),
        Index("idx_allocations_allocated_at", "allocated_at"),
    )

    def __repr__(self) -> str:
        return f"<Allocation(id={self.id}, resource_id={self.resource_id}, cost={self.cost_at_allocation})>"

    @property
    def is_active(self) -> bool:
        """Check if allocation is still active"""
        return self.deallocated_at is None
