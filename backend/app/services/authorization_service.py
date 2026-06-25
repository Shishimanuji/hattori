"""Authorization service for role-based access control (RBAC)"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from uuid import UUID
from typing import Optional, List
import logging

from app.models.user import User, UserRole
from app.models.project import Project
from app.models.resource import Resource

logger = logging.getLogger(__name__)


class AuthorizationError(Exception):
    """Raised when authorization check fails"""
    pass


class AuthorizationService:
    """Service for RBAC authorization checks across all operations"""
    
    # ==================== Project Authorization ====================
    
    @staticmethod
    def can_create_project(user: User) -> bool:
        """
        Check if user can create projects.
        
        Allowed roles: Admin, Manager
        
        Args:
            user: Current user
            
        Returns:
            True if user can create projects
        """
        return user.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    @staticmethod
    def can_edit_project(user: User, project: Project) -> bool:
        """
        Check if user can edit a project.
        
        Rules:
        - Admin: Can edit any project
        - Manager: Can only edit own projects
        - Analyst: Cannot edit
        - Viewer: Cannot edit
        
        Args:
            user: Current user
            project: Project to check
            
        Returns:
            True if user can edit project
        """
        if user.role == UserRole.ADMIN:
            return True
        if user.role == UserRole.MANAGER:
            return str(user.id) == str(project.owner_id)
        return False
    
    @staticmethod
    def can_delete_project(user: User, project: Project) -> bool:
        """
        Check if user can delete a project.
        
        Rules: Same as edit (Admin any, Manager own)
        
        Args:
            user: Current user
            project: Project to check
            
        Returns:
            True if user can delete project
        """
        return AuthorizationService.can_edit_project(user, project)
    
    @staticmethod
    def can_view_project(
        user: User,
        project: Project,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Check if user can view a project.
        
        Rules:
        - Admin: Can view all projects
        - Manager: Can view all projects
        - Analyst: Can view all projects (read-only)
        - Viewer: Can only view assigned projects
        
        Args:
            user: Current user
            project: Project to check
            db: Database session (needed for Viewer role)
            
        Returns:
            True if user can view project
        """
        if user.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]:
            return True
        
        if user.role == UserRole.VIEWER:
            # Viewers see only assigned projects
            # Check if user has assigned_projects attribute (for testing)
            if hasattr(user, 'assigned_projects') and user.assigned_projects:
                return project.id in user.assigned_projects
            else:
                # No assigned projects means no access
                return False
        
        return False
    
    @staticmethod
    def filter_viewable_projects(
        user: User,
        query,
        db: Optional[Session] = None,
    ):
        """
        Filter project query based on user's viewable projects.
        
        Rules:
        - Admin: All active projects
        - Manager: All active projects (they can edit only their own)
        - Analyst: All active projects (read-only)
        - Viewer: Only assigned projects
        
        Args:
            user: Current user
            query: SQLAlchemy query
            db: Database session (needed for filtering)
            
        Returns:
            Filtered query
        """
        # Exclude soft-deleted projects for all users
        query = query.filter(Project.deleted_at == None)
        
        if user.role == UserRole.ADMIN:
            # Admins see all active projects
            return query
        
        if user.role == UserRole.MANAGER:
            # Managers see all active projects (but can only edit their own)
            return query
        
        if user.role == UserRole.ANALYST:
            # Analysts see all active projects (read-only)
            return query
        
        if user.role == UserRole.VIEWER:
            # Viewers see only assigned projects
            # Check if user_id exists in assigned_projects list (for future enhancement)
            # For now, filter to a specific list if assigned_projects is populated
            if hasattr(user, 'assigned_projects') and user.assigned_projects:
                # If assigned_projects is a list of UUIDs, filter to those projects
                return query.filter(Project.id.in_(user.assigned_projects))
            else:
                # No assigned projects means no access
                return query.filter(Project.id == None)  # Returns empty result
        
        return query.filter(Project.id == None)  # No access by default
    
    # ==================== Resource Authorization ====================
    
    @staticmethod
    def can_create_resource(user: User) -> bool:
        """
        Check if user can create resources.
        
        Allowed roles: Admin, Manager
        
        Args:
            user: Current user
            
        Returns:
            True if user can create resources
        """
        return user.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    @staticmethod
    def can_edit_resource(user: User, resource: Resource, project: Project) -> bool:
        """
        Check if user can edit a resource.
        
        Rules:
        - Admin: Can edit any resource
        - Manager: Can edit resources in own projects
        - Analyst: Cannot edit
        - Viewer: Cannot edit
        
        Args:
            user: Current user
            resource: Resource to check
            project: Project containing resource
            
        Returns:
            True if user can edit resource
        """
        if user.role == UserRole.ADMIN:
            return True
        if user.role == UserRole.MANAGER:
            return str(user.id) == str(project.owner_id)
        return False
    
    @staticmethod
    def can_delete_resource(user: User, resource: Resource, project: Project) -> bool:
        """
        Check if user can delete a resource.
        
        Rules: Same as edit
        
        Args:
            user: Current user
            resource: Resource to check
            project: Project containing resource
            
        Returns:
            True if user can delete resource
        """
        return AuthorizationService.can_edit_resource(user, resource, project)
    
    @staticmethod
    def can_view_resource(
        user: User,
        resource: Resource,
        project: Project,
    ) -> bool:
        """
        Check if user can view a resource.
        
        Rules:
        - Admin: Can view all resources
        - Manager: Can view resources in accessible projects
        - Analyst: Can view all resources (read-only)
        - Viewer: Can view resources in assigned projects only
        
        Args:
            user: Current user
            resource: Resource to check
            project: Project containing resource
            
        Returns:
            True if user can view resource
        """
        if user.role == UserRole.ADMIN:
            return True
        
        if user.role == UserRole.MANAGER:
            return str(user.id) == str(project.owner_id)
        
        if user.role == UserRole.ANALYST:
            return True
        
        if user.role == UserRole.VIEWER:
            # Viewers can only view resources in assigned projects
            if hasattr(user, 'assigned_projects') and user.assigned_projects:
                return resource.project_id in user.assigned_projects
            else:
                return False
        
        return False
    
    @staticmethod
    def filter_viewable_resources(
        user: User,
        query,
        db: Optional[Session] = None,
    ):
        """
        Filter resource query based on user's viewable resources.
        
        Rules:
        - Admin: All active resources
        - Manager: Resources in own projects (projects where owner_id = user_id)
        - Analyst: All active resources (read-only)
        - Viewer: Resources in assigned projects only
        
        Args:
            user: Current user
            query: SQLAlchemy query
            db: Database session (required)
            
        Returns:
            Filtered query
        """
        if db is None:
            # Cannot filter without database session
            return query.filter(Resource.id == None)
        
        # Exclude soft-deleted resources for all users
        query = query.filter(Resource.deleted_at == None)
        
        if user.role == UserRole.ADMIN:
            # Admins see all active resources
            return query
        
        if user.role == UserRole.MANAGER:
            # Managers see resources only in their projects (projects they own)
            manager_projects = db.query(Project.id).filter(
                Project.owner_id == user.id,
                Project.deleted_at == None
            ).subquery()
            query = query.filter(Resource.project_id.in_(manager_projects))
            return query
        
        if user.role == UserRole.ANALYST:
            # Analysts see all active resources (read-only)
            return query
        
        if user.role == UserRole.VIEWER:
            # Viewers see resources only in assigned projects
            # Check if user has assigned_projects
            if hasattr(user, 'assigned_projects') and user.assigned_projects:
                query = query.filter(Resource.project_id.in_(user.assigned_projects))
                return query
            else:
                # No assigned projects means no access
                return query.filter(Resource.id == None)  # Returns empty result
        
        return query.filter(Resource.id == None)  # No access
    
    # ==================== Import Authorization ====================
    
    @staticmethod
    def can_import_resources(user: User) -> bool:
        """
        Check if user can import resources.
        
        Allowed roles: Admin, Manager
        
        Args:
            user: Current user
            
        Returns:
            True if user can import
        """
        return user.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    # ==================== Asset Type Authorization ====================
    
    @staticmethod
    def can_manage_asset_types(user: User) -> bool:
        """
        Check if user can manage asset types.
        
        Allowed roles: Admin only
        
        Args:
            user: Current user
            
        Returns:
            True if user can manage asset types
        """
        return user.role == UserRole.ADMIN
    
    # ==================== User Management Authorization ====================
    
    @staticmethod
    def can_manage_users(user: User) -> bool:
        """
        Check if user can manage users.
        
        Allowed roles: Admin only
        
        Args:
            user: Current user
            
        Returns:
            True if user can manage users
        """
        return user.role == UserRole.ADMIN
    
    # ==================== Audit Log Authorization ====================
    
    @staticmethod
    def can_view_audit_logs(user: User) -> bool:
        """
        Check if user can view audit logs.
        
        Allowed roles: Admin only
        
        Args:
            user: Current user
            
        Returns:
            True if user can view audit logs
        """
        return user.role == UserRole.ADMIN
    
    # ==================== Dashboard Authorization ====================
    
    @staticmethod
    def can_access_dashboard(user: User) -> bool:
        """
        Check if user can access dashboard.
        
        Allowed roles: All authenticated users (Admin, Manager, Analyst, Viewer)
        
        Args:
            user: Current user
            
        Returns:
            True if user can access dashboard
        """
        # All authenticated users can view dashboard
        return user.role in [
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.ANALYST,
            UserRole.VIEWER
        ]
    
    # ==================== Summary Authorization Methods ====================
    
    @staticmethod
    def get_permission_summary(user: User) -> dict:
        """
        Get a summary of all permissions for the user.
        
        Args:
            user: Current user
            
        Returns:
            Dictionary with permission summary
        """
        return {
            "role": user.role,
            "can_create_project": AuthorizationService.can_create_project(user),
            "can_manage_users": AuthorizationService.can_manage_users(user),
            "can_manage_asset_types": AuthorizationService.can_manage_asset_types(user),
            "can_import_resources": AuthorizationService.can_import_resources(user),
            "can_view_audit_logs": AuthorizationService.can_view_audit_logs(user),
            "can_access_dashboard": AuthorizationService.can_access_dashboard(user),
        }
