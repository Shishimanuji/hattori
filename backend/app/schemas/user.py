"""User request/response schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class RoleEnum(str, Enum):
    """Valid user roles"""
    ADMIN = "Admin"
    MANAGER = "Manager"
    ANALYST = "Analyst"
    VIEWER = "Viewer"


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    role: RoleEnum = Field(default=RoleEnum.VIEWER, description="User role: Admin, Manager, Analyst, or Viewer")


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8, max_length=255)


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UpdateUserRequest(BaseModel):
    """User update request schema - used for partial updates"""
    email: Optional[EmailStr] = None
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema"""
    id: UUID
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Detailed user response schema"""
    pass


class PaginatedUserResponse(BaseModel):
    """Paginated user response schema"""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        from_attributes = True

