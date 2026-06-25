"""Dependency functions for FastAPI routes"""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.session import Session as SessionModel
from app.utils.auth import AuthUtils
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user from the request.
    Validates Bearer token and ensures user is active.
    
    Args:
        request: FastAPI Request object
        db: Database session
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: 401 if no token, invalid token, or user not active
    """
    # Extract authorization header
    auth_header = request.headers.get("authorization")
    
    if not auth_header:
        logger.warning("Request received without authorization header")
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    # Extract token from header
    token = AuthUtils.extract_token_from_header(auth_header)
    
    if not token:
        logger.warning("Invalid authorization header format")
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    # Verify token
    token_data = AuthUtils.verify_token(token)
    
    if not token_data:
        logger.warning("Token verification failed - invalid or expired")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Extract user_id from token
    user_id = token_data.get("sub")
    
    if not user_id:
        logger.warning("Token missing user ID claim")
        raise HTTPException(status_code=401, detail="Invalid token claims")
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        logger.warning(f"User not found for token user_id: {user_id}")
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user_id}")
        raise HTTPException(status_code=401, detail="User account is inactive")
    
    # Check if session is valid
    token_hash = AuthUtils.hash_token(token)
    session_record = db.query(SessionModel).filter(
        SessionModel.token_hash == token_hash,
        SessionModel.user_id == user.id
    ).first()
    
    if not session_record:
        logger.warning(f"No session found for user {user_id}. Token hash: {token_hash[:16]}...")
        raise HTTPException(status_code=401, detail="Session not found. Please login again.")
    
    # Check if session is valid (not expired)
    try:
        # Log session details for debugging
        logger.debug(f"Session check for user {user_id}: is_active={session_record.is_active}, " 
                    f"created_at={session_record.created_at}, last_activity={session_record.last_activity}, "
                    f"invalidated_at={session_record.invalidated_at}")
        
        if not session_record.is_valid():
            # Provide more specific error details
            if not session_record.is_active:
                logger.warning(f"Session inactive for user {user_id}")
                raise HTTPException(status_code=401, detail="Session has been invalidated. Please login again.")
            elif session_record.invalidated_at is not None:
                logger.warning(f"Session invalidated at {session_record.invalidated_at} for user {user_id}")
                raise HTTPException(status_code=401, detail="Session has been invalidated. Please login again.")
            elif session_record.is_idle_expired():
                logger.warning(f"Session idle timeout for user {user_id}")
                raise HTTPException(status_code=401, detail="Session expired due to inactivity. Please login again.")
            elif session_record.is_absolute_expired():
                logger.warning(f"Session absolute timeout for user {user_id}")
                raise HTTPException(status_code=401, detail="Session expired. Please login again.")
            else:
                logger.warning(f"Session invalid for unknown reason for user {user_id}")
                raise HTTPException(status_code=401, detail="Session invalid. Please login again.")
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error validating session for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Session validation error. Please login again.")
    
    # Update last activity to reset idle timer
    try:
        session_record.reset_idle_timer()
        db.commit()
    except Exception as e:
        logger.error(f"Error updating session idle timer for user {user_id}: {str(e)}")
        # Don't fail the request, just log the error
        db.rollback()
    
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to ensure current user is an Admin.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User if admin, raises HTTPException otherwise
        
    Raises:
        HTTPException: 403 if user is not admin
    """
    from app.models.user import UserRole
    
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user attempted to access admin endpoint: {current_user.id}")
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    return current_user


async def get_current_manager_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to ensure current user is a Manager or Admin.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User if manager or admin, raises HTTPException otherwise
        
    Raises:
        HTTPException: 403 if user is not manager or admin
    """
    from app.models.user import UserRole
    
    if current_user.role not in (UserRole.MANAGER, UserRole.ADMIN):
        logger.warning(f"Non-manager user attempted to access manager endpoint: {current_user.id}")
        raise HTTPException(status_code=403, detail="Manager privileges required")
    
    return current_user
