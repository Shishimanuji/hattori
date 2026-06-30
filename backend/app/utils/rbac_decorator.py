"""Role-based access control decorator for FastAPI routes"""
from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, Depends, status
import logging

from app.models.user import User

logger = logging.getLogger(__name__)


def require_role(*allowed_roles: str):
    """
    Decorator to enforce role-based access control on FastAPI routes.
    
    This decorator checks that the current_user's role is in the allowed_roles list.
    If not, it raises HTTPException with 403 Forbidden status.
    
    **IMPORTANT**: This decorator must be applied BEFORE route decorators like @router.get().
    The dependency system will inject the current_user, and this decorator will check their role.
    
    Args:
        *allowed_roles: One or more role names (Admin, Manager, Analyst, Viewer)
        
    Usage:
        @require_role("Admin")
        @router.get("/admin-only")
        async def admin_endpoint(current_user: User = Depends(get_current_user)):
            return {"message": "Admin access granted"}
            
        @require_role("Admin", "Manager")
        @router.post("/managers")
        async def manager_endpoint(current_user: User = Depends(get_current_user)):
            return {"message": "Manager or Admin access granted"}
    
    Returns:
        Decorated function that enforces role-based access
        
    Raises:
        HTTPException: 403 Forbidden if user role not in allowed_roles
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
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract current_user from kwargs (injected by FastAPI's dependency system)
            current_user = kwargs.get('current_user')
            
            # Verify user is authenticated
            if not current_user:
                logger.warning("Access attempt without authenticated user")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            # Get the user's role - handle both direct role attribute and role relationship
            user_role = None
            if hasattr(current_user, 'role'):
                if isinstance(current_user.role, str):
                    # Direct string role
                    user_role = current_user.role
                elif hasattr(current_user.role, 'role_name'):
                    # Role is an object with role_name attribute
                    user_role = current_user.role.role_name
            
            # Check if user's role is in allowed roles
            if user_role not in allowed_roles:
                logger.warning(
                    f"Access denied: User {current_user.id} with role {user_role} "
                    f"attempted access to endpoint requiring roles {allowed_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required role(s): {', '.join(allowed_roles)}"
                )
            
            # Log successful access
            logger.debug(f"Role-based access granted to user {current_user.id} with role {user_role}")
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def check_role(*allowed_roles: str):
    """
    FastAPI Depends-compatible role checking function.
    
    Can be used with FastAPI's Depends to enforce roles on routes.
    This is an alternative to the @require_role decorator.
    
    Args:
        *allowed_roles: One or more role names (Admin, Manager, Analyst, Viewer)
        
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user: User = Depends(get_current_user),
            _ = Depends(check_role("Admin"))
        ):
            return {"message": "Admin access granted"}
            
        @router.post("/managers")
        async def manager_endpoint(
            current_user: User = Depends(get_current_user),
            _ = Depends(check_role("Admin", "Manager"))
        ):
            return {"message": "Manager or Admin access granted"}
    
    Returns:
        A dependency function that checks roles
        
    Raises:
        HTTPException: 403 Forbidden if user role not in allowed_roles
    """
    async def role_checker(current_user: User = Depends(lambda: None)) -> None:
        """
        Check if the current user has one of the required roles.
        
        Args:
            current_user: The authenticated user (injected by FastAPI)
            
        Raises:
            HTTPException: 401 if not authenticated, 403 if insufficient permissions
        """
        if not current_user:
            logger.warning("Access attempt without authenticated user")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        # Get the user's role - handle both direct role attribute and role relationship
        user_role = None
        if hasattr(current_user, 'role'):
            if isinstance(current_user.role, str):
                # Direct string role
                user_role = current_user.role
            elif hasattr(current_user.role, 'role_name'):
                # Role is an object with role_name attribute
                user_role = current_user.role.role_name
        
        # Check if user's role is in allowed roles
        if user_role not in allowed_roles:
            logger.warning(
                f"Access denied: User {current_user.id} with role {user_role} "
                f"attempted access to endpoint requiring roles {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(allowed_roles)}"
            )
    
    return role_checker
