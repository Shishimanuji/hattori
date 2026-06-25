"""
Unit and integration tests for Phase 6: User Management Backend

Tests for:
- Task 6.1: Create User API endpoints (GET, POST, PUT, DELETE /api/users)
- Task 6.2: Implement user role assignment and validation
- Task 6.3: Implement password reset functionality

Validates Requirements: 4.1, 4.2, 4.3, 4.6, 4.7, 12.1
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.session import Session as SessionModel
from app.services.user_service import (
    UserService, UserNotFoundError, UserAlreadyExistsError, CannotDeleteSelfError
)
from app.services.password_reset_service import PasswordResetService
from app.services.audit_service import log_audit
from app.models.audit_log import AuditOperation, AuditLogStatus
from app.utils.auth import AuthUtils


class TestTaskSix1UserAPI:
    """Tests for Task 6.1: Create User API endpoints"""
    
    def test_user_service_create_user_with_valid_data(self, db: Session):
        """
        Requirement 4.2: Create new user with role assignment
        """
        user = UserService.create_user(
            db=db,
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123",
            role=UserRole.MANAGER.value,
        )
        
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.role == UserRole.MANAGER.value
        assert user.is_active is True
        assert user.password_hash != "SecurePass123"  # Should be hashed
    
    def test_user_service_create_duplicate_username_fails(self, db: Session, test_user):
        """
        Requirement 4.6: Enforce unique usernames
        """
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            UserService.create_user(
                db=db,
                username=test_user.username,
                email="different@example.com",
                password="SecurePass123",
                role=UserRole.ANALYST.value,
            )
        assert "already exists" in str(exc_info.value)
    
    def test_user_service_create_duplicate_email_fails(self, db: Session, test_user):
        """
        Requirement 4.6: Enforce unique email addresses
        """
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            UserService.create_user(
                db=db,
                username="different_user",
                email=test_user.email,
                password="SecurePass123",
                role=UserRole.ANALYST.value,
            )
        assert "already exists" in str(exc_info.value)
    
    def test_user_service_list_paginated(self, db: Session, test_user):
        """
        Requirement 4.1: List all users with pagination
        """
        # Create a few more users
        for i in range(3):
            UserService.create_user(
                db=db,
                username=f"user_{i}",
                email=f"user_{i}@example.com",
                password="SecurePass123",
                role=UserRole.VIEWER.value,
            )
        
        users, total = UserService.get_users_paginated(
            db=db,
            skip=0,
            limit=2,
        )
        
        assert len(users) <= 2
        assert total >= 3  # At least the test user plus 3 we created
    
    def test_user_service_get_user_by_id(self, db: Session, test_user):
        """
        Requirement 4.1: Get user details by ID
        """
        user = UserService.get_user_by_id(db=db, user_id=test_user.id)
        assert user.id == test_user.id
        assert user.username == test_user.username
    
    def test_user_service_get_user_by_id_not_found(self, db: Session):
        """
        Requirement 4.1: Handle user not found gracefully
        """
        with pytest.raises(UserNotFoundError):
            UserService.get_user_by_id(db=db, user_id=uuid4())
    
    def test_user_service_update_user(self, db: Session, test_user):
        """
        Requirement 4.2: Update user information
        """
        updated_user = UserService.update_user(
            db=db,
            user_id=test_user.id,
            updates={"email": "newemail@example.com"},
        )
        
        assert updated_user.email == "newemail@example.com"
        assert updated_user.id == test_user.id
    
    def test_user_service_delete_user_soft_delete(self, db: Session):
        """
        Requirement 4.5: Archive user (soft delete) - mark deleted_at and set is_active=false
        """
        # Create admin and user to delete
        admin = UserService.create_user(
            db=db,
            username="admin",
            email="admin@example.com",
            password="SecurePass123",
            role=UserRole.ADMIN.value,
        )
        
        user_to_delete = UserService.create_user(
            db=db,
            username="todelete",
            email="todelete@example.com",
            password="SecurePass123",
            role=UserRole.ANALYST.value,
        )
        
        # Delete the user
        UserService.delete_user(
            db=db,
            user_id=user_to_delete.id,
            current_user_id=admin.id,
            deleted_by_user_id=admin.id,
        )
        
        # Verify soft delete: record still exists but marked as deleted
        deleted_user = db.query(User).filter(User.id == user_to_delete.id).first()
        assert deleted_user is not None
        assert deleted_user.deleted_at is not None
        assert deleted_user.is_active is False
    
    def test_user_service_cannot_delete_self(self, db: Session, test_user):
        """
        Requirement 4.5: Admin cannot delete their own account
        """
        with pytest.raises(CannotDeleteSelfError):
            UserService.delete_user(
                db=db,
                user_id=test_user.id,
                current_user_id=test_user.id,  # Same user
                deleted_by_user_id=test_user.id,
            )


class TestTaskSix2RoleAssignment:
    """Tests for Task 6.2: Implement user role assignment and validation"""
    
    def test_validate_role_valid_values(self):
        """
        Requirement 4.2: Validate role values (Admin, Manager, Analyst, Viewer)
        """
        from app.services.role_service import validate_role
        
        # All valid roles should pass
        assert validate_role("Admin") is True
        assert validate_role("Manager") is True
        assert validate_role("Analyst") is True
        assert validate_role("Viewer") is True
    
    def test_validate_role_invalid_values(self):
        """
        Requirement 4.2: Reject invalid role values
        """
        from app.services.role_service import validate_role
        
        # Invalid roles should fail
        assert validate_role("InvalidRole") is False
        assert validate_role("") is False
        assert validate_role("admin") is False  # Case sensitive
    
    def test_assign_role_updates_user_role(self, db: Session):
        """
        Requirement 4.2: Implement role update with audit logging
        """
        from app.services.role_service import assign_role
        
        # Create admin and user
        admin = UserService.create_user(
            db=db,
            username="admin",
            email="admin@example.com",
            password="SecurePass123",
            role=UserRole.ADMIN.value,
        )
        
        user = UserService.create_user(
            db=db,
            username="testuser",
            email="testuser@example.com",
            password="SecurePass123",
            role=UserRole.VIEWER.value,
        )
        
        # Assign new role
        updated_user = assign_role(
            user_id=user.id,
            new_role=UserRole.MANAGER.value,
            current_user_id=admin.id,
            db=db,
        )
        
        assert updated_user.role == UserRole.MANAGER.value
    
    def test_assign_role_creates_audit_log(self, db: Session):
        """
        Requirement 4.4: Role changes are audited
        """
        from app.services.role_service import assign_role
        from app.models.audit_log import AuditLog
        
        admin = UserService.create_user(
            db=db,
            username="admin",
            email="admin@example.com",
            password="SecurePass123",
            role=UserRole.ADMIN.value,
        )
        
        user = UserService.create_user(
            db=db,
            username="testuser",
            email="testuser@example.com",
            password="SecurePass123",
            role=UserRole.VIEWER.value,
        )
        
        # Assign role
        assign_role(
            user_id=user.id,
            new_role=UserRole.MANAGER.value,
            current_user_id=admin.id,
            db=db,
        )
        
        # Check audit log was created
        audit_log = db.query(AuditLog).filter(
            AuditLog.user_id == admin.id,
            AuditLog.entity_id == user.id,
            AuditLog.operation == AuditOperation.ROLE_CHANGE.value,
        ).first()
        
        assert audit_log is not None
        assert audit_log.old_values["role"] == UserRole.VIEWER.value
        assert audit_log.new_values["role"] == UserRole.MANAGER.value


class TestTaskSix3PasswordReset:
    """Tests for Task 6.3: Implement password reset functionality"""
    
    def test_generate_token(self):
        """
        Requirement 4.7: Generate one-time token
        """
        token = PasswordResetService.generate_token()
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.isalnum() or "_" in token  # Hex encoded
    
    def test_generate_temporary_password(self):
        """
        Requirement 4.7: Generate temporary password
        """
        temp_password = PasswordResetService.generate_temporary_password()
        
        assert isinstance(temp_password, str)
        assert len(temp_password) == PasswordResetService.TEMP_PASSWORD_LENGTH
        
        # Should have mixed character types
        has_upper = any(c.isupper() for c in temp_password)
        has_lower = any(c.islower() for c in temp_password)
        has_digit = any(c.isdigit() for c in temp_password)
        has_special = any(c in "!@#$%^&*" for c in temp_password)
        
        assert has_upper and has_lower and has_digit and has_special
    
    def test_request_password_reset(self, db: Session, test_user):
        """
        Requirement 4.7: Request password reset for a user
        """
        result = PasswordResetService.request_password_reset(
            db=db,
            username_or_email=test_user.username,
        )
        
        assert result["success"] is True
        assert "message" in result
        # In testing, token and temp password are returned
        if "token" in result:
            assert "temporary_password" in result
    
    def test_validate_reset_token_valid(self, db: Session, test_user):
        """
        Requirement 4.7: Validate reset token is valid
        """
        # Request reset
        result = PasswordResetService.request_password_reset(
            db=db,
            username_or_email=test_user.username,
        )
        
        if "token" in result:
            token = result["token"]
            
            # Validate token
            reset_token = PasswordResetService.validate_reset_token(db, token)
            
            assert reset_token is not None
            assert reset_token.user_id == test_user.id
            assert not reset_token.is_expired
            assert not reset_token.is_used
    
    def test_complete_password_reset(self, db: Session, test_user):
        """
        Requirement 4.7: Complete password reset with new password
        """
        # Request reset
        result = PasswordResetService.request_password_reset(
            db=db,
            username_or_email=test_user.username,
        )
        
        if "token" in result:
            token = result["token"]
            
            # Complete reset
            complete_result = PasswordResetService.complete_password_reset(
                db=db,
                token=token,
                new_password="NewPassword456!",
            )
            
            assert complete_result["success"] is True
            
            # Verify password was changed
            user_after = db.query(User).filter(User.id == test_user.id).first()
            
            # New password should be different from old
            assert user_after.password_hash != test_user.password_hash
            
            # New password should be verifiable
            assert AuthUtils.verify_password("NewPassword456!", user_after.password_hash)
    
    def test_reset_token_one_time_use(self, db: Session, test_user):
        """
        Requirement 4.7: Reset tokens can only be used once
        """
        # Request reset
        result = PasswordResetService.request_password_reset(
            db=db,
            username_or_email=test_user.username,
        )
        
        if "token" in result:
            token = result["token"]
            
            # Use token once
            PasswordResetService.complete_password_reset(
                db=db,
                token=token,
                new_password="NewPassword456!",
            )
            
            # Try to use the same token again - should fail
            with pytest.raises(ValueError) as exc_info:
                PasswordResetService.complete_password_reset(
                    db=db,
                    token=token,
                    new_password="AnotherPassword789!",
                )
            
            assert "already been used" in str(exc_info.value)


class TestAuditLogging:
    """Integration tests for audit logging of user operations"""
    
    def test_user_creation_audit_log(self, db: Session):
        """
        Requirement 4.4: User creation is audited
        """
        from app.models.audit_log import AuditLog
        
        admin = UserService.create_user(
            db=db,
            username="admin",
            email="admin@example.com",
            password="SecurePass123",
            role=UserRole.ADMIN.value,
            created_by_user_id=None,
        )
        
        user = UserService.create_user(
            db=db,
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123",
            role=UserRole.ANALYST.value,
            created_by_user_id=admin.id,
        )
        
        # Check audit log was created
        audit_log = db.query(AuditLog).filter(
            AuditLog.entity_id == user.id,
            AuditLog.operation == AuditOperation.CREATE.value,
        ).first()
        
        assert audit_log is not None
        assert audit_log.entity_type == "User"
        assert audit_log.new_values["username"] == "newuser"
    
    def test_user_update_audit_log(self, db: Session, test_user):
        """
        Requirement 4.4: User updates are audited
        """
        from app.models.audit_log import AuditLog
        
        admin = UserService.create_user(
            db=db,
            username="admin",
            email="admin@example.com",
            password="SecurePass123",
            role=UserRole.ADMIN.value,
        )
        
        # Update user
        UserService.update_user(
            db=db,
            user_id=test_user.id,
            updates={"email": "newemail@example.com"},
            updated_by_user_id=admin.id,
        )
        
        # Check audit log was created
        audit_log = db.query(AuditLog).filter(
            AuditLog.entity_id == test_user.id,
            AuditLog.operation == AuditOperation.UPDATE.value,
        ).first()
        
        assert audit_log is not None
        assert audit_log.entity_type == "User"
        assert audit_log.old_values["email"] == test_user.email
        assert audit_log.new_values["email"] == "newemail@example.com"
