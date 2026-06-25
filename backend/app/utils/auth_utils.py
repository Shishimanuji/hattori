"""Authentication utilities and dependency injection"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.models.user import User
from app.schemas.current_user import CurrentUser
from app.utils.jwt_utils import verify_token

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer()


def get_token_from_header(authorization: str) -> str:
    """
    Extract Bearer token from Authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Token string
        
    Raises:
        HTTPException: If header is malformed or missing
    """
    if not authorization:
        logger.warning("Missing authorization header")
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )
    
    parts = authorization.split()
    
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(f"Invalid authorization format: {parts[0] if parts else 'none'}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Expected: Bearer <token>"
        )
    
    return parts[1]


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    Dependency function to get and validate current authenticated user.
    Extracts JWT token from Authorization header, validates it, and returns user.
    
    Args:
        request: FastAPI Request object
        db: Database session
        
    Returns:
        CurrentUser object with id, username, email, role, is_active, token_payload
        
    Raises:
        HTTPException: 401 for missing/invalid/expired tokens
    """
    # Get Authorization header
    auth_header = request.headers.get("authorization")
    
    if not auth_header:
        logger.warning("Request missing authorization header")
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )
    
    # Extract token from header
    try:
        token = get_token_from_header(auth_header)
    except HTTPException:
        raise
    
    # Verify token and extract payload
    try:
        payload = verify_token(token)
    except ValueError as e:
        logger.warning(f"Token validation failed: {str(e)}")
        error_detail = str(e)
        if "expired" in error_detail.lower():
            raise HTTPException(
                status_code=401,
                detail="Token expired"
            )
        elif "signature" in error_detail.lower():
            raise HTTPException(
                status_code=401,
                detail="Invalid token signature"
            )
        elif "malformed" in error_detail.lower():
            raise HTTPException(
                status_code=401,
                detail="Malformed token"
            )
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
    
    # Extract user_id from payload
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Token missing user ID (sub claim)")
        raise HTTPException(
            status_code=401,
            detail="Invalid token: missing user ID"
        )
    
    # Query database for fresh user data
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user_id}")
            raise HTTPException(
                status_code=401,
                detail="User account is inactive"
            )
        
        # Create CurrentUser object with fresh data
        current_user = CurrentUser(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            token_payload=payload
        )
        
        logger.debug(f"User authenticated: {user.username} (role: {user.role})")
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error verifying user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


async def get_current_user_async(
    request: Request,
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    Async version of get_current_user for async route handlers.
    
    Args:
        request: FastAPI Request object
        db: Database session
        
    Returns:
        CurrentUser object
        
    Raises:
        HTTPException: 401 for authentication errors
    """
    return get_current_user(request, db)


def require_role(*allowed_roles: str):
    """
    Dependency for route-level role-based access control.
    
    Usage:
        @app.get("/admin")
        async def admin_only(
            current_user: CurrentUser = Depends(get_current_user),
            _=Depends(require_role("Admin"))
        ):
            return {"message": "Admin only"}
    
    Args:
        allowed_roles: Tuple of allowed role strings
        
    Returns:
        Dependency function that checks user role
        
    Raises:
        HTTPException: 403 Forbidden if user role not in allowed_roles
    """
    async def check_role(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            logger.warning(
                f"User {current_user.username} with role {current_user.role} "
                f"attempted to access resource requiring: {allowed_roles}"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return check_role


def inject_user_into_state(current_user: CurrentUser) -> CurrentUser:
    """
    Helper function to inject user into request.state
    (typically used in middleware pattern)
    
    Args:
        current_user: CurrentUser object to inject
        
    Returns:
        Same CurrentUser object
    """
    return current_user
