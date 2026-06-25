"""Audit logging service"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, Dict, Any
import logging

from app.models.audit_log import AuditLog, AuditOperation, AuditLogStatus

logger = logging.getLogger(__name__)


def log_audit(
    db: Session,
    user_id: Optional[UUID],
    entity_type: str,
    entity_id: UUID,
    operation: AuditOperation,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: AuditLogStatus = AuditLogStatus.SUCCESS,
    error_message: Optional[str] = None,
    execution_time_ms: Optional[int] = None,
) -> AuditLog:
    """
    Create an audit log entry.
    
    Args:
        db: Database session
        user_id: User performing the action
        entity_type: Type of entity affected (e.g., 'User', 'Session', 'Project')
        entity_id: ID of the entity affected
        operation: Type of operation (CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.)
        old_values: Previous values (for UPDATE operations)
        new_values: New values (for CREATE/UPDATE operations)
        ip_address: IP address of the request
        user_agent: User agent string
        status: Success or failure status
        error_message: Error message if operation failed
        execution_time_ms: Time taken to execute the operation
        
    Returns:
        The created AuditLog record
    """
    try:
        audit_log = AuditLog(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation.value,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status.value,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        logger.info(
            f"Audit log created: {operation.value} on {entity_type} {entity_id} by user {user_id}"
        )
        return audit_log
    except Exception as e:
        logger.error(f"Error creating audit log: {str(e)}")
        db.rollback()
        raise


def log_logout(
    db: Session,
    user_id: UUID,
    session_id: UUID,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """
    Log a logout operation.
    
    Args:
        db: Database session
        user_id: User logging out
        session_id: Session being invalidated
        ip_address: IP address of the request
        user_agent: User agent string
        
    Returns:
        The created AuditLog record
    """
    return log_audit(
        db=db,
        user_id=user_id,
        entity_type="Session",
        entity_id=session_id,
        operation=AuditOperation.LOGOUT,
        new_values={"is_active": False, "invalidated_at": "now()"},
        ip_address=ip_address,
        user_agent=user_agent,
        status=AuditLogStatus.SUCCESS,
    )


def log_login(
    db: Session,
    user_id: UUID,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """
    Log a login operation.
    
    Args:
        db: Database session
        user_id: User logging in
        ip_address: IP address of the request
        user_agent: User agent string
        
    Returns:
        The created AuditLog record
    """
    return log_audit(
        db=db,
        user_id=user_id,
        entity_type="User",
        entity_id=user_id,
        operation=AuditOperation.LOGIN,
        new_values={"login_at": "now()"},
        ip_address=ip_address,
        user_agent=user_agent,
        status=AuditLogStatus.SUCCESS,
    )
