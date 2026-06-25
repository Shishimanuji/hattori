"""Authentication request/response schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiration in seconds")
    user: 'CurrentUserResponse' = Field(description="Authenticated user information")


class LogoutResponse(BaseModel):
    """Logout response schema"""
    message: str = "Successfully logged out"


class TokenData(BaseModel):
    """Token data schema"""
    user_id: UUID
    username: str
    role: str
    exp: datetime


class CurrentUserResponse(BaseModel):
    """Current user response schema"""
    id: UUID
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordResetRequestRequest(BaseModel):
    """Password reset request schema"""
    username_or_email: str = Field(..., min_length=3, max_length=255)


class PasswordResetRequestResponse(BaseModel):
    """Password reset request response schema"""
    success: bool
    message: str
    token: Optional[str] = Field(None, description="Token for testing (remove in production)")
    temporary_password: Optional[str] = Field(None, description="Temporary password for testing (remove in production)")


class PasswordResetVerifyRequest(BaseModel):
    """Password reset verification request schema"""
    token: str = Field(..., min_length=32, max_length=255)
    new_password: str = Field(..., min_length=8, max_length=255)


class PasswordResetVerifyResponse(BaseModel):
    """Password reset verification response schema"""
    success: bool
    message: str


class PasswordResetWithTempRequest(BaseModel):
    """Password reset with temporary password request schema"""
    token: str = Field(..., min_length=32, max_length=255)
    temporary_password: str = Field(..., min_length=8, max_length=255)
    new_password: str = Field(..., min_length=8, max_length=255)


class PasswordResetWithTempResponse(BaseModel):
    """Password reset with temporary password response schema"""
    success: bool
    message: str
    must_change_password: bool = False


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    old_password: str = Field(..., min_length=8, max_length=255)
    new_password: str = Field(..., min_length=8, max_length=255)


class ChangePasswordResponse(BaseModel):
    """Change password response schema"""
    success: bool
    message: str
