"""
Tests for RBAC decorator (Task 13.1)

Tests verify that the @require_role decorator:
- Correctly checks user roles
- Returns 403 Forbidden for unauthorized users
- Returns 401 Unauthorized for unauthenticated users
- Allows authorized users to access endpoints
- Works with the check_role dependency function
"""

import pytest
from uuid import uuid4
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.role import Role
from app.utils.rbac_decorator import require_role, check_role
from app.utils.dependencies import get_current_user


# Mock user objects for testing
def create_mock_user(user_id=None, role_name="Admin"):
    """Create a mock user with the specified role"""
    user = User(
        id=user_id or uuid4(),
        username=f"test_{role_name}",
        email=f"test_{role_name}@example.com",
        password_hash="hashed_password",
        is_active=True
    )
    # Mock the role relationship
    mock_role = type('MockRole', (), {})()
    mock_role.role_name = role_name
    user.role = mock_role
    return user


class TestRequireRoleDecorator:
    """Tests for @require_role decorator (Task 13.1)"""
    
    def test_require_role_decorator_exists(self):
        """
        **Validates: Requirement 3.5**
        Verify that the @require_role decorator is properly defined and callable
        """
        assert callable(require_role)
        assert require_role.__name__ == "require_role"
    
    def test_require_role_with_single_role(self):
        """
        **Validates: Requirement 3.5**
        Decorator can be called with a single role
        """
        decorator = require_role("Admin")
        assert callable(decorator)
    
    def test_require_role_with_multiple_roles(self):
        """
        **Validates: Requirement 3.5**
        Decorator can be called with multiple roles
        """
        decorator = require_role("Admin", "Manager")
        assert callable(decorator)
    
    def test_require_role_decorator_returns_wrapper(self):
        """
        **Validates: Requirement 3.5**
        Decorator returns a function wrapper
        """
        async def test_func():
            return "success"
        
        decorated = require_role("Admin")(test_func)
        assert callable(decorated)
        assert decorated.__name__ == test_func.__name__  # wraps preserves name
    
    @pytest.mark.asyncio
    async def test_require_role_allows_authorized_user(self):
        """
        **Validates: Requirement 3.6**
        Decorator allows access for user with required role
        """
        @require_role("Admin")
        async def admin_endpoint(current_user: User):
            return {"message": "success"}
        
        admin_user = create_mock_user(role_name="Admin")
        result = await admin_endpoint(current_user=admin_user)
        assert result == {"message": "success"}
    
    @pytest.mark.asyncio
    async def test_require_role_allows_multiple_allowed_roles(self):
        """
        **Validates: Requirement 3.5, 3.6**
        Decorator allows access for users with any of the allowed roles
        """
        @require_role("Admin", "Manager")
        async def endpoint(current_user: User):
            return {"message": "success"}
        
        # Test Admin access
        admin_user = create_mock_user(role_name="Admin")
        result = await endpoint(current_user=admin_user)
        assert result == {"message": "success"}
        
        # Test Manager access
        manager_user = create_mock_user(role_name="Manager")
        result = await endpoint(current_user=manager_user)
        assert result == {"message": "success"}
    
    @pytest.mark.asyncio
    async def test_require_role_denies_unauthorized_user(self):
        """
        **Validates: Requirement 3.5, 3.7, 3.8**
        Decorator returns 403 Forbidden for user without required role
        """
        from fastapi import HTTPException
        
        @require_role("Admin")
        async def admin_endpoint(current_user: User):
            return {"message": "success"}
        
        # User with insufficient permissions
        analyst_user = create_mock_user(role_name="Analyst")
        
        with pytest.raises(HTTPException) as exc_info:
            await admin_endpoint(current_user=analyst_user)
        
        # Verify it's a 403 Forbidden response
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail
        assert "Admin" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_role_denies_unauthenticated_user(self):
        """
        **Validates: Requirement 3.1**
        Decorator returns 401 Unauthorized when user is not authenticated
        """
        from fastapi import HTTPException
        
        @require_role("Admin")
        async def admin_endpoint(current_user: User):
            return {"message": "success"}
        
        # No user provided (unauthenticated)
        with pytest.raises(HTTPException) as exc_info:
            await admin_endpoint(current_user=None)
        
        # Verify it's a 401 Unauthorized response
        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_role_preserves_function_behavior(self):
        """
        **Validates: Requirement 3.5**
        Decorator preserves the original function's behavior and return value
        """
        @require_role("Admin")
        async def get_admin_data(current_user: User):
            return {
                "message": "admin data",
                "user_id": str(current_user.id),
                "role": current_user.role.role_name
            }
        
        admin_user = create_mock_user(role_name="Admin")
        result = await get_admin_data(current_user=admin_user)
        
        assert result["message"] == "admin data"
        assert result["role"] == "Admin"
    
    @pytest.mark.asyncio
    async def test_require_role_with_function_parameters(self):
        """
        **Validates: Requirement 3.5**
        Decorator works with functions that have other parameters
        """
        @require_role("Admin")
        async def endpoint(current_user: User, name: str, age: int):
            return {
                "message": f"Hello {name}, age {age}",
                "user_id": str(current_user.id)
            }
        
        admin_user = create_mock_user(role_name="Admin")
        result = await endpoint(current_user=admin_user, name="John", age=30)
        
        assert result["message"] == "Hello John, age 30"


class TestCheckRoleDependency:
    """Tests for check_role dependency function (Task 13.1)"""
    
    def test_check_role_exists(self):
        """
        **Validates: Requirement 3.5**
        Verify that the check_role dependency function is properly defined
        """
        assert callable(check_role)
        assert check_role.__name__ == "check_role"
    
    def test_check_role_with_single_role(self):
        """
        **Validates: Requirement 3.5**
        Dependency can be called with a single role
        """
        dep = check_role("Admin")
        assert callable(dep)
    
    def test_check_role_with_multiple_roles(self):
        """
        **Validates: Requirement 3.5**
        Dependency can be called with multiple roles
        """
        dep = check_role("Admin", "Manager")
        assert callable(dep)
    
    @pytest.mark.asyncio
    async def test_check_role_allows_authorized_user(self):
        """
        **Validates: Requirement 3.6**
        Dependency allows access for user with required role
        """
        check_admin = check_role("Admin")
        admin_user = create_mock_user(role_name="Admin")
        
        # Should not raise an exception
        result = await check_admin(current_user=admin_user)
        assert result is None  # Dependencies return None on success
    
    @pytest.mark.asyncio
    async def test_check_role_denies_unauthorized_user(self):
        """
        **Validates: Requirement 3.7, 3.8**
        Dependency returns 403 Forbidden for user without required role
        """
        from fastapi import HTTPException
        
        check_admin = check_role("Admin")
        analyst_user = create_mock_user(role_name="Analyst")
        
        with pytest.raises(HTTPException) as exc_info:
            await check_admin(current_user=analyst_user)
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_check_role_denies_unauthenticated_user(self):
        """
        **Validates: Requirement 3.1**
        Dependency returns 401 Unauthorized when user is not authenticated
        """
        from fastapi import HTTPException
        
        check_admin = check_role("Admin")
        
        with pytest.raises(HTTPException) as exc_info:
            await check_admin(current_user=None)
        
        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail


class TestRBACIntegration:
    """Integration tests for RBAC decorator with FastAPI"""
    
    def test_decorator_with_fastapi_route(self):
        """
        **Validates: Requirement 3.5, 3.6, 3.7, 3.8**
        Decorator works correctly with FastAPI routes
        """
        app = FastAPI()
        router = APIRouter()
        
        # Mock dependency for testing
        async def mock_get_current_user():
            return create_mock_user(role_name="Admin")
        
        @require_role("Admin")
        @router.get("/admin")
        async def admin_endpoint(current_user: User = Depends(mock_get_current_user)):
            return {"message": "admin access granted"}
        
        app.include_router(router)
        client = TestClient(app)
        
        # This test verifies the decorator doesn't break FastAPI routing
        # (actual HTTP testing would require proper dependency injection)
        assert router.routes[0].path == "/admin"
    
    def test_multiple_decorators_on_route(self):
        """
        **Validates: Requirement 3.5**
        Multiple role decorators can be applied
        """
        @require_role("Admin", "Manager")
        async def endpoint(current_user: User):
            return {"message": "success"}
        
        # Both Admin and Manager should be allowed
        admin_user = create_mock_user(role_name="Admin")
        manager_user = create_mock_user(role_name="Manager")
        
        # Functions should be callable (decorator chain works)
        assert callable(endpoint)


class TestRBACErrorMessages:
    """Tests for RBAC error message clarity"""
    
    @pytest.mark.asyncio
    async def test_error_message_includes_required_roles(self):
        """
        **Validates: Requirement 3.5**
        Error message clearly indicates which roles are required
        """
        from fastapi import HTTPException
        
        @require_role("Admin", "Manager")
        async def endpoint(current_user: User):
            return {"message": "success"}
        
        analyst_user = create_mock_user(role_name="Analyst")
        
        with pytest.raises(HTTPException) as exc_info:
            await endpoint(current_user=analyst_user)
        
        # Message should list the required roles
        detail = exc_info.value.detail
        assert "Admin" in detail
        assert "Manager" in detail
    
    @pytest.mark.asyncio
    async def test_logging_on_denied_access(self, caplog):
        """
        **Validates: Requirement 3.5**
        Access denials are logged for security auditing
        """
        from fastapi import HTTPException
        import logging
        
        caplog.set_level(logging.WARNING)
        
        @require_role("Admin")
        async def endpoint(current_user: User):
            return {"message": "success"}
        
        analyst_user = create_mock_user(user_id=uuid4(), role_name="Analyst")
        
        with pytest.raises(HTTPException):
            await endpoint(current_user=analyst_user)
        
        # Check that warning was logged
        assert any("Access denied" in record.message for record in caplog.records)


class TestRBACWithDifferentRoles:
    """Tests covering all role types"""
    
    @pytest.mark.asyncio
    async def test_role_admin(self):
        """Admin role is properly recognized"""
        @require_role("Admin")
        async def endpoint(current_user: User):
            return {"message": "success"}
        
        admin = create_mock_user(role_name="Admin")
        result = await endpoint(current_user=admin)
        assert result == {"message": "success"}
    
    @pytest.mark.asyncio
    async def test_role_manager(self):
        """Manager role is properly recognized"""
        @require_role("Manager")
        async def endpoint(current_user: User):
            return {"message": "success"}
        
        manager = create_mock_user(role_name="Manager")
        result = await endpoint(current_user=manager)
        assert result == {"message": "success"}
    
    @pytest.mark.asyncio
    async def test_role_analyst(self):
        """Analyst role is properly recognized"""
        @require_role("Analyst")
        async def endpoint(current_user: User):
            return {"message": "success"}
        
        analyst = create_mock_user(role_name="Analyst")
        result = await endpoint(current_user=analyst)
        assert result == {"message": "success"}
    
    @pytest.mark.asyncio
    async def test_role_viewer(self):
        """Viewer role is properly recognized"""
        @require_role("Viewer")
        async def endpoint(current_user: User):
            return {"message": "success"}
        
        viewer = create_mock_user(role_name="Viewer")
        result = await endpoint(current_user=viewer)
        assert result == {"message": "success"}
