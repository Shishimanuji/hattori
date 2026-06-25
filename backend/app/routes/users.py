"""User management routes"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate, UpdateUserRequest, UserResponse, PaginatedUserResponse,
    UserDetailResponse
)
from app.services.user_service import (
    UserService, UserNotFoundError, UserAlreadyExistsError, CannotDeleteSelfError
)
from app.services.role_service import assign_role, validate_role
from app.utils.dependencies import get_current_user
from app.utils.exceptions import InsufficientPermissionsException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["User Management"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure current user is Admin"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail="Only Admin users can perform this action"
        )
    return current_user


@router.get("", response_model=PaginatedUserResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str = Query(None, description="Filter by status: active or inactive"),
    role: str = Query(None, description="Filter by role"),
    search: str = Query(None, description="Search by username or email"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    List all users with pagination and filtering.
    
    **Requirements:**
    - Only Admin users can list all users (Requirement 4.1)
    - Support pagination with limit and offset
    - Support filtering by status, role, and search term
    
    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Number of records to return (default: 50, max: 100)
    - status: Filter by 'active' or 'inactive'
    - role: Filter by role (Admin, Manager, Analyst, Viewer)
    - search: Search by username or email
    
    **Returns:**
    - 200 OK: PaginatedUserResponse with user list
    - 403 Forbidden: If current user is not Admin
    
    **Example:**
    ```
    GET /api/users?skip=0&limit=20&status=active&role=Manager
    ```
    """
    filters = {}
    if status:
        filters["status"] = status
    if role:
        filters["role"] = role
    if search:
        filters["search"] = search
    
    users, total = UserService.get_users_paginated(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters if filters else None
    )
    
    page = skip // limit if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    
    return PaginatedUserResponse(
        items=[UserResponse.from_orm(u) for u in users],
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Create a new user.
    
    **Requirements:**
    - Only Admin users can create users (Requirement 4.1)
    - Username and email must be unique (Requirement 4.6)
    - All required fields must be provided (Requirement 4.2)
    - Role must be one of: Admin, Manager, Analyst, Viewer
    - User creation is audited (Requirement 4.4)
    
    **Request Body:**
    - username: Unique username (3-255 characters)
    - email: Unique email address
    - password: Password (minimum 8 characters)
    - role: User role (Admin, Manager, Analyst, or Viewer)
    
    **Returns:**
    - 201 Created: UserResponse with new user details
    - 400 Bad Request: If validation fails
    - 403 Forbidden: If current user is not Admin
    - 409 Conflict: If username or email already exists
    
    **Example:**
    ```
    POST /api/users
    Content-Type: application/json
    Authorization: Bearer <token>
    
    {
      "username": "john.doe",
      "email": "john@example.com",
      "password": "SecurePass123!",
      "role": "Manager"
    }
    ```
    """
    try:
        # Validate role
        if not validate_role(user_data.role.value):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid role: {user_data.role.value}"
            )
        
        # Get IP address and user agent for audit log
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        # Create user
        new_user = UserService.create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role.value,
            created_by_user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        logger.info(f"User created: {new_user.username} by {current_user.username}")
        return UserResponse.from_orm(new_user)
        
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=400, detail="Error creating user")


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get user details by ID.
    
    **Requirements:**
    - Only Admin users can view user details (Requirement 4.1)
    
    **Path Parameters:**
    - user_id: UUID of the user to retrieve
    
    **Returns:**
    - 200 OK: UserDetailResponse with user information
    - 403 Forbidden: If current user is not Admin
    - 404 Not Found: If user not found
    
    **Example:**
    ```
    GET /api/users/{user_id}
    ```
    """
    try:
        user = UserService.get_user_by_id(db=db, user_id=user_id)
        return UserDetailResponse.from_orm(user)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UpdateUserRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Update a user's information.
    
    **Requirements:**
    - Only Admin users can update users (Requirement 4.1)
    - Email must be unique (Requirement 4.6)
    - User updates are audited (Requirement 4.4)
    
    **Path Parameters:**
    - user_id: UUID of the user to update
    
    **Request Body (all optional):**
    - email: New email address (must be unique)
    - is_active: Whether user is active
    - role: New role (Admin, Manager, Analyst, or Viewer) - use role endpoint instead
    
    **Returns:**
    - 200 OK: UserResponse with updated user information
    - 403 Forbidden: If current user is not Admin
    - 404 Not Found: If user not found
    - 409 Conflict: If email already exists
    
    **Example:**
    ```
    PUT /api/users/{user_id}
    Content-Type: application/json
    Authorization: Bearer <token>
    
    {
      "email": "newemail@example.com",
      "is_active": true
    }
    ```
    """
    try:
        # Get IP address and user agent for audit log
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        # Prepare updates dictionary
        updates = {}
        if user_data.email:
            updates["email"] = user_data.email
        if user_data.is_active is not None:
            updates["is_active"] = user_data.is_active
        
        # Update user
        updated_user = UserService.update_user(
            db=db,
            user_id=user_id,
            updates=updates,
            updated_by_user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        logger.info(f"User updated: {updated_user.username} by {current_user.username}")
        return UserResponse.from_orm(updated_user)
        
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=400, detail="Error updating user")


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Archive (soft delete) a user.
    
    **Requirements:**
    - Only Admin users can delete users (Requirement 4.1, 4.5)
    - Performs soft delete - marks deleted_at and sets is_active=false (Requirement 4.5)
    - User deletion is audited (Requirement 4.4)
    - Admin users cannot delete themselves
    
    **Path Parameters:**
    - user_id: UUID of the user to delete
    
    **Returns:**
    - 204 No Content: User deleted successfully
    - 403 Forbidden: If current user is not Admin or trying to delete self
    - 404 Not Found: If user not found
    
    **Example:**
    ```
    DELETE /api/users/{user_id}
    ```
    """
    try:
        # Get IP address and user agent for audit log
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        # Delete user
        UserService.delete_user(
            db=db,
            user_id=user_id,
            current_user_id=current_user.id,
            deleted_by_user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        logger.info(f"User deleted: {user_id} by {current_user.username}")
        return None
        
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except CannotDeleteSelfError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=400, detail="Error deleting user")


@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    request_data: UpdateUserRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Update a user's role.
    
    **Requirements:**
    - Only Admin users can assign/change roles (Requirement 4.2)
    - Valid roles: Admin, Manager, Analyst, Viewer (Requirement 4.2)
    - Cannot demote the last admin in the system (Requirement 4.2)
    - All role changes are audited with ROLE_CHANGE operation (Requirement 4.4)
    
    **Path Parameters:**
    - user_id: UUID of the user whose role should be updated
    
    **Request Body:**
    - role: New role to assign (Admin, Manager, Analyst, or Viewer)
    
    **Returns:**
    - 200 OK: UserResponse with updated user info
    - 403 Forbidden: If current user is not Admin
    - 404 Not Found: If target user not found
    - 409 Conflict: If attempting to demote the last admin
    - 422 Unprocessable Entity: If role is invalid
    
    **Example:**
    ```
    PUT /api/users/{user_id}/role
    Content-Type: application/json
    Authorization: Bearer <token>
    
    {
      "role": "Manager"
    }
    ```
    """
    # Validate that role is provided
    if request_data.role is None:
        raise HTTPException(
            status_code=422,
            detail="Role must be provided"
        )
    
    # Use role_service to assign role (handles all validation and audit logging)
    updated_user = assign_role(
        user_id=user_id,
        new_role=request_data.role.value,
        current_user_id=current_user.id,
        db=db,
    )
    
    logger.info(
        f"Role updated for user {user_id} to {request_data.role.value} by {current_user.id}"
    )
    
    return UserResponse.from_orm(updated_user)
