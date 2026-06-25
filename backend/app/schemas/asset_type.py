"""Asset Type and Custom Field request/response schemas"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import enum


class FieldType(str, enum.Enum):
    """Custom field type enumeration"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    DROPDOWN = "dropdown"
    BOOLEAN = "boolean"


class CustomFieldBase(BaseModel):
    """Base custom field schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Field name (unique per asset type, 1-255 chars)")
    field_type: FieldType = Field(..., description="Field type (text, number, date, dropdown, boolean)")
    is_required: bool = Field(default=False, description="Whether field is required")
    display_order: Optional[int] = Field(default=0, description="Display order in forms")
    options: Optional[List[str]] = Field(None, description="Options list for dropdown types")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules (min, max, regex, enum)")

    @field_validator("field_type", mode="before")
    @classmethod
    def validate_field_type(cls, v):
        """Validate field type is one of allowed values"""
        if isinstance(v, str):
            v = v.lower()
        return v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: Optional[List[str]], info) -> Optional[List[str]]:
        """Validate options are provided for dropdown types"""
        if info.data.get("field_type") == FieldType.DROPDOWN:
            if not v or len(v) == 0:
                raise ValueError("Options must be provided for dropdown field types")
        elif v is not None:
            raise ValueError("Options should only be provided for dropdown field types")
        return v

    @field_validator("validation_rules")
    @classmethod
    def validate_rules(cls, v: Optional[Dict[str, Any]], info) -> Optional[Dict[str, Any]]:
        """Validate validation rules structure"""
        if v is not None:
            allowed_keys = {"required", "min", "max", "regex", "enum"}
            for key in v.keys():
                if key not in allowed_keys:
                    raise ValueError(f"Invalid validation rule key: {key}. Allowed: {allowed_keys}")
        return v


class CustomFieldCreate(CustomFieldBase):
    """Custom field creation schema"""
    pass


class CustomFieldUpdate(BaseModel):
    """Custom field update schema - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Field name")
    field_type: Optional[FieldType] = Field(None, description="Field type")
    is_required: Optional[bool] = Field(None, description="Whether field is required")
    display_order: Optional[int] = Field(None, description="Display order")
    options: Optional[List[str]] = Field(None, description="Options for dropdown")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")


class CustomFieldResponse(CustomFieldBase):
    """Custom field response schema"""
    id: UUID
    asset_type_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetTypeBase(BaseModel):
    """Base asset type schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Asset type name (unique, 1-255 chars)")
    description: Optional[str] = Field(None, description="Asset type description")


class AssetTypeCreate(AssetTypeBase):
    """Asset type creation schema"""
    custom_fields: Optional[List[CustomFieldCreate]] = Field(default=[], description="Initial custom fields")


class AssetTypeUpdate(BaseModel):
    """Asset type update schema - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Asset type name")
    description: Optional[str] = Field(None, description="Asset type description")
    is_active: Optional[bool] = Field(None, description="Whether asset type is active")


class AssetTypeResponse(AssetTypeBase):
    """Asset type response schema with custom fields"""
    id: UUID
    is_active: bool
    custom_fields: List[CustomFieldResponse] = Field(default=[], description="List of custom fields")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetTypeDetailResponse(AssetTypeResponse):
    """Detailed asset type response with field count"""
    field_count: int = Field(default=0, description="Number of custom fields")


class AssetTypeListItem(BaseModel):
    """Asset type list item schema"""
    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    field_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetTypeListResponse(BaseModel):
    """Paginated asset type list response schema"""
    items: List[AssetTypeListItem] = Field(..., description="List of asset types")
    total: int = Field(..., description="Total number of asset types")
    page: int = Field(..., description="Current page number (0-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    has_more: bool = Field(..., description="Whether there are more pages")

    @classmethod
    def from_items(
        cls,
        items: List[AssetTypeListItem],
        total: int,
        page: int,
        page_size: int
    ) -> "AssetTypeListResponse":
        """Create response from items list"""
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page + 1) * page_size < total
        )
