"""Authentication middleware for verifying JWT tokens and session timeouts"""
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.orm import Session as DBSession
import logging

from app.utils.auth import AuthUtils
from app.services.session_service import SessionService, SessionNotFoundError, SessionExpiredError
from app.core.database import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass


async def get_current_user(
    request: Request,
    db: DBSession = Depends(get_db)
):
    """
    FastAPI dependency to get the current authenticated user.
    
    Validates JWT token and checks session timeouts:
    1. Extracts token from Authorization header
    2. Verifies JWT signature and expiration
    3. Retrieves session from database
    4. Validates session is not idle expired (30 min)
    5. Validates session is not absolutely expired (35 min)
    6. Updates last_activity to reset idle timer
    
    Raises:
        HTTPException 401: Token missing, invalid, or user not found
        HTTPException 401: Session expired (idle or absolute)
    """
    # Extract authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.warning("No authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from header
    token = AuthUtils.extract_token_from_header(auth_header)
    if not token:
        logger.warning("Invalid authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify JWT token
    payload = AuthUtils.verify_token(token)
    if not payload:
        logger.warning("Invalid JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user_id from token
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Token missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Hash the token for lookup
    token_hash = AuthUtils.hash_token(token)

    # Get session from database
    try:
        session = SessionService.get_session_by_user_and_token(
            db=db,
            user_id=user_id,
            token_hash=token_hash
        )
    except SessionNotFoundError:
        logger.warning(f"Session not found for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or has been invalidated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate session timeouts
    try:
        SessionService.validate_session_timeout(
            session=session,
            idle_timeout_minutes=settings.idle_timeout_minutes,
            absolute_timeout_minutes=settings.absolute_timeout_minutes
        )
    except SessionExpiredError as e:
        logger.info(f"Session {session.id} has expired: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reset idle timer to prevent timeout during active use
    SessionService.reset_idle_timer(session, db)

    # Attach user info to request state
    request.state.user_id = user_id
    request.state.session = session

    return {
        "user_id": user_id,
        "session_id": session.id
    }


def require_auth():
    """
    FastAPI dependency to require authentication on a route.
    
    Usage:
        @app.get("/protected")
        async def protected_route(current_user = Depends(require_auth())):
            ...
    """
    async def auth_dependency(
        request: Request,
        db: DBSession = Depends(get_db)
    ):
        return await get_current_user(request, db)
    
    return auth_dependency


def require_role(*allowed_roles):
    """
    FastAPI dependency to require specific roles for a route.
    
    Usage:
        @app.get("/admin")
        async def admin_route(current_user = Depends(require_role("Admin"))):
            ...
    
    Args:
        *allowed_roles: One or more role names
    """
    async def role_dependency(
        request: Request,
        db: DBSession = Depends(get_db)
    ):
        # First verify authentication
        user_info = await get_current_user(request, db)
        
        # Get user from database
        from app.models.user import User
        user = db.query(User).filter(User.id == user_info["user_id"]).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        # Check role
        if user.role not in allowed_roles:
            logger.warning(f"User {user.id} with role {user.role} attempted unauthorized access")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join(allowed_roles)}",
            )
        
        return {"user_id": user_info["user_id"], "user": user}
    
    return role_dependency
