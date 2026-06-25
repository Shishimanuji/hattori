"""Project request/response schemas"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal


class ProjectBase(BaseModel):
    """Base project schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Project name (unique, 1-255 chars)")
    description: Optional[str] = Field(None, description="Project description")
    budget: Decimal = Field(..., decimal_places=2, description="Project budget (>= 0)")
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date: Optional[date] = Field(None, description="Project end date")

    @field_validator("budget")
    @classmethod
    def validate_budget(cls, v: Decimal) -> Decimal:
        """Validate budget is non-negative"""
        if v < 0:
            raise ValueError("Budget must be greater than or equal to 0")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: Optional[date], info) -> Optional[date]:
        """Validate end_date is >= start_date if both are set"""
        if v is not None and "start_date" in info.data:
            start_date = info.data.get("start_date")
            if start_date is not None and v < start_date:
                raise ValueError("End date must be greater than or equal to start date")
        return v


class ProjectCreate(ProjectBase):
    """Project creation schema"""
    status: Optional[str] = Field(default="Active", description="Project status (Active, Pending, Completed, On Hold)")


class ProjectUpdate(BaseModel):
    """Project update schema - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    status: Optional[str] = Field(None, description="Project status")
    budget: Optional[Decimal] = Field(None, decimal_places=2, description="Project budget")
    end_date: Optional[date] = Field(None, description="Project end date")

    @field_validator("budget")
    @classmethod
    def validate_budget(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate budget is non-negative"""
        if v is not None and v < 0:
            raise ValueError("Budget must be greater than or equal to 0")
        return v


class ProjectResponse(ProjectBase):
    """Project response schema with computed fields"""
    id: UUID
    status: str
    owner_id: UUID
    allocated_budget: Decimal = Field(..., description="Amount of budget allocated to resources")
    remaining_budget: Decimal = Field(..., description="Remaining budget (budget - allocated_budget)")
    utilization_percentage: float = Field(..., description="Budget utilization percentage (0-100)")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    """Detailed project response schema with resource summary"""
    resource_count: int = Field(default=0, description="Number of active resources in project")
    resources_by_type: dict = Field(default_factory=dict, description="Resource count grouped by asset type")


class ProjectListItem(BaseModel):
    """Project list item schema"""
    id: UUID
    name: str
    status: str
    budget: Decimal
    allocated_budget: Decimal
    remaining_budget: Decimal
    utilization_percentage: float
    resource_count: int = 0
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Paginated project list response schema"""
    items: List[ProjectListItem] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")
    page: int = Field(..., description="Current page number (0-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    has_more: bool = Field(..., description="Whether there are more pages")

    @classmethod
    def from_items(
        cls,
        items: List[ProjectListItem],
        total: int,
        page: int,
        page_size: int
    ) -> "ProjectListResponse":
        """Create response from items list"""
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page + 1) * page_size < total
        )
