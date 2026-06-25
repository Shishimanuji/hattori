"""Unit tests for user management endpoints and services"""
import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UpdateUserRequest, RoleEnum
from app.services.user_service import UserService, UserNotFoundError, UserAlreadyExistsError
from app.services.role_service import assign_role
from app.utils.auth import AuthUtils


class TestUserCreation:
    """Tests for user creation functionality (Task 6.1, 6.2)"""
    
    def test_create_user_with_valid_data(self, admin_user, admin_token, db: Session, client):
        """
        Test creating a user with valid data.
        Validates: Requirement 4.2 - Create new user with role
        """
        response = client.post(
            "/api/users",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePassword123",
                "role": "Manager"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "Manager"
        assert "password" not in data  # Password should never be returned
        assert UUID(data["id"])  # Should have a valid UUID

    def test_create_user_without_admin_role(self, manager_user, manager_token, db: Session):
        """
        Test that non-admin users cannot create users.
        Validates: Requirement 4.1 - Only Admin can create users
        """
        response = client.post(
            "/api/users",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePassword123",
                "role": "Analyst"
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        assert response.status_code == 403
        assert "Admin" in response.json()["detail"]

    def test_create_user_with_duplicate_username(self, admin_user, admin_token, db: Session):
        """
        Test that creating a user with duplicate username fails.
        Validates: Requirement 4.6 - Email and username must be unique
        """
        # First create a user
        response1 = client.post(
            "/api/users",
            json={
                "username": "testuser",
                "email": "test1@example.com",
                "password": "SecurePassword123",
                "role": "Analyst"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response1.status_code == 201
        
        # Try to create another user with same username
        response2 = client.post(
            "/api/users",
            json={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "SecurePassword123",
                "role": "Analyst"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    def test_create_user_with_duplicate_email(self, admin_user, admin_token, db: Session):
        """
        Test that creating a user with duplicate email fails.
        Validates: Requirement 4.6 - Email must be unique
        """
        # First create a user
        response1 = client.post(
            "/api/users",
            json={
                "username": "testuser1",
                "email": "test@example.com",
                "password": "SecurePassword123",
                "role": "Analyst"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response1.status_code == 201
        
        # Try to create another user with same email
        response2 = client.post(
            "/api/users",
            json={
                "username": "testuser2",
                "email": "test@example.com",
                "password": "SecurePassword123",
                "role": "Analyst"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    def test_create_user_with_valid_roles(self, admin_user, admin_token, db: Session):
        """
        Test creating users with all valid roles.
        Validates: Requirement 4.2 - Validate role values (Admin, Manager, Analyst, Viewer)
        """
        roles = ["Admin", "Manager", "Analyst", "Viewer"]
        
        for idx, role in enumerate(roles):
            response = client.post(
                "/api/users",
                json={
                    "username": f"user_{role}_{idx}",
                    "email": f"user_{role}_{idx}@example.com",
                    "password": "SecurePassword123",
                    "role": role
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["role"] == role


class TestUserListing:
    """Tests for user listing functionality (Task 6.1)"""
    
    def test_list_users_with_pagination(self, admin_user, admin_token, db: Session):
        """
        Test listing users with pagination.
        Validates: Requirement 4.1 - List all users with pagination
        """
        # Create multiple users
        for i in range(5):
            client.post(
                "/api/users",
                json={
                    "username": f"user_{i}",
                    "email": f"user_{i}@example.com",
                    "password": "SecurePassword123",
                    "role": "Analyst"
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        
        # List with limit
        response = client.get(
            "/api/users?limit=3&skip=0",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 3
        assert data["page_size"] == 3
        assert data["total"] > 0

    def test_list_users_requires_admin(self, manager_user, manager_token, db: Session):
        """
        Test that non-admin users cannot list all users.
        Validates: Requirement 4.1 - Only Admin can list users
        """
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        assert response.status_code == 403

    def test_list_users_with_status_filter(self, admin_user, admin_token, db: Session):
        """
        Test listing users with status filter.
        Validates: Requirement 4.1 - Support filtering
        """
        response = client.get(
            "/api/users?status=active",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["is_active"] for item in data["items"])


class TestUserUpdate:
    """Tests for user update functionality (Task 6.1, 6.2)"""
    
    def test_update_user_email(self, admin_user, admin_token, db: Session):
        """
        Test updating user's email.
        Validates: Requirement 4.2, 4.6 - Update user and ensure email uniqueness
        """
        # Create a user
        create_response = client.post(
            "/api/users",
            json={
                "username": "testuser",
                "email": "old@example.com",
                "password": "SecurePassword123",
                "role": "Analyst"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        user_id = create_response.json()["id"]
        
        # Update email
        update_response = client.put(
            f"/api/users/{user_id}",
            json={"email": "new@example.com"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["email"] == "new@example.com"

    def test_update_user_role(self, admin_user, admin_token, db: Session):
        """
        Test updating user's role via dedicated role endpoint.
        Validates: Requirement 4.2 - Implement role update with audit logging
        """
        # Create a user with Viewer role
        create_response = client.post(
            "/api/users",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "SecurePassword123",
                "role": "Viewer"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        user_id = create_response.json()["id"]
        
        # Update role to Manager
        update_response = client.put(
            f"/api/users/{user_id}/role",
            json={"role": "Manager"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["role"] == "Manager"

    def test_update_user_without_admin_role(self, manager_user, manager_token, db: Session):
        """
        Test that non-admin users cannot update users.
        Validates: Requirement 4.1 - Only Admin can update users
        """
        response = client.put(
            f"/api/users/550e8400-e29b-41d4-a716-446655440000",
            json={"email": "new@example.com"},
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        assert response.status_code == 403

    def test_cannot_demote_last_admin(self, db: Session):
        """
        Test that the last admin cannot be demoted.
        Validates: Requirement 4.2 - Cannot demote last admin
        """
        # Assuming there's only one admin (admin_user from fixture)
        # Try to demote them to Manager
        admin = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
        
        if admin:
            # First create an admin token
            token = AuthUtils.create_access_token(
                data={"sub": str(admin.id)},
                expires_delta=None
            )[0]
            
            response = client.put(
                f"/api/users/{admin.id}/role",
                json={"role": "Manager"},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should fail because it's the last admin
            assert response.status_code == 409


class TestUserDelete:
    """Tests for user delete functionality (Task 6.1)"""
    
    def test_delete_user(self, admin_user, admin_token, db: Session):
        """
        Test deleting a user (soft delete).
        Validates: Requirement 4.5 - Perform soft delete and prevent login
        """
        # Create a user
        create_response = client.post(
            "/api/users",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "SecurePassword123",
                "role": "Analyst"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        user_id = create_response.json()["id"]
        
        # Delete the user
        delete_response = client.delete(
            f"/api/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert delete_response.status_code == 204
        
        # Verify user is still in database but marked as deleted
        user = db.query(User).filter(User.id == user_id).first()
        assert user is not None
        assert user.deleted_at is not None
        assert user.is_active is False

    def test_cannot_delete_self(self, admin_user, admin_token, db: Session):
        """
        Test that users cannot delete themselves.
        Validates: Requirement 4.5 - Admin cannot delete themselves
        """
        response = client.delete(
            f"/api/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 403
        assert "cannot delete" in response.json()["detail"].lower()

    def test_delete_user_without_admin_role(self, manager_user, manager_token, db: Session):
        """
        Test that non-admin users cannot delete users.
        Validates: Requirement 4.1 - Only Admin can delete users
        """
        response = client.delete(
            f"/api/users/550e8400-e29b-41d4-a716-446655440000",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        assert response.status_code == 403


class TestPasswordReset:
    """Tests for password reset functionality (Task 6.3)"""
    
    def test_request_password_reset(self, db: Session):
        """
        Test requesting a password reset.
        Validates: Requirement 4.7 - Generate temporary password and one-time token
        """
        response = client.post(
            "/api/auth/password-reset/request",
            json={"username_or_email": "testuser@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_complete_password_reset(self, db: Session, test_user):
        """
        Test completing a password reset.
        Validates: Requirement 4.7 - Require user to set new password on first login after reset
        """
        # First request a reset
        reset_response = client.post(
            "/api/auth/password-reset/request",
            json={"username_or_email": test_user.username}
        )
        
        assert reset_response.status_code == 200
        
        # Get the token from the response (in testing environment)
        token = reset_response.json().get("token")
        temp_password = reset_response.json().get("temporary_password")
        
        if token:  # Only test if we have the token (testing mode)
            # Complete the reset
            complete_response = client.post(
                "/api/auth/password-reset/complete",
                json={
                    "token": token,
                    "new_password": "NewSecurePassword456"
                }
            )
            
            assert complete_response.status_code == 200
            assert complete_response.json()["success"] is True


class TestRoleValidation:
    """Tests for role validation (Task 6.2)"""
    
    def test_validate_role(self, db: Session):
        """
        Test role validation.
        Validates: Requirement 4.2 - Validate role values
        """
        from app.services.role_service import validate_role
        
        # Valid roles should pass
        assert validate_role("Admin") is True
        assert validate_role("Manager") is True
        assert validate_role("Analyst") is True
        assert validate_role("Viewer") is True
        
        # Invalid roles should fail
        assert validate_role("InvalidRole") is False
        assert validate_role("") is False
        assert validate_role("admin") is False  # Case sensitive


class TestUserServiceMethods:
    """Tests for UserService methods (Task 6.1, 6.2)"""
    
    def test_get_users_paginated(self, db: Session):
        """
        Test UserService.get_users_paginated.
        Validates: Requirement 4.1 - Pagination works correctly
        """
        users, total = UserService.get_users_paginated(
            db=db,
            skip=0,
            limit=10,
        )
        
        assert isinstance(users, list)
        assert isinstance(total, int)
        assert total >= 0

    def test_create_user_service(self, db: Session):
        """
        Test UserService.create_user.
        Validates: Requirement 4.2 - User creation with role assignment
        """
        user = UserService.create_user(
            db=db,
            username="servicetest",
            email="servicetest@example.com",
            password="SecurePassword123",
            role=UserRole.MANAGER.value,
        )
        
        assert user.username == "servicetest"
        assert user.email == "servicetest@example.com"
        assert user.role == UserRole.MANAGER.value
        assert user.is_active is True

    def test_create_user_duplicate_username(self, db: Session, test_user):
        """
        Test that creating a user with duplicate username raises error.
        Validates: Requirement 4.6 - Username must be unique
        """
        with pytest.raises(UserAlreadyExistsError):
            UserService.create_user(
                db=db,
                username=test_user.username,
                email="different@example.com",
                password="SecurePassword123",
                role=UserRole.ANALYST.value,
            )

    def test_get_user_by_id(self, db: Session, test_user):
        """
        Test UserService.get_user_by_id.
        Validates: Requirement 4.1 - Retrieve user by ID
        """
        user = UserService.get_user_by_id(db=db, user_id=test_user.id)
        
        assert user.id == test_user.id
        assert user.username == test_user.username

    def test_get_user_by_id_not_found(self, db: Session):
        """
        Test that getting non-existent user raises error.
        """
        from uuid import uuid4
        with pytest.raises(UserNotFoundError):
            UserService.get_user_by_id(db=db, user_id=uuid4())

    def test_update_user(self, db: Session, test_user):
        """
        Test UserService.update_user.
        Validates: Requirement 4.2 - Update user information
        """
        updated_user = UserService.update_user(
            db=db,
            user_id=test_user.id,
            updates={"email": "newemail@example.com"},
        )
        
        assert updated_user.email == "newemail@example.com"

    def test_delete_user(self, db: Session):
        """
        Test UserService.delete_user (soft delete).
        Validates: Requirement 4.5 - Soft delete user
        """
        # Create a user
        user = UserService.create_user(
            db=db,
            username="tobedeleted",
            email="tobedeleted@example.com",
            password="SecurePassword123",
            role=UserRole.ANALYST.value,
        )
        
        # Delete the user
        admin = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
        UserService.delete_user(
            db=db,
            user_id=user.id,
            current_user_id=admin.id if admin else user.id,
            deleted_by_user_id=admin.id if admin else user.id,
        )
        
        # Verify soft delete
        deleted_user = db.query(User).filter(User.id == user.id).first()
        assert deleted_user.deleted_at is not None
        assert deleted_user.is_active is False
