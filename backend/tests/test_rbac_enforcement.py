"""
Tests for RBAC (Role-Based Access Control) Enforcement - Phase 13

Tests verify that:
1. Role-based access control decorator works correctly (13.1)
2. RBAC service layer enforces permissions properly (13.2)
3. Viewer/Analyst project scope limiting works (13.3)
4. Resource-level authorization checks are enforced (13.4)
"""

import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.project import Project
from app.models.resource import Resource
from app.models.asset_type import AssetType
from app.services.authorization_service import AuthorizationService
from app.services.project_service import get_projects_paginated
from app.services.resource_service import get_resources_paginated


class TestRBACDecorator:
    """Tests for @require_role decorator (Task 13.1)"""
    
    def test_require_role_decorator_exists(self):
        """
        **Validates: Requirement 3.5**
        Verify that the @require_role decorator is properly defined
        """
        from app.utils.rbac_decorator import require_role
        assert callable(require_role)
    
    def test_check_role_dependency_exists(self):
        """
        Verify that check_role dependency function exists for FastAPI
        """
        from app.utils.rbac_decorator import check_role
        assert callable(check_role)


class TestProjectAuthorization:
    """Tests for project-level RBAC (Task 13.2, 13.3)"""
    
    def test_admin_can_create_project(self):
        """
        **Validates: Requirement 3.5, 3.6**
        Admin role can create projects
        """
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        assert AuthorizationService.can_create_project(admin)
    
    def test_manager_can_create_project(self):
        """
        **Validates: Requirement 3.5, 3.6**
        Manager role can create projects
        """
        manager = User(id=uuid4(), role=UserRole.MANAGER)
        assert AuthorizationService.can_create_project(manager)
    
    def test_analyst_cannot_create_project(self):
        """
        **Validates: Requirement 3.7**
        Analyst role cannot create projects
        """
        analyst = User(id=uuid4(), role=UserRole.ANALYST)
        assert not AuthorizationService.can_create_project(analyst)
    
    def test_viewer_cannot_create_project(self):
        """
        **Validates: Requirement 3.8**
        Viewer role cannot create projects
        """
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        assert not AuthorizationService.can_create_project(viewer)
    
    def test_admin_can_edit_any_project(self):
        """
        **Validates: Requirement 3.6**
        Admin can edit any project
        """
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        project = Project(id=uuid4(), owner_id=uuid4())  # Not owned by admin
        assert AuthorizationService.can_edit_project(admin, project)
    
    def test_manager_can_edit_own_project(self):
        """
        **Validates: Requirement 3.6**
        Manager can edit project they own
        """
        manager_id = uuid4()
        manager = User(id=manager_id, role=UserRole.MANAGER)
        project = Project(id=uuid4(), owner_id=manager_id)
        assert AuthorizationService.can_edit_project(manager, project)
    
    def test_manager_cannot_edit_others_project(self):
        """
        **Validates: Requirement 3.6**
        Manager cannot edit project owned by someone else
        """
        manager = User(id=uuid4(), role=UserRole.MANAGER)
        project = Project(id=uuid4(), owner_id=uuid4())  # Owned by someone else
        assert not AuthorizationService.can_edit_project(manager, project)
    
    def test_analyst_cannot_edit_project(self):
        """
        **Validates: Requirement 3.7**
        Analyst cannot edit any project
        """
        analyst = User(id=uuid4(), role=UserRole.ANALYST)
        project = Project(id=uuid4(), owner_id=uuid4())
        assert not AuthorizationService.can_edit_project(analyst, project)
    
    def test_viewer_cannot_edit_project(self):
        """
        **Validates: Requirement 3.8**
        Viewer cannot edit any project
        """
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        project = Project(id=uuid4(), owner_id=uuid4())
        assert not AuthorizationService.can_edit_project(viewer, project)
    
    def test_admin_can_view_all_projects(self):
        """
        **Validates: Requirement 3.5**
        Admin can view all projects
        """
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        project = Project(id=uuid4(), owner_id=uuid4())
        assert AuthorizationService.can_view_project(admin, project)
    
    def test_manager_can_view_all_projects(self):
        """
        **Validates: Requirement 3.6**
        Manager can view all projects
        """
        manager = User(id=uuid4(), role=UserRole.MANAGER)
        project = Project(id=uuid4(), owner_id=uuid4())  # Not their project
        assert AuthorizationService.can_view_project(manager, project)
    
    def test_analyst_can_view_all_projects(self):
        """
        **Validates: Requirement 3.7**
        Analyst can view all projects (read-only)
        """
        analyst = User(id=uuid4(), role=UserRole.ANALYST)
        project = Project(id=uuid4(), owner_id=uuid4())
        assert AuthorizationService.can_view_project(analyst, project)
    
    def test_viewer_cannot_view_unassigned_project(self):
        """
        **Validates: Requirement 3.8, 1.5**
        Viewer cannot view projects not assigned to them
        """
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        viewer.assigned_projects = []  # Set as attribute, not in constructor
        project = Project(id=uuid4(), owner_id=uuid4())
        assert not AuthorizationService.can_view_project(viewer, project)
    
    def test_viewer_can_view_assigned_project(self):
        """
        **Validates: Requirement 1.5**
        Viewer can view projects assigned to them
        """
        project_id = uuid4()
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        viewer.assigned_projects = [project_id]  # Set as attribute, not in constructor
        project = Project(id=project_id, owner_id=uuid4())
        assert AuthorizationService.can_view_project(viewer, project)


class TestResourceAuthorization:
    """Tests for resource-level RBAC (Task 13.4)"""
    
    def test_admin_can_create_resource(self):
        """
        **Validates: Requirement 3.5**
        Admin can create resources
        """
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        assert AuthorizationService.can_create_resource(admin)
    
    def test_manager_can_create_resource(self):
        """
        **Validates: Requirement 3.5**
        Manager can create resources
        """
        manager = User(id=uuid4(), role=UserRole.MANAGER)
        assert AuthorizationService.can_create_resource(manager)
    
    def test_analyst_cannot_create_resource(self):
        """
        **Validates: Requirement 3.5**
        Analyst cannot create resources (read-only)
        """
        analyst = User(id=uuid4(), role=UserRole.ANALYST)
        assert not AuthorizationService.can_create_resource(analyst)
    
    def test_viewer_cannot_create_resource(self):
        """
        **Validates: Requirement 3.5**
        Viewer cannot create resources
        """
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        assert not AuthorizationService.can_create_resource(viewer)
    
    def test_admin_can_edit_any_resource(self):
        """
        **Validates: Requirement 3.6**
        Admin can edit any resource
        """
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        resource = Resource(id=uuid4(), project_id=uuid4())
        project = Project(id=resource.project_id, owner_id=uuid4())
        assert AuthorizationService.can_edit_resource(admin, resource, project)
    
    def test_manager_can_edit_resource_in_own_project(self):
        """
        **Validates: Requirement 3.6**
        Manager can edit resources in their own projects
        """
        manager_id = uuid4()
        manager = User(id=manager_id, role=UserRole.MANAGER)
        project_id = uuid4()
        resource = Resource(id=uuid4(), project_id=project_id)
        project = Project(id=project_id, owner_id=manager_id)
        assert AuthorizationService.can_edit_resource(manager, resource, project)
    
    def test_manager_cannot_edit_resource_in_others_project(self):
        """
        **Validates: Requirement 3.6**
        Manager cannot edit resources in projects they don't own
        """
        manager = User(id=uuid4(), role=UserRole.MANAGER)
        project_id = uuid4()
        resource = Resource(id=uuid4(), project_id=project_id)
        project = Project(id=project_id, owner_id=uuid4())  # Not owned by manager
        assert not AuthorizationService.can_edit_resource(manager, resource, project)
    
    def test_analyst_cannot_edit_resource(self):
        """
        **Validates: Requirement 3.5**
        Analyst cannot edit resources (read-only)
        """
        analyst = User(id=uuid4(), role=UserRole.ANALYST)
        resource = Resource(id=uuid4(), project_id=uuid4())
        project = Project(id=resource.project_id, owner_id=uuid4())
        assert not AuthorizationService.can_edit_resource(analyst, resource, project)
    
    def test_viewer_cannot_edit_resource(self):
        """
        **Validates: Requirement 3.8**
        Viewer cannot edit resources
        """
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        resource = Resource(id=uuid4(), project_id=uuid4())
        project = Project(id=resource.project_id, owner_id=uuid4())
        assert not AuthorizationService.can_edit_resource(viewer, resource, project)
    
    def test_admin_can_view_all_resources(self):
        """
        **Validates: Requirement 3.5**
        Admin can view all resources
        """
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        resource = Resource(id=uuid4(), project_id=uuid4())
        project = Project(id=resource.project_id, owner_id=uuid4())
        assert AuthorizationService.can_view_resource(admin, resource, project)
    
    def test_manager_can_view_resource_in_own_project(self):
        """
        **Validates: Requirement 3.6**
        Manager can view resources in their own projects
        """
        manager_id = uuid4()
        manager = User(id=manager_id, role=UserRole.MANAGER)
        project_id = uuid4()
        resource = Resource(id=uuid4(), project_id=project_id)
        project = Project(id=project_id, owner_id=manager_id)
        assert AuthorizationService.can_view_resource(manager, resource, project)
    
    def test_manager_cannot_view_resource_in_others_project(self):
        """
        **Validates: Requirement 3.6**
        Manager cannot view resources in projects they don't own
        """
        manager = User(id=uuid4(), role=UserRole.MANAGER)
        project_id = uuid4()
        resource = Resource(id=uuid4(), project_id=project_id)
        project = Project(id=project_id, owner_id=uuid4())
        assert not AuthorizationService.can_view_resource(manager, resource, project)
    
    def test_analyst_can_view_all_resources(self):
        """
        **Validates: Requirement 3.7**
        Analyst can view all resources (read-only)
        """
        analyst = User(id=uuid4(), role=UserRole.ANALYST)
        resource = Resource(id=uuid4(), project_id=uuid4())
        project = Project(id=resource.project_id, owner_id=uuid4())
        assert AuthorizationService.can_view_resource(analyst, resource, project)
    
    def test_viewer_cannot_view_resource_in_unassigned_project(self):
        """
        **Validates: Requirement 3.8**
        Viewer cannot view resources in projects not assigned to them
        """
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        viewer.assigned_projects = []  # Set as attribute, not in constructor
        resource = Resource(id=uuid4(), project_id=uuid4())
        project = Project(id=resource.project_id, owner_id=uuid4())
        assert not AuthorizationService.can_view_resource(viewer, resource, project)
    
    def test_viewer_can_view_resource_in_assigned_project(self):
        """
        **Validates: Requirement 3.8, 1.5**
        Viewer can view resources in their assigned projects
        """
        project_id = uuid4()
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        viewer.assigned_projects = [project_id]  # Set as attribute, not in constructor
        resource = Resource(id=uuid4(), project_id=project_id)
        project = Project(id=project_id, owner_id=uuid4())
        assert AuthorizationService.can_view_resource(viewer, resource, project)


class TestDashboardAccess:
    """Tests for dashboard access control"""
    
    def test_admin_can_access_dashboard(self):
        """Admin can access dashboard"""
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        assert AuthorizationService.can_access_dashboard(admin)
    
    def test_manager_can_access_dashboard(self):
        """Manager can access dashboard"""
        manager = User(id=uuid4(), role=UserRole.MANAGER)
        assert AuthorizationService.can_access_dashboard(manager)
    
    def test_analyst_can_access_dashboard(self):
        """Analyst can access dashboard"""
        analyst = User(id=uuid4(), role=UserRole.ANALYST)
        assert AuthorizationService.can_access_dashboard(analyst)
    
    def test_viewer_can_access_dashboard(self):
        """Viewer can access dashboard"""
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        assert AuthorizationService.can_access_dashboard(viewer)


class TestImportAuthorization:
    """Tests for import authorization"""
    
    def test_admin_can_import_resources(self):
        """Admin can import resources"""
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        assert AuthorizationService.can_import_resources(admin)
    
    def test_manager_can_import_resources(self):
        """Manager can import resources"""
        manager = User(id=uuid4(), role=UserRole.MANAGER)
        assert AuthorizationService.can_import_resources(manager)
    
    def test_analyst_cannot_import_resources(self):
        """Analyst cannot import resources"""
        analyst = User(id=uuid4(), role=UserRole.ANALYST)
        assert not AuthorizationService.can_import_resources(analyst)
    
    def test_viewer_cannot_import_resources(self):
        """Viewer cannot import resources"""
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        assert not AuthorizationService.can_import_resources(viewer)


class TestAssetTypeManagement:
    """Tests for asset type management authorization"""
    
    def test_only_admin_can_manage_asset_types(self):
        """Only Admin can manage asset types"""
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        manager = User(id=uuid4(), role=UserRole.MANAGER)
        analyst = User(id=uuid4(), role=UserRole.ANALYST)
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        
        assert AuthorizationService.can_manage_asset_types(admin)
        assert not AuthorizationService.can_manage_asset_types(manager)
        assert not AuthorizationService.can_manage_asset_types(analyst)
        assert not AuthorizationService.can_manage_asset_types(viewer)


class TestUserManagement:
    """Tests for user management authorization"""
    
    def test_only_admin_can_manage_users(self):
        """Only Admin can manage users"""
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        manager = User(id=uuid4(), role=UserRole.MANAGER)
        analyst = User(id=uuid4(), role=UserRole.ANALYST)
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        
        assert AuthorizationService.can_manage_users(admin)
        assert not AuthorizationService.can_manage_users(manager)
        assert not AuthorizationService.can_manage_users(analyst)
        assert not AuthorizationService.can_manage_users(viewer)


class TestAuditLogAccess:
    """Tests for audit log access authorization"""
    
    def test_only_admin_can_view_audit_logs(self):
        """Only Admin can view audit logs"""
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        manager = User(id=uuid4(), role=UserRole.MANAGER)
        analyst = User(id=uuid4(), role=UserRole.ANALYST)
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        
        assert AuthorizationService.can_view_audit_logs(admin)
        assert not AuthorizationService.can_view_audit_logs(manager)
        assert not AuthorizationService.can_view_audit_logs(analyst)
        assert not AuthorizationService.can_view_audit_logs(viewer)


class TestPermissionSummary:
    """Tests for permission summary"""
    
    def test_admin_permission_summary(self):
        """
        Admin has all permissions
        """
        admin = User(id=uuid4(), role=UserRole.ADMIN)
        summary = AuthorizationService.get_permission_summary(admin)
        
        assert summary["role"] == UserRole.ADMIN
        assert summary["can_create_project"]
        assert summary["can_manage_users"]
        assert summary["can_manage_asset_types"]
        assert summary["can_import_resources"]
        assert summary["can_view_audit_logs"]
        assert summary["can_access_dashboard"]
    
    def test_manager_permission_summary(self):
        """
        Manager has project/resource management permissions
        """
        manager = User(id=uuid4(), role=UserRole.MANAGER)
        summary = AuthorizationService.get_permission_summary(manager)
        
        assert summary["role"] == UserRole.MANAGER
        assert summary["can_create_project"]
        assert not summary["can_manage_users"]
        assert not summary["can_manage_asset_types"]
        assert summary["can_import_resources"]
        assert not summary["can_view_audit_logs"]
        assert summary["can_access_dashboard"]
    
    def test_analyst_permission_summary(self):
        """
        Analyst has read-only permissions
        """
        analyst = User(id=uuid4(), role=UserRole.ANALYST)
        summary = AuthorizationService.get_permission_summary(analyst)
        
        assert summary["role"] == UserRole.ANALYST
        assert not summary["can_create_project"]
        assert not summary["can_manage_users"]
        assert not summary["can_manage_asset_types"]
        assert not summary["can_import_resources"]
        assert not summary["can_view_audit_logs"]
        assert summary["can_access_dashboard"]
    
    def test_viewer_permission_summary(self):
        """
        Viewer has minimal permissions
        """
        viewer = User(id=uuid4(), role=UserRole.VIEWER)
        summary = AuthorizationService.get_permission_summary(viewer)
        
        assert summary["role"] == UserRole.VIEWER
        assert not summary["can_create_project"]
        assert not summary["can_manage_users"]
        assert not summary["can_manage_asset_types"]
        assert not summary["can_import_resources"]
        assert not summary["can_view_audit_logs"]
        assert summary["can_access_dashboard"]
