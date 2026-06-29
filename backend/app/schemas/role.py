"""Pydantic schemas for role models"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RoleSchema(BaseModel):
    id: int
    role_name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RoleCreateSchema(BaseModel):
    role_name: str
    description: Optional[str] = None


class RoleUpdateSchema(BaseModel):
    role_name: Optional[str] = None
    description: Optional[str] = None