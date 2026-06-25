"""User management service"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from uuid import UUID
from typing import List, Optional, Dict, Any
import logging

from app.models.user import User, UserRole
from app.utils.auth import AuthUtils
from app.services.audit_service import log_audit
from app.models.audit_log import AuditOperation, AuditLogStatus

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    """Raised when a user is not found"""
    pass


class UserAlreadyExistsError(Exception):
    """Raised when trying to create a user that already exists"""
    pass


class CannotDeleteSelfError(Exception):
    """Raised when a user tries to delete themselves"""
    pass


class CannotRemoveOnlyAdminError(Exception):
    """Raised when trying to remove admin status from the only admin"""
    pass


class UserService:
    """Service for user management operations"""

    @staticmethod
    def get_users_paginated(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> tuple[List[User], int]:
        """
        Get paginated list of users with optional filtering.
        
        Args:
            db: Database session
            skip: Number of records to skip (offset)
            limit: Number of records to return (default 20, max 100)
            filters: Optional filter dictionary with keys: status, role
            
        Returns:
            Tuple of (users list, total count)
        """
        # Build base query
        query = db.query(User).filter(User.deleted_at.is_(None))
        
        # Apply filters
        if filters:
            if "status" in filters:
                is_active = filters["status"] == "active"
                query = query.filter(User.is_active == is_active)
            
            if "role" in filters:
                query = query.filter(User.role == filters["role"])
            
            if "search" in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        User.username.ilike(search_term),
                        User.email.ilike(search_term),
                    )
                )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
        logger.debug(f"Retrieved {len(users)} users (total: {total_count}) with skip={skip}, limit={limit}")
        return users, total_count

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> User:
        """
        Get a user by ID.
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            User object
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = db.query(User).filter(
            and_(User.id == user_id, User.deleted_at.is_(None))
        ).first()
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise UserNotFoundError(f"User {user_id} not found")
        
        return user

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            User object or None if not found
        """
        return db.query(User).filter(
            and_(User.username == username, User.deleted_at.is_(None))
        ).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            db: Database session
            email: Email address
            
        Returns:
            User object or None if not found
        """
        return db.query(User).filter(
            and_(User.email == email, User.deleted_at.is_(None))
        ).first()

    @staticmethod
    def create_user(
        db: Session,
        username: str,
        email: str,
        password: str,
        role: str = UserRole.VIEWER,
        created_by_user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
            role: User role (default: Viewer)
            created_by_user_id: Admin user creating this user
            ip_address: IP address for audit log
            user_agent: User agent for audit log
            
        Returns:
            Created User object
            
        Raises:
            UserAlreadyExistsError: If username or email already exists
        """
        # Check if username already exists
        if UserService.get_user_by_username(db, username):
            logger.warning(f"Username already exists: {username}")
            raise UserAlreadyExistsError(f"Username '{username}' already exists")
        
        # Check if email already exists
        if UserService.get_user_by_email(db, email):
            logger.warning(f"Email already exists: {email}")
            raise UserAlreadyExistsError(f"Email '{email}' already exists")
        
        # Hash password
        password_hash = AuthUtils.hash_password(password)
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True,
        )
        
        db.add(user)
        db.flush()  # Flush to get the ID before committing
        
        # Log the creation
        try:
            log_audit(
                db=db,
                user_id=created_by_user_id,
                entity_type="User",
                entity_id=user.id,
                operation=AuditOperation.CREATE,
                new_values={
                    "username": username,
                    "email": email,
                    "role": role,
                    "is_active": True,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as e:
            logger.error(f"Error logging user creation: {str(e)}")
            db.rollback()
            raise
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User created: {username} (ID: {user.id})")
        return user

    @staticmethod
    def update_user(
        db: Session,
        user_id: UUID,
        updates: Dict[str, Any],
        updated_by_user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """
        Update a user's information.
        
        Args:
            db: Database session
            user_id: User UUID to update
            updates: Dictionary of fields to update (email, role, status)
            updated_by_user_id: Admin user performing the update
            ip_address: IP address for audit log
            user_agent: User agent for audit log
            
        Returns:
            Updated User object
            
        Raises:
            UserNotFoundError: If user not found
            UserAlreadyExistsError: If email already exists
        """
        user = UserService.get_user_by_id(db, user_id)
        
        # Check for email uniqueness if email is being updated
        if "email" in updates and updates["email"] != user.email:
            if UserService.get_user_by_email(db, updates["email"]):
                logger.warning(f"Email already exists: {updates['email']}")
                raise UserAlreadyExistsError(f"Email '{updates['email']}' already exists")
        
        # Store old values for audit log
        old_values = {
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        }
        
        # Apply updates
        if "email" in updates:
            user.email = updates["email"]
        
        if "role" in updates:
            user.role = updates["role"]
        
        if "is_active" in updates:
            user.is_active = updates["is_active"]
        
        db.add(user)
        db.flush()
        
        # Log the update
        try:
            log_audit(
                db=db,
                user_id=updated_by_user_id,
                entity_type="User",
                entity_id=user.id,
                operation=AuditOperation.UPDATE,
                old_values=old_values,
                new_values={
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as e:
            logger.error(f"Error logging user update: {str(e)}")
            db.rollback()
            raise
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated: {user.username} (ID: {user.id})")
        return user

    @staticmethod
    def delete_user(
        db: Session,
        user_id: UUID,
        current_user_id: UUID,
        deleted_by_user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Soft delete a user (archive).
        
        Args:
            db: Database session
            user_id: User UUID to delete
            current_user_id: ID of user making the request (for validation)
            deleted_by_user_id: Admin user performing the deletion
            ip_address: IP address for audit log
            user_agent: User agent for audit log
            
        Raises:
            UserNotFoundError: If user not found
            CannotDeleteSelfError: If user tries to delete themselves
        """
        # Check if user exists
        user = UserService.get_user_by_id(db, user_id)
        
        # Prevent user from deleting themselves
        if user_id == current_user_id:
            logger.warning(f"User attempted to delete themselves: {user_id}")
            raise CannotDeleteSelfError("You cannot delete your own account")
        
        # Store old values for audit log
        old_values = {
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        }
        
        # Soft delete - set deleted_at timestamp
        from datetime import datetime
        user.deleted_at = datetime.utcnow()
        user.is_active = False
        
        db.add(user)
        db.flush()
        
        # Log the deletion
        try:
            log_audit(
                db=db,
                user_id=deleted_by_user_id,
                entity_type="User",
                entity_id=user.id,
                operation=AuditOperation.DELETE,
                old_values=old_values,
                new_values={
                    "deleted_at": user.deleted_at.isoformat(),
                    "is_active": False,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as e:
            logger.error(f"Error logging user deletion: {str(e)}")
            db.rollback()
            raise
        
        db.commit()
        logger.info(f"User deleted: {user.username} (ID: {user.id})")

    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets strength requirements
        """
        # Minimum 8 characters
        if len(password) < 8:
            return False
        
        return True
