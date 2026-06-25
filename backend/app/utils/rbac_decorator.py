"""Role-based access control decorator for FastAPI routes"""
from functools import wraps
from typing import List, Callable, Any
from fastapi import HTTPException, Depends, Request
import logging

from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


def require_role(*allowed_roles: str):
    """
    Decorator to enforce role-based access control on FastAPI routes.
    
    This decorator checks that the current_user's role is in the allowed_roles list.
    If not, it raises HTTPException with 403 Forbidden status.
    
    Works with FastAPI's Depends system by checking the current_user from dependencies.
    
    Args:
        *allowed_roles: One or more role names (Admin, Manager, Analyst, Viewer)
        
    Usage:
        @router.get("/admin-only")
        @require_role("Admin")
        async def admin_endpoint(current_user: User = Depends(get_current_user)):
            return {"message": "Admin access granted"}
            
        @router.post("/managers")
        @require_role("Admin", "Manager")
        async def manager_endpoint(current_user: User = Depends(get_current_user)):
            return {"message": "Manager or Admin access granted"}
    
    Returns:
        Decorated function that enforces role-based access
        
    Raises:
        HTTPException: 403 Forbidden if user role not in allowed_roles
        HTTPException: 401 Unauthorized if user is not authenticated
    """
    def decorator(func: Callable) -> Callable:
        """
        Actual decorator that wraps the endpoint function.
        
        Args:
            func: The endpoint function to wrap
            
        Returns:
            Wrapped function with role checking
        """
        @wraps(func)
        async def wrapper(*args: Any, current_user: User = None, **kwargs: Any) -> Any:
            # Verify user is authenticated
            if not current_user:
                logger.warning("Access attempt without authenticated user")
                raise HTTPException(
                    status_code=401,
                    detail="Not authenticated"
                )
            
            # Check if user's role is in allowed roles
            if current_user.role not in allowed_roles:
                logger.warning(
                    f"Access denied: User {current_user.id} with role {current_user.role} "
                    f"attempted access to endpoint requiring roles {allowed_roles}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
                )
            
            # Log successful access
            logger.debug(f"Role-based access granted to user {current_user.id} with role {current_user.role}")
            
            # Call the original function
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator


def check_role(*allowed_roles: str):
    """
    FastAPI Depends-compatible role checking function.
    
    Can be used with FastAPI's Depends to enforce roles on routes.
    
    Args:
        *allowed_roles: One or more role names
        
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user: User = Depends(get_current_user),
            _ = Depends(check_role("Admin"))
        ):
            return {"message": "Admin access granted"}
    
    Returns:
        A dependency function that checks roles
    """
    async def check(current_user: User = Depends(lambda: None)) -> None:
        if not current_user:
            logger.warning("Access attempt without authenticated user")
            raise HTTPException(
                status_code=401,
                detail="Not authenticated"
            )
        
        if current_user.role not in allowed_roles:
            logger.warning(
                f"Access denied: User {current_user.id} with role {current_user.role} "
                f"attempted access to endpoint requiring roles {allowed_roles}"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
    
    return check
