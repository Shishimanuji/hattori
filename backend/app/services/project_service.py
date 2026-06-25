"""Project management service"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from uuid import UUID
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import logging

from app.models.project import Project, ProjectStatus
from app.models.resource import Resource, Allocation
from app.models.user import User
from app.services.audit_service import log_audit
from app.models.audit_log import AuditOperation, AuditLogStatus

logger = logging.getLogger(__name__)


class ProjectNotFoundError(Exception):
    """Raised when a project is not found"""
    pass


class ProjectPermissionError(Exception):
    """Raised when user lacks permission to access/modify a project"""
    pass


def get_projects_paginated(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    user: Optional[User] = None,
) -> Tuple[List[Project], int]:
    """
    Get paginated list of projects with filtering and sorting.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination offset)
        limit: Number of records to return (pagination limit)
        status_filter: Filter by project status (Active, Pending, Completed, On Hold)
        search: Search by project name (case-insensitive substring)
        sort_by: Field to sort by (name, budget, created_at, updated_at)
        sort_order: Sort direction (asc, desc)
        user: Optional user for RBAC filtering
        
    Returns:
        Tuple of (projects list, total count)
        
    Raises:
        ValueError: If invalid sort_by or sort_order values
    """
    # Validate sort parameters
    valid_sort_by = ["name", "budget", "created_at", "updated_at"]
    valid_sort_order = ["asc", "desc"]
    
    if sort_by not in valid_sort_by:
        raise ValueError(f"sort_by must be one of {valid_sort_by}")
    if sort_order not in valid_sort_order:
        raise ValueError(f"sort_order must be one of {valid_sort_order}")
    
    # Start with base query (exclude deleted projects)
    query = db.query(Project).filter(Project.deleted_at == None)
    
    # Apply RBAC filtering if user provided
    if user:
        from app.services.authorization_service import AuthorizationService
        query = AuthorizationService.filter_viewable_projects(user, query, db)
    
    # Apply status filter
    if status_filter:
        query = query.filter(Project.status == status_filter)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Project.name.ilike(search_term),
                Project.description.ilike(search_term)
            )
        )
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply sorting
    sort_column = getattr(Project, sort_by)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # Apply pagination
    projects = query.offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(projects)} projects (total: {total_count})")
    
    return projects, total_count


def get_project_by_id(db: Session, project_id: UUID) -> Project:
    """
    Get a project by ID. Includes soft-deleted projects.
    
    Args:
        db: Database session
        project_id: UUID of the project
        
    Returns:
        Project object
        
    Raises:
        ProjectNotFoundError: If project not found
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        logger.warning(f"Project not found: {project_id}")
        raise ProjectNotFoundError(f"Project {project_id} not found")
    
    return project


def create_project(
    db: Session,
    name: str,
    budget: Decimal,
    current_user_id: UUID,
    description: Optional[str] = None,
    status: str = "Active",
    start_date: Optional[Any] = None,
    end_date: Optional[Any] = None,
) -> Project:
    """
    Create a new project.
    
    Args:
        db: Database session
        name: Project name
        budget: Project budget
        current_user_id: UUID of creating user (becomes project owner)
        description: Optional project description
        status: Project status (default: Active)
        start_date: Optional project start date
        end_date: Optional project end date
        
    Returns:
        Created Project object
    """
    try:
        project = Project(
            name=name,
            description=description,
            status=status,
            budget=budget,
            allocated_budget=Decimal("0"),
            start_date=start_date,
            end_date=end_date,
            owner_id=current_user_id,
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Log the creation
        log_audit(
            db=db,
            user_id=current_user_id,
            entity_type="Project",
            entity_id=project.id,
            operation=AuditOperation.CREATE,
            new_values={
                "name": name,
                "budget": str(budget),
                "status": status,
                "owner_id": str(current_user_id),
            },
            status=AuditLogStatus.SUCCESS,
        )
        
        logger.info(f"Project created: {project.id} by user {current_user_id}")
        
        return project
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating project: {str(e)}")
        raise


def update_project(
    db: Session,
    project_id: UUID,
    current_user_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    budget: Optional[Decimal] = None,
    start_date: Optional[Any] = None,
    end_date: Optional[Any] = None,
) -> Project:
    """
    Update an existing project.
    
    Args:
        db: Database session
        project_id: UUID of project to update
        current_user_id: UUID of user performing update (must be owner or admin)
        name: Optional new name
        description: Optional new description
        status: Optional new status
        budget: Optional new budget
        start_date: Optional new start date
        end_date: Optional new end date
        
    Returns:
        Updated Project object
        
    Raises:
        ProjectNotFoundError: If project not found
        ProjectPermissionError: If user lacks permission
    """
    project = get_project_by_id(db, project_id)
    
    # Check permission (must be owner - admin can be added later)
    if project.owner_id != current_user_id:
        # For now, only owner can update. Admin check can be added later.
        logger.warning(
            f"User {current_user_id} attempted to update project {project_id} they don't own"
        )
        raise ProjectPermissionError("Only project owner can update")
    
    # Store old values for audit logging
    old_values = {
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "budget": str(project.budget),
        "start_date": str(project.start_date) if project.start_date else None,
        "end_date": str(project.end_date) if project.end_date else None,
    }
    
    # Update fields
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if status is not None:
        project.status = status
    if budget is not None:
        project.budget = budget
    if start_date is not None:
        project.start_date = start_date
    if end_date is not None:
        project.end_date = end_date
    
    project.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(project)
        
        # Store new values for audit logging
        new_values = {
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "budget": str(project.budget),
            "start_date": str(project.start_date) if project.start_date else None,
            "end_date": str(project.end_date) if project.end_date else None,
        }
        
        # Log the update
        log_audit(
            db=db,
            user_id=current_user_id,
            entity_type="Project",
            entity_id=project.id,
            operation=AuditOperation.UPDATE,
            old_values=old_values,
            new_values=new_values,
            status=AuditLogStatus.SUCCESS,
        )
        
        logger.info(f"Project updated: {project.id} by user {current_user_id}")
        
        return project
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating project: {str(e)}")
        raise


def delete_project(
    db: Session,
    project_id: UUID,
    current_user_id: UUID,
) -> None:
    """
    Soft delete a project (set deleted_at timestamp).
    
    Args:
        db: Database session
        project_id: UUID of project to delete
        current_user_id: UUID of user performing delete (must be owner)
        
    Returns:
        None
        
    Raises:
        ProjectNotFoundError: If project not found
        ProjectPermissionError: If user lacks permission
    """
    project = get_project_by_id(db, project_id)
    
    # Check permission (must be owner - admin can be added later)
    if project.owner_id != current_user_id:
        logger.warning(
            f"User {current_user_id} attempted to delete project {project_id} they don't own"
        )
        raise ProjectPermissionError("Only project owner can delete")
    
    try:
        project.deleted_at = datetime.utcnow()
        db.commit()
        
        # Log the deletion
        log_audit(
            db=db,
            user_id=current_user_id,
            entity_type="Project",
            entity_id=project.id,
            operation=AuditOperation.DELETE,
            old_values={"deleted_at": None},
            new_values={"deleted_at": str(datetime.utcnow())},
            status=AuditLogStatus.SUCCESS,
        )
        
        logger.info(f"Project soft-deleted: {project.id} by user {current_user_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting project: {str(e)}")
        raise


def get_project_resource_summary(db: Session, project_id: UUID) -> Dict[str, Any]:
    """
    Get resource summary for a project (count by type, status).
    
    Args:
        db: Database session
        project_id: UUID of project
        
    Returns:
        Dictionary with resource counts by type
        
    Raises:
        ProjectNotFoundError: If project not found
    """
    project = get_project_by_id(db, project_id)
    
    # Count active resources by asset type
    resources_by_type = {}
    
    # Query resources for this project (exclude deleted)
    resources = db.query(Resource).filter(
        Resource.project_id == project_id,
        Resource.deleted_at == None,
        Resource.status == "Active"
    ).all()
    
    total_count = len(resources)
    
    # Group by asset type
    for resource in resources:
        asset_type_name = resource.asset_type.name if resource.asset_type else "Unknown"
        if asset_type_name not in resources_by_type:
            resources_by_type[asset_type_name] = 0
        resources_by_type[asset_type_name] += 1
    
    logger.debug(f"Resource summary for project {project_id}: {resources_by_type}")
    
    return {
        "total_count": total_count,
        "by_type": resources_by_type,
    }


def check_can_add_resources(db: Session, project_id: UUID) -> bool:
    """
    Check if resources can be added to a project.
    Returns False if project is deleted, otherwise True.
    
    Args:
        db: Database session
        project_id: UUID of project
        
    Returns:
        True if resources can be added, False if project is deleted
        
    Raises:
        ProjectNotFoundError: If project not found
    """
    project = get_project_by_id(db, project_id)
    
    # Cannot add resources to deleted project
    if project.deleted_at is not None:
        logger.warning(f"Attempt to add resources to deleted project {project_id}")
        return False
    
    return True


def update_project_allocated_budget(
    db: Session,
    project_id: UUID,
    amount: Decimal,
    operation: str = "add",
) -> Project:
    """
    Update project allocated budget when resources are allocated/deallocated.
    
    Args:
        db: Database session
        project_id: UUID of project
        amount: Amount to add or subtract
        operation: "add" to increase, "subtract" to decrease
        
    Returns:
        Updated Project object
        
    Raises:
        ProjectNotFoundError: If project not found
    """
    project = get_project_by_id(db, project_id)
    
    current_allocation = Decimal(str(project.allocated_budget))
    
    if operation == "add":
        new_allocation = current_allocation + amount
    elif operation == "subtract":
        new_allocation = current_allocation - amount
    else:
        raise ValueError(f"Invalid operation: {operation}")
    
    # Ensure allocation doesn't go negative
    if new_allocation < 0:
        new_allocation = Decimal("0")
    
    project.allocated_budget = new_allocation
    
    try:
        db.commit()
        db.refresh(project)
        
        logger.info(
            f"Project {project_id} allocated budget updated to {new_allocation} "
            f"(operation: {operation}, amount: {amount})"
        )
        
        return project
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating project allocated budget: {str(e)}")
        raise
