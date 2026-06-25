"""Current user schema with authentication context"""
from pydantic import BaseModel
from uuid import UUID
from typing import Dict, Any


class CurrentUser(BaseModel):
    """Schema for current authenticated user injected into request context"""
    id: UUID
    username: str
    email: str
    role: str
    is_active: bool
    token_payload: Dict[str, Any]

    class Config:
        from_attributes = True
