"""Asset and related models for the new schema"""
from sqlalchemy import Column, String, Text, Numeric, Date, DateTime, Boolean, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
import uuid
import enum

from app.core.database import Base


class AssetStatus(str, enum.Enum):
    """Asset status enumeration"""
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DISPOSED = "Disposed"
    UNDER_REPAIR = "Under Repair"
    RESERVED = "Reserved"


class AuditStatus(str, enum.Enum):
    """Asset audit status enumeration"""
    PENDING = "Pending"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"
    NOT_REQUIRED = "Not Required"


class Asset(Base):
    """Unified asset model replacing the old resources table"""
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    resource_type_id = Column(UUID(as_uuid=True), ForeignKey("resource_types.id"), nullable=False)
    asset_code = Column(String(100), nullable=True)
    asset_name = Column(String(255), nullable=False)
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True)
    service_tag = Column(String(255), nullable=True)
    vendor = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    room_no = Column(String(50), nullable=True)
    custodian_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    purchase_date = Column(Date, nullable=True)
    installation_date = Column(Date, nullable=True)
    warranty_start = Column(Date, nullable=True)
    warranty_end = Column(Date, nullable=True)
    cost = Column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    status = Column(String(50), nullable=False, default=AssetStatus.ACTIVE)
    audit_status = Column(String(50), nullable=False, default=AuditStatus.PENDING)
    last_audit_date = Column(Date, nullable=True)
    remarks = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="assets")
    resource_type = relationship("ResourceType", back_populates="assets")
    custodian = relationship("User", foreign_keys=[custodian_id], back_populates="custodial_assets")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_assets")
    field_values = relationship("AssetFieldValue", back_populates="asset", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="asset")
    alerts = relationship("Alert", back_populates="asset")

    __table_args__ = (
        Index("idx_assets_project_id", "project_id"),
        Index("idx_assets_resource_type_id", "resource_type_id"),
        Index("idx_assets_asset_code", "asset_code"),
        Index("idx_assets_serial_number", "serial_number"),
        Index("idx_assets_status", "status"),
        Index("idx_assets_audit_status", "audit_status"),
        Index("idx_assets_custodian_id", "custodian_id"),
        Index("idx_assets_warranty_end", "warranty_end"),
        Index("idx_assets_created_by", "created_by"),
        CheckConstraint("status IN ('Active', 'Inactive', 'Disposed', 'Under Repair', 'Reserved')", 
                       name="ck_assets_status"),
        CheckConstraint("audit_status IN ('Pending', 'Completed', 'Overdue', 'Not Required')", 
                       name="ck_assets_audit_status"),
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, code={self.asset_code}, name={self.asset_name})>"

    @property
    def is_warranty_valid(self) -> bool:
        """Check if warranty is still valid"""
        if not self.warranty_end:
            return False
        return datetime.now().date() <= self.warranty_end

    @property
    def warranty_days_remaining(self) -> int:
        """Get days remaining on warranty"""
        if not self.warranty_end:
            return 0
        delta = self.warranty_end - datetime.now().date()
        return max(0, delta.days)

    @property
    def is_audit_due(self) -> bool:
        """Check if asset needs audit"""
        if self.audit_status == AuditStatus.NOT_REQUIRED:
            return False
        if self.audit_status == AuditStatus.OVERDUE:
            return True
        # Consider audit due if last audit was more than 365 days ago
        if self.last_audit_date:
            days_since_audit = (datetime.now().date() - self.last_audit_date).days
            return days_since_audit > 365
        return True  # No audit history means audit is due

    def get_field_value(self, field_name: str):
        """Get value for a specific dynamic field"""
        for field_value in self.field_values:
            if field_value.resource_field.field_name == field_name:
                return field_value.get_typed_value()
        return None

    def set_field_value(self, field_name: str, value, session):
        """Set value for a specific dynamic field"""
        from .resource_type import ResourceField
        
        # Find the field definition
        field_def = session.query(ResourceField).filter(
            ResourceField.resource_type_id == self.resource_type_id,
            ResourceField.field_name == field_name
        ).first()
        
        if not field_def:
            raise ValueError(f"Field '{field_name}' not found for resource type")
        
        # Validate the value
        is_valid, error_msg = field_def.validate_value(value)
        if not is_valid:
            raise ValueError(f"Invalid value for field '{field_name}': {error_msg}")
        
        # Find or create field value record
        field_value = None
        for fv in self.field_values:
            if fv.resource_field_id == field_def.id:
                field_value = fv
                break
        
        if not field_value:
            field_value = AssetFieldValue(
                asset_id=self.id,
                resource_field_id=field_def.id
            )
            self.field_values.append(field_value)
        
        field_value.set_typed_value(value, field_def.data_type)
        return field_value


class AssetFieldValue(Base):
    """EAV model for storing dynamic asset field values"""
    __tablename__ = "asset_field_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    resource_field_id = Column(UUID(as_uuid=True), ForeignKey("resource_fields.id"), nullable=False)
    text_value = Column(Text, nullable=True)
    number_value = Column(Numeric(15, 4), nullable=True)
    date_value = Column(Date, nullable=True)
    boolean_value = Column(Boolean, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    asset = relationship("Asset", back_populates="field_values")
    resource_field = relationship("ResourceField", back_populates="asset_field_values")

    __table_args__ = (
        Index("idx_asset_field_values_asset_id", "asset_id"),
        Index("idx_asset_field_values_field_id", "resource_field_id"),
    )

    def __repr__(self) -> str:
        return f"<AssetFieldValue(asset_id={self.asset_id}, field_id={self.resource_field_id})>"

    def get_typed_value(self):
        """Get the value in the correct type based on field definition"""
        if self.text_value is not None:
            return self.text_value
        elif self.number_value is not None:
            return self.number_value
        elif self.date_value is not None:
            return self.date_value
        elif self.boolean_value is not None:
            return self.boolean_value
        return None

    def set_typed_value(self, value, field_type: str):
        """Set the value in the appropriate column based on field type"""
        # Clear all values first
        self.text_value = None
        self.number_value = None
        self.date_value = None
        self.boolean_value = None
        
        if value is None:
            return
        
        from .resource_type import FieldType
        
        if field_type in [FieldType.TEXT, FieldType.DROPDOWN, FieldType.EMAIL, FieldType.URL]:
            self.text_value = str(value)
        elif field_type == FieldType.NUMBER:
            self.number_value = Decimal(str(value))
        elif field_type == FieldType.DECIMAL:
            self.number_value = Decimal(str(value))
        elif field_type == FieldType.DATE:
            if isinstance(value, str):
                from datetime import datetime
                self.date_value = datetime.strptime(value, "%Y-%m-%d").date()
            else:
                self.date_value = value
        elif field_type == FieldType.BOOLEAN:
            if isinstance(value, bool):
                self.boolean_value = value
            else:
                self.boolean_value = str(value).lower() in ('true', '1', 'yes', 'on')
        
        self.updated_at = datetime.utcnow()