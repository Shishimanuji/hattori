"""Pydantic schemas for template models"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ResourceTypeSchema(BaseModel):
    id: UUID
    name: str
    display_name: str
    icon: Optional[str] = None
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True


class TemplateResourceTypeSchema(BaseModel):
    id: UUID
    template_id: UUID
    resource_type_id: UUID
    display_order: int
    is_required: bool
    resource_type: Optional[ResourceTypeSchema] = None

    class Config:
        from_attributes = True


class SheetMappingSchema(BaseModel):
    id: UUID
    template_id: UUID
    sheet_name: str
    resource_type_id: UUID
    display_order: int
    is_summary_sheet: bool
    resource_type: Optional[ResourceTypeSchema] = None

    class Config:
        from_attributes = True


class TemplateCreateSchema(BaseModel):
    template_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    version: str = "1.0.0"
    client_type: str
    is_default: bool = False
    template_config: Dict[str, Any] = Field(default_factory=dict)


class TemplateUpdateSchema(BaseModel):
    template_name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    client_type: Optional[str] = None
    is_default: Optional[bool] = None
    template_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class TemplateSchema(BaseModel):
    id: UUID
    template_name: str
    description: Optional[str] = None
    version: str
    client_type: str
    is_default: bool
    is_active: bool
    template_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    template_resource_types: Optional[List[TemplateResourceTypeSchema]] = None
    sheet_mappings: Optional[List[SheetMappingSchema]] = None

    class Config:
        from_attributes = True