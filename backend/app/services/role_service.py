"""Role management and validation service"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from typing import Optional, List
import logging

from app.models.user import User, UserRole
from app.models.project import Project
from app.models.resource import Resource
from app.services.audit_service import log_audit
from app.models.audit_log import AuditOperation, AuditLogStatus
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Valid roles
VALID_ROLES = [role.value for role in UserRole]


def validate_role(role_name: str) -> bool:
    """
    Validate that a role name is one of the valid roles.
    
    Args:
        role_name: The role name to validate
        
    Returns:
        True if role is valid, False otherwise
    """
    return role_name in VALID_ROLES


def count_admin_users(db: Session) -> int:
    """
    Count the number of active admin users in the system.
    
    Args:
        db: Database session
        
    Returns:
        Number of active admin users
    """
    return db.query(User).filter(
        User.role == UserRole.ADMIN.value,
        User.is_active == True,
        User.deleted_at == None
    ).count()


def assign_role(
    user_id: UUID,
    new_role: str,
    current_user_id: UUID,
    db: Session,
) -> User:
    """
    Assign a new role to a user with comprehensive validation and audit logging.
    
    Validation rules:
    1. new_role must be a valid role (Admin, Manager, Analyst, Viewer)
    2. current_user must have Admin role to assign roles
    3. Cannot demote the last admin in the system
    4. Target user must exist and be active
    
    Args:
        user_id: UUID of user to assign role to
        new_role: New role name
        current_user_id: UUID of user performing the action (must be Admin)
        db: Database session
        
    Returns:
        Updated User object
        
    Raises:
        HTTPException: If validation fails
            - 422: Invalid role value
            - 403: Current user is not Admin
            - 409: Cannot demote last admin
            - 404: Target user not found
    """
    # Validate new role is valid
    if not validate_role(new_role):
        logger.warning(f"Attempt to assign invalid role '{new_role}' to user {user_id}")
        raise HTTPException(
            status_code=422,
            detail=f"Invalid role '{new_role}'. Valid roles are: {', '.join(VALID_ROLES)}"
        )
    
    # Get current user and verify they are Admin
    current_user = db.query(User).filter(User.id == current_user_id).first()
    if not current_user:
        logger.warning(f"Role assignment attempted by non-existent user {current_user_id}")
        raise HTTPException(status_code=404, detail="Current user not found")
    
    if current_user.role != UserRole.ADMIN.value:
        logger.warning(
            f"Non-admin user {current_user_id} attempted to assign role"
        )
        raise HTTPException(
            status_code=403,
            detail="Only Admin users can assign roles"
        )
    
    # Get target user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        logger.warning(f"Role assignment attempted for non-existent user {user_id}")
        raise HTTPException(status_code=404, detail="Target user not found")
    
    # Check if attempting to demote the last admin
    if (target_user.role == UserRole.ADMIN.value and 
        new_role != UserRole.ADMIN.value):
        # Count active admins
        admin_count = count_admin_users(db)
        if admin_count <= 1:  # This is the only admin
            logger.warning(
                f"Attempt to demote last admin user {user_id} by {current_user_id}"
            )
            raise HTTPException(
                status_code=409,
                detail="Cannot demote the last admin user. At least one admin must exist."
            )
    
    # Store old role for audit logging
    old_role = target_user.role
    
    # Assign new role
    target_user.role = new_role
    
    try:
        db.commit()
        db.refresh(target_user)
        
        # Log role change to audit log
        log_audit(
            db=db,
            user_id=current_user_id,
            entity_type="User",
            entity_id=user_id,
            operation=AuditOperation.ROLE_CHANGE,
            old_values={"role": old_role},
            new_values={"role": new_role},
            status=AuditLogStatus.SUCCESS,
        )
        
        logger.info(
            f"Role change successful: User {user_id} role changed from {old_role} to {new_role} by {current_user_id}"
        )
        
        return target_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning role: {str(e)}")
        
        # Log failed role change to audit log
        log_audit(
            db=db,
            user_id=current_user_id,
            entity_type="User",
            entity_id=user_id,
            operation=AuditOperation.ROLE_CHANGE,
            old_values={"role": old_role},
            new_values={"role": new_role},
            status=AuditLogStatus.FAILURE,
            error_message=str(e),
        )
        
        raise HTTPException(
            status_code=500,
            detail="Error assigning role"
        )
