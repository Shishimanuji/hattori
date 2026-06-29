"""Template database models for workbook format definitions"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Template(Base):
    """Template model for workbook format definitions"""
    __tablename__ = "templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), nullable=False, default="1.0.0")
    client_type = Column(String(100), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    template_config = Column(JSONB, nullable=False, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = relationship("Project", back_populates="template")
    template_resource_types = relationship("TemplateResourceType", back_populates="template", cascade="all, delete-orphan")
    sheet_mappings = relationship("SheetMapping", back_populates="template", cascade="all, delete-orphan")
    import_history = relationship("ImportHistory", back_populates="template")

    __table_args__ = (
        Index("idx_templates_client_type", "client_type"),
        Index("idx_templates_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Template(id={self.id}, name={self.template_name}, version={self.version})>"

    @property
    def resource_types(self):
        """Get associated resource types ordered by display_order"""
        return [trt.resource_type for trt in 
                sorted(self.template_resource_types, key=lambda x: x.display_order)]


class TemplateResourceType(Base):
    """Junction table linking templates to resource types"""
    __tablename__ = "template_resource_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=False)
    resource_type_id = Column(UUID(as_uuid=True), ForeignKey("resource_types.id"), nullable=False)
    display_order = Column(Integer, nullable=False)
    is_required = Column(Boolean, nullable=False, default=False)

    # Relationships
    template = relationship("Template", back_populates="template_resource_types")
    resource_type = relationship("ResourceType", back_populates="template_resource_types")

    __table_args__ = (
        Index("idx_template_resource_types_template", "template_id"),
        UniqueConstraint("template_id", "resource_type_id", name="uq_template_resource_type"),
    )

    def __repr__(self) -> str:
        return f"<TemplateResourceType(template_id={self.template_id}, resource_type_id={self.resource_type_id})>"


class SheetMapping(Base):
    """Maps Excel sheet names to resource types for template flexibility"""
    __tablename__ = "sheet_mapping"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=False)
    sheet_name = Column(String(255), nullable=False)
    resource_type_id = Column(UUID(as_uuid=True), ForeignKey("resource_types.id"), nullable=False)
    display_order = Column(Integer, nullable=False)
    is_summary_sheet = Column(Boolean, nullable=False, default=False)

    # Relationships
    template = relationship("Template", back_populates="sheet_mappings")
    resource_type = relationship("ResourceType", back_populates="sheet_mappings")

    __table_args__ = (
        Index("idx_sheet_mapping_template", "template_id"),
        UniqueConstraint("template_id", "sheet_name", name="uq_template_sheet_name"),
    )

    def __repr__(self) -> str:
        return f"<SheetMapping(sheet_name={self.sheet_name}, resource_type={self.resource_type_id})>"