"""Pydantic schemas for asset models"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal


class ResourceFieldSchema(BaseModel):
    id: UUID
    resource_type_id: UUID
    field_name: str
    display_name: str
    data_type: str
    unit: Optional[str] = None
    is_required: bool
    is_unique: bool
    default_value: Optional[str] = None
    validation_regex: Optional[str] = None
    options: Optional[List[str]] = None
    display_order: int
    is_visible: bool

    class Config:
        from_attributes = True


class AssetFieldValueSchema(BaseModel):
    id: UUID
    asset_id: UUID
    resource_field_id: UUID
    text_value: Optional[str] = None
    number_value: Optional[Decimal] = None
    date_value: Optional[date] = None
    boolean_value: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetCreateSchema(BaseModel):
    project_id: UUID
    resource_type_id: UUID
    asset_code: Optional[str] = None
    asset_name: str = Field(..., min_length=1, max_length=255)
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    service_tag: Optional[str] = None
    vendor: Optional[str] = None
    location: Optional[str] = None
    room_no: Optional[str] = None
    custodian_id: Optional[UUID] = None
    purchase_date: Optional[date] = None
    installation_date: Optional[date] = None
    warranty_start: Optional[date] = None
    warranty_end: Optional[date] = None
    cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: str = "Active"
    audit_status: str = "Pending"
    remarks: Optional[str] = None
    field_values: Optional[Dict[str, Any]] = None


class AssetUpdateSchema(BaseModel):
    asset_name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    service_tag: Optional[str] = None
    vendor: Optional[str] = None
    location: Optional[str] = None
    room_no: Optional[str] = None
    custodian_id: Optional[UUID] = None
    purchase_date: Optional[date] = None
    installation_date: Optional[date] = None
    warranty_start: Optional[date] = None
    warranty_end: Optional[date] = None
    cost: Optional[Decimal] = None
    status: Optional[str] = None
    audit_status: Optional[str] = None
    remarks: Optional[str] = None
    field_values: Optional[Dict[str, Any]] = None


class AssetSchema(BaseModel):
    id: UUID
    project_id: UUID
    resource_type_id: UUID
    asset_code: Optional[str] = None
    asset_name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    service_tag: Optional[str] = None
    vendor: Optional[str] = None
    location: Optional[str] = None
    room_no: Optional[str] = None
    custodian_id: Optional[UUID] = None
    purchase_date: Optional[date] = None
    installation_date: Optional[date] = None
    warranty_start: Optional[date] = None
    warranty_end: Optional[date] = None
    cost: Decimal
    status: str
    audit_status: str
    last_audit_date: Optional[date] = None
    remarks: Optional[str] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    field_values: Optional[List[AssetFieldValueSchema]] = None

    class Config:
        from_attributes = True


class AssetListSchema(BaseModel):
    id: UUID
    asset_code: Optional[str] = None
    asset_name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    status: str
    warranty_end: Optional[date] = None
    cost: Decimal

    class Config:
        from_attributes = True