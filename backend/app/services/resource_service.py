"""Resource management service with RBAC support"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from uuid import UUID
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date
import logging

from app.models.resource import Resource, ResourceStatus, Allocation
from app.models.project import Project
from app.models.asset_type import AssetType, CustomField
from app.models.user import User
from app.services.audit_service import log_audit
from app.models.audit_log import AuditOperation, AuditLogStatus
from app.services.authorization_service import AuthorizationService

logger = logging.getLogger(__name__)


class ResourceNotFoundError(Exception):
    """Raised when a resource is not found"""
    pass


class ResourcePermissionError(Exception):
    """Raised when user lacks permission to access/modify a resource"""
    pass


class ResourceAlreadyExistsError(Exception):
    """Raised when trying to create a duplicate resource"""
    pass


def get_resources_paginated(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    project_id: Optional[UUID] = None,
    asset_type_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: Optional[User] = None,
) -> Tuple[List[Resource], int]:
    """
    Get paginated list of resources with filtering and sorting.
    Applies RBAC filtering based on user role.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination offset)
        limit: Number of records to return (pagination limit)
        project_id: Optional filter by project ID
        asset_type_id: Optional filter by asset type ID
        status_filter: Filter by resource status (Active, Inactive)
        search: Search by resource name (case-insensitive substring)
        sort_by: Field to sort by (name, cost, created_at, updated_at)
        sort_order: Sort direction (asc, desc)
        current_user: Current user for RBAC filtering
        
    Returns:
        Tuple of (resources list, total count)
        
    Raises:
        ValueError: If invalid sort_by or sort_order values
    """
    # Validate sort parameters
    valid_sort_by = ["name", "cost", "created_at", "updated_at", "allocation_date"]
    valid_sort_order = ["asc", "desc"]
    
    if sort_by not in valid_sort_by:
        raise ValueError(f"sort_by must be one of {valid_sort_by}")
    if sort_order not in valid_sort_order:
        raise ValueError(f"sort_order must be one of {valid_sort_order}")
    
    # Start with base query (exclude deleted resources)
    query = db.query(Resource).filter(Resource.deleted_at == None)
    
    # Apply RBAC filtering if user provided
    if current_user:
        query = AuthorizationService.filter_viewable_resources(current_user, query, db)
    
    # Apply project filter
    if project_id:
        query = query.filter(Resource.project_id == project_id)
    
    # Apply asset type filter
    if asset_type_id:
        query = query.filter(Resource.asset_type_id == asset_type_id)
    
    # Apply status filter
    if status_filter:
        query = query.filter(Resource.status == status_filter)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(Resource.name.ilike(search_term))
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply sorting
    sort_column = getattr(Resource, sort_by)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # Apply pagination
    resources = query.offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(resources)} resources (total: {total_count})")
    
    return resources, total_count


def get_resource_by_id(db: Session, resource_id: UUID) -> Resource:
    """
    Get a resource by ID. Includes soft-deleted resources.
    
    Args:
        db: Database session
        resource_id: UUID of the resource
        
    Returns:
        Resource object
        
    Raises:
        ResourceNotFoundError: If resource not found
    """
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    
    if not resource:
        logger.warning(f"Resource not found: {resource_id}")
        raise ResourceNotFoundError(f"Resource {resource_id} not found")
    
    return resource


def create_resource(
    db: Session,
    project_id: UUID,
    asset_type_id: UUID,
    name: str,
    cost: Decimal,
    allocation_date: date,
    current_user_id: UUID,
    custom_field_values: Optional[Dict[str, Any]] = None,
    status: str = ResourceStatus.ACTIVE,
) -> Resource:
    """
    Create a new resource with RBAC permission check.
    
    Args:
        db: Database session
        project_id: UUID of project
        asset_type_id: UUID of asset type
        name: Resource name
        cost: Resource cost
        allocation_date: Allocation date
        current_user_id: UUID of creating user
        custom_field_values: Optional custom field values
        status: Resource status (default: Active)
        
    Returns:
        Created Resource object
        
    Raises:
        ProjectNotFoundError: If project not found
        AssetTypeNotFoundError: If asset type not found
        ResourcePermissionError: If user lacks create permission
        ValueError: If project is deleted or budget exceeded
    """
    from app.services.project_service import get_project_by_id, update_project_allocated_budget
    
    try:
        # Get current user for permission check
        user = db.query(User).filter(User.id == current_user_id).first()
        if not user:
            raise ValueError(f"User {current_user_id} not found")
        
        # Check authorization
        if not AuthorizationService.can_create_resource(user):
            logger.warning(f"User {current_user_id} with role {user.role} denied resource creation")
            raise ResourcePermissionError("Only Admin and Manager roles can create resources")
        
        # Get project and verify it exists and is not deleted
        project = get_project_by_id(db, project_id)
        if project.deleted_at is not None:
            raise ValueError(f"Cannot add resources to deleted project {project_id}")
        
        # Verify project owner (for Manager role)
        if user.role == "Manager" and str(user.id) != str(project.owner_id):
            logger.warning(
                f"Manager {current_user_id} attempted to create resource in project {project_id} they don't own"
            )
            raise ResourcePermissionError("Managers can only add resources to their own projects")
        
        # Get asset type to verify it exists
        asset_type = db.query(AssetType).filter(AssetType.id == asset_type_id).first()
        if not asset_type:
            raise ValueError(f"Asset type {asset_type_id} not found")
        
        # Check budget constraint
        proposed_allocated = Decimal(str(project.allocated_budget)) + cost
        if proposed_allocated > Decimal(str(project.budget)):
            logger.warning(
                f"Budget exceeded: project {project_id} budget {project.budget} < "
                f"proposed allocation {proposed_allocated}"
            )
            raise ValueError(
                f"Cannot allocate resource. Budget constraint exceeded: "
                f"allocated {proposed_allocated} > budget {project.budget}"
            )
        
        # Initialize custom field values
        if custom_field_values is None:
            custom_field_values = {}
        
        # Create resource
        resource = Resource(
            project_id=project_id,
            asset_type_id=asset_type_id,
            name=name,
            cost=cost,
            allocation_date=allocation_date,
            status=status,
            custom_field_values=custom_field_values,
            created_by=current_user_id,
        )
        
        db.add(resource)
        db.flush()  # Get the ID before creating allocation
        
        # Create allocation record
        allocation = Allocation(
            resource_id=resource.id,
            project_id=project_id,
            cost_at_allocation=cost,
            created_by=current_user_id,
        )
        db.add(allocation)
        
        # Update project allocated budget
        update_project_allocated_budget(db, project_id, cost, "add")
        
        db.commit()
        db.refresh(resource)
        
        # Log the creation
        log_audit(
            db=db,
            user_id=current_user_id,
            entity_type="Resource",
            entity_id=resource.id,
            operation=AuditOperation.CREATE,
            new_values={
                "name": name,
                "cost": str(cost),
                "project_id": str(project_id),
                "asset_type_id": str(asset_type_id),
                "status": status,
            },
            status=AuditLogStatus.SUCCESS,
        )
        
        logger.info(f"Resource created: {resource.id} by user {current_user_id}")
        
        return resource
        
    except (ResourcePermissionError, ValueError) as e:
        db.rollback()
        logger.warning(f"Resource creation rejected: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating resource: {str(e)}")
        raise


def update_resource(
    db: Session,
    resource_id: UUID,
    project_id: UUID,
    current_user_id: UUID,
    name: Optional[str] = None,
    cost: Optional[Decimal] = None,
    allocation_date: Optional[date] = None,
    status: Optional[str] = None,
    custom_field_values: Optional[Dict[str, Any]] = None,
) -> Resource:
    """
    Update an existing resource with RBAC permission check.
    
    Args:
        db: Database session
        resource_id: UUID of resource to update
        project_id: UUID of project containing resource
        current_user_id: UUID of user performing update
        name: Optional new name
        cost: Optional new cost
        allocation_date: Optional new allocation date
        status: Optional new status
        custom_field_values: Optional new custom field values
        
    Returns:
        Updated Resource object
        
    Raises:
        ResourceNotFoundError: If resource not found
        ResourcePermissionError: If user lacks permission
    """
    from app.services.project_service import get_project_by_id, update_project_allocated_budget
    
    try:
        # Get current user for permission check
        user = db.query(User).filter(User.id == current_user_id).first()
        if not user:
            raise ValueError(f"User {current_user_id} not found")
        
        resource = get_resource_by_id(db, resource_id)
        project = get_project_by_id(db, project_id)
        
        # Check authorization
        if not AuthorizationService.can_edit_resource(user, resource, project):
            logger.warning(f"User {current_user_id} denied resource update for {resource_id}")
            raise ResourcePermissionError("You don't have permission to update this resource")
        
        # Store old values for audit logging
        old_values = {
            "name": resource.name,
            "cost": str(resource.cost),
            "status": resource.status,
        }
        
        # Handle cost change
        if cost is not None and cost != resource.cost:
            cost_difference = cost - resource.cost
            
            # Check budget constraint with new cost
            proposed_allocated = Decimal(str(project.allocated_budget)) + cost_difference
            if proposed_allocated > Decimal(str(project.budget)):
                raise ValueError(
                    f"Cannot update resource. Budget constraint exceeded: "
                    f"allocated {proposed_allocated} > budget {project.budget}"
                )
            
            # Update project budget if cost changed
            update_project_allocated_budget(db, project_id, cost_difference, "add")
        
        # Update fields
        if name is not None:
            resource.name = name
        if cost is not None:
            resource.cost = cost
        if allocation_date is not None:
            resource.allocation_date = allocation_date
        if status is not None:
            resource.status = status
        if custom_field_values is not None:
            resource.custom_field_values = custom_field_values
        
        resource.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(resource)
        
        # Store new values for audit logging
        new_values = {
            "name": resource.name,
            "cost": str(resource.cost),
            "status": resource.status,
        }
        
        # Log the update
        log_audit(
            db=db,
            user_id=current_user_id,
            entity_type="Resource",
            entity_id=resource.id,
            operation=AuditOperation.UPDATE,
            old_values=old_values,
            new_values=new_values,
            status=AuditLogStatus.SUCCESS,
        )
        
        logger.info(f"Resource updated: {resource.id} by user {current_user_id}")
        
        return resource
        
    except (ResourcePermissionError, ValueError) as e:
        db.rollback()
        logger.warning(f"Resource update rejected: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating resource: {str(e)}")
        raise


def delete_resource(
    db: Session,
    resource_id: UUID,
    project_id: UUID,
    current_user_id: UUID,
) -> None:
    """
    Soft delete a resource (set deleted_at timestamp) with RBAC permission check.
    
    Args:
        db: Database session
        resource_id: UUID of resource to delete
        project_id: UUID of project containing resource
        current_user_id: UUID of user performing delete
        
    Returns:
        None
        
    Raises:
        ResourceNotFoundError: If resource not found
        ResourcePermissionError: If user lacks permission
    """
    from app.services.project_service import get_project_by_id, update_project_allocated_budget
    
    try:
        # Get current user for permission check
        user = db.query(User).filter(User.id == current_user_id).first()
        if not user:
            raise ValueError(f"User {current_user_id} not found")
        
        resource = get_resource_by_id(db, resource_id)
        project = get_project_by_id(db, project_id)
        
        # Check authorization
        if not AuthorizationService.can_delete_resource(user, resource, project):
            logger.warning(f"User {current_user_id} denied resource deletion for {resource_id}")
            raise ResourcePermissionError("You don't have permission to delete this resource")
        
        # Return cost to project budget
        update_project_allocated_budget(db, project_id, resource.cost, "subtract")
        
        resource.deleted_at = datetime.utcnow()
        db.commit()
        
        # Log the deletion
        log_audit(
            db=db,
            user_id=current_user_id,
            entity_type="Resource",
            entity_id=resource.id,
            operation=AuditOperation.DELETE,
            old_values={"deleted_at": None},
            new_values={"deleted_at": str(datetime.utcnow())},
            status=AuditLogStatus.SUCCESS,
        )
        
        logger.info(f"Resource soft-deleted: {resource.id} by user {current_user_id}")
        
    except (ResourcePermissionError, ValueError) as e:
        db.rollback()
        logger.warning(f"Resource deletion rejected: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting resource: {str(e)}")
        raise
