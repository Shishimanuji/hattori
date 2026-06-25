"""Asset type and custom field database models"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, Index, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class FieldType(str, enum.Enum):
    """Custom field type enumeration"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    DROPDOWN = "dropdown"
    BOOLEAN = "boolean"


class AssetType(Base):
    """Asset type model for defining resource categories"""
    __tablename__ = "asset_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    custom_fields = relationship("CustomField", back_populates="asset_type", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="asset_type")

    __table_args__ = (
        Index("idx_asset_types_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<AssetType(id={self.id}, name={self.name})>"


class CustomField(Base):
    """Custom field model for dynamic asset type schema"""
    __tablename__ = "custom_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_type_id = Column(UUID(as_uuid=True), ForeignKey("asset_types.id"), nullable=False)
    name = Column(String(255), nullable=False)
    field_type = Column(String(50), nullable=False)  # text, number, date, dropdown, boolean
    is_required = Column(Boolean, nullable=False, default=False)
    options = Column(JSONB, nullable=True)  # JSON array for dropdown types
    validation_rules = Column(JSONB, nullable=True)  # JSON object with constraints
    display_order = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    asset_type = relationship("AssetType", back_populates="custom_fields")

    __table_args__ = (
        Index("idx_custom_fields_asset_type_id", "asset_type_id"),
        UniqueConstraint("asset_type_id", "name", name="uq_asset_type_field_name"),
    )

    def __repr__(self) -> str:
        return f"<CustomField(id={self.id}, name={self.name}, type={self.field_type})>"
