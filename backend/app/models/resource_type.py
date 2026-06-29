"""Resource type and field definition models"""
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class FieldType(str, enum.Enum):
    """Field data type enumeration"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    DROPDOWN = "dropdown"
    BOOLEAN = "boolean"
    DECIMAL = "decimal"
    EMAIL = "email"
    URL = "url"


class ResourceType(Base):
    """Resource type model representing workbook tabs"""
    __tablename__ = "resource_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    icon = Column(String(50), nullable=True)
    display_order = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    template_resource_types = relationship("TemplateResourceType", back_populates="resource_type")
    sheet_mappings = relationship("SheetMapping", back_populates="resource_type")
    resource_fields = relationship("ResourceField", back_populates="resource_type", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="resource_type")

    __table_args__ = (
        Index("idx_resource_types_display_order", "display_order"),
    )

    def __repr__(self) -> str:
        return f"<ResourceType(id={self.id}, name={self.name}, display_name={self.display_name})>"

    @property
    def active_fields(self):
        """Get active resource fields ordered by display_order"""
        return [field for field in sorted(self.resource_fields, key=lambda x: x.display_order) 
                if field.is_visible]


class ResourceField(Base):
    """Dynamic field definitions for resource types"""
    __tablename__ = "resource_fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_type_id = Column(UUID(as_uuid=True), ForeignKey("resource_types.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False)
    data_type = Column(String(50), nullable=False)
    unit = Column(String(20), nullable=True)
    is_required = Column(Boolean, nullable=False, default=False)
    is_unique = Column(Boolean, nullable=False, default=False)
    default_value = Column(Text, nullable=True)
    validation_regex = Column(Text, nullable=True)
    options = Column(JSONB, nullable=True)  # For dropdown options
    display_order = Column(Integer, nullable=False)
    is_visible = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    resource_type = relationship("ResourceType", back_populates="resource_fields")
    asset_field_values = relationship("AssetFieldValue", back_populates="resource_field", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_resource_fields_resource_type", "resource_type_id"),
        Index("idx_resource_fields_display_order", "resource_type_id", "display_order"),
        UniqueConstraint("resource_type_id", "field_name", name="uq_resource_type_field_name"),
        CheckConstraint("data_type IN ('text', 'number', 'date', 'dropdown', 'boolean', 'decimal', 'email', 'url')", 
                       name="ck_resource_fields_data_type"),
    )

    def __repr__(self) -> str:
        return f"<ResourceField(id={self.id}, name={self.field_name}, type={self.data_type})>"

    def validate_value(self, value):
        """Validate a value against this field's constraints"""
        if value is None:
            return not self.is_required, "Field is required" if self.is_required else None

        # Type-specific validation
        if self.data_type == FieldType.NUMBER:
            try:
                int(value)
                return True, None
            except ValueError:
                return False, "Must be a valid number"
        
        elif self.data_type == FieldType.DECIMAL:
            try:
                float(value)
                return True, None
            except ValueError:
                return False, "Must be a valid decimal number"
        
        elif self.data_type == FieldType.BOOLEAN:
            if isinstance(value, bool) or str(value).lower() in ('true', 'false', '1', '0'):
                return True, None
            return False, "Must be true or false"
        
        elif self.data_type == FieldType.EMAIL:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(email_pattern, str(value)):
                return True, None
            return False, "Must be a valid email address"
        
        elif self.data_type == FieldType.DROPDOWN:
            if self.options and isinstance(self.options, list):
                if value in self.options:
                    return True, None
                return False, f"Must be one of: {', '.join(self.options)}"
        
        # Custom regex validation
        if self.validation_regex:
            import re
            if not re.match(self.validation_regex, str(value)):
                return False, "Value does not match required format"

        return True, None