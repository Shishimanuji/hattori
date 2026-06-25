"""Custom authentication and application exceptions"""
from fastapi import HTTPException
from typing import Any, Dict, Optional


class InvalidTokenException(HTTPException):
    """Raised when token is invalid or malformed"""
    def __init__(
        self,
        detail: str = "Invalid token",
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=401,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )


class TokenExpiredException(HTTPException):
    """Raised when token has expired"""
    def __init__(
        self,
        detail: str = "Token expired",
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=401,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )


class MissingTokenException(HTTPException):
    """Raised when authorization token is missing"""
    def __init__(
        self,
        detail: str = "Missing authorization header",
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=401,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )


class InsufficientPermissionsException(HTTPException):
    """Raised when user lacks required permissions"""
    def __init__(
        self,
        detail: str = "Insufficient permissions",
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=403,
            detail=detail,
            headers=headers
        )


class UserNotFoundException(HTTPException):
    """Raised when user is not found"""
    def __init__(
        self,
        detail: str = "User not found",
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=404,
            detail=detail,
            headers=headers
        )


class UserInactiveException(HTTPException):
    """Raised when user account is inactive"""
    def __init__(
        self,
        detail: str = "User account is inactive",
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=401,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )
