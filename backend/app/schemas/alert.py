"""Pydantic schemas for alert models"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class AlertCreateSchema(BaseModel):
    project_id: Optional[UUID] = None
    asset_id: Optional[UUID] = None
    alert_type: str
    severity: str
    title: str = Field(..., min_length=1, max_length=255)
    message: str
    due_date: Optional[date] = None


class AlertUpdateSchema(BaseModel):
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None


class AlertSchema(BaseModel):
    id: UUID
    project_id: Optional[UUID] = None
    asset_id: Optional[UUID] = None
    alert_type: str
    severity: str
    title: str
    message: str
    status: str
    due_date: Optional[date] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class AlertListSchema(BaseModel):
    id: UUID
    alert_type: str
    severity: str
    title: str
    status: str
    due_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True