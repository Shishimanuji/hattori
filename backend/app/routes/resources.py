"""Resource management API routes with RBAC enforcement"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal
from typing import Optional
from datetime import date
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.resource import Allocation
from app.schemas.project import ProjectResponse
from app.utils.dependencies import get_current_user
from app.services.resource_service import (
    get_resources_paginated,
    get_resource_by_id,
    create_resource,
    update_resource,
    delete_resource,
    ResourceNotFoundError,
    ResourcePermissionError,
)
from app.services.authorization_service import AuthorizationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resources", tags=["Resources"])


@router.get("", response_model=dict)
async def list_resources(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    asset_type_id: Optional[str] = Query(None, description="Filter by asset type ID"),
    status: Optional[str] = Query(None, description="Filter by status: Active, Inactive"),
    search: Optional[str] = Query(None, description="Search by resource name"),
    sort_by: str = Query("created_at", description="Sort by: name, cost, created_at, updated_at"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
):
    """
    List resources with pagination, filtering, and sorting.
    
    - Authentication required (any authenticated user)
    - Returns paginated list of resources filtered by user role
    - Supports filtering by project, asset type, status, and search by name
    
    RBAC applied:
    - Admin: Sees all resources
    - Manager: Sees resources in their projects only
    - Analyst: Sees all resources (read-only)
    - Viewer: Sees resources in assigned projects only
    
    Query parameters:
    - page: Page number (default 1)
    - page_size: Items per page (default 20, max 100)
    - project_id: Filter by project UUID
    - asset_type_id: Filter by asset type UUID
    - status: Filter by status (Active, Inactive)
    - search: Search by resource name (substring match, case-insensitive)
    - sort_by: Sort field (name, cost, created_at, updated_at)
    - sort_order: asc or desc
    
    Returns:
    - 200 OK: { resources: [...], total: int, page: int, page_size: int, total_pages: int }
    - 400 Bad Request: Invalid parameters
    - 401 Unauthorized: Not authenticated
    """
    try:
        # Parse optional UUIDs
        parsed_project_id = None
        parsed_asset_type_id = None
        
        if project_id:
            try:
                parsed_project_id = UUID(project_id)
            except ValueError:
                raise ValueError(f"Invalid project_id format: {project_id}")
        
        if asset_type_id:
            try:
                parsed_asset_type_id = UUID(asset_type_id)
            except ValueError:
                raise ValueError(f"Invalid asset_type_id format: {asset_type_id}")
        
        # Calculate offset from page number
        skip = (page - 1) * page_size
        
        # Get resources with pagination and RBAC filtering
        resources, total_count = get_resources_paginated(
            db=db,
            skip=skip,
            limit=page_size,
            project_id=parsed_project_id,
            asset_type_id=parsed_asset_type_id,
            status_filter=status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            current_user=current_user,
        )
        
        # Convert to response format
        resource_responses = []
        for r in resources:
            resource_responses.append({
                "id": str(r.id),
                "project_id": str(r.project_id),
                "asset_type_id": str(r.asset_type_id),
                "name": r.name,
                "cost": float(r.cost),
                "allocation_date": r.allocation_date.isoformat(),
                "status": r.status,
                "custom_field_values": r.custom_field_values or {},
                "created_by": str(r.created_by),
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            })
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "resources": resource_responses,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
        
    except ValueError as e:
        logger.warning(f"Invalid parameters in list_resources: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", status_code=201)
async def create_resource_endpoint(
    request: Request,
    project_id: str = Query(..., description="Project UUID"),
    asset_type_id: str = Query(..., description="Asset type UUID"),
    name: str = Query(..., description="Resource name"),
    cost: Decimal = Query(..., description="Resource cost"),
    allocation_date: date = Query(..., description="Allocation date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new resource.
    
    - Authentication required (Manager or Admin role)
    - RBAC enforced: Only Admin and Manager can create
    - Manager can only create in their own projects
    - Budget constraint enforced
    - Audit logged: CREATE
    
    Query parameters:
    - project_id: UUID of project (required)
    - asset_type_id: UUID of asset type (required)
    - name: Resource name (required)
    - cost: Resource cost (required, > 0)
    - allocation_date: Allocation date YYYY-MM-DD (required)
    
    Returns:
    - 201 Created: Resource object
    - 400 Bad Request: Invalid data or constraints violated
    - 403 Forbidden: Insufficient permissions
    - 404 Not Found: Project or asset type not found
    """
    try:
        # Parse UUIDs
        try:
            parsed_project_id = UUID(project_id)
            parsed_asset_type_id = UUID(asset_type_id)
        except ValueError as e:
            raise ValueError(f"Invalid UUID format: {str(e)}")
        
        # Create resource
        resource = create_resource(
            db=db,
            project_id=parsed_project_id,
            asset_type_id=parsed_asset_type_id,
            name=name,
            cost=cost,
            allocation_date=allocation_date,
            current_user_id=current_user.id,
        )
        
        return {
            "id": str(resource.id),
            "project_id": str(resource.project_id),
            "asset_type_id": str(resource.asset_type_id),
            "name": resource.name,
            "cost": float(resource.cost),
            "allocation_date": resource.allocation_date.isoformat(),
            "status": resource.status,
            "custom_field_values": resource.custom_field_values or {},
            "created_by": str(resource.created_by),
            "created_at": resource.created_at.isoformat(),
            "updated_at": resource.updated_at.isoformat(),
        }
        
    except ResourcePermissionError as e:
        logger.warning(f"Resource creation denied: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        logger.warning(f"Invalid input for resource creation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating resource: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{resource_id}")
async def get_resource(
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get resource details.
    
    - Authentication required (any authenticated user)
    - RBAC enforced: User can only view resources in projects they have access to
    
    Path parameters:
    - resource_id: UUID of resource
    
    Returns:
    - 200 OK: Resource object
    - 401 Unauthorized: Not authenticated
    - 403 Forbidden: No access to resource
    - 404 Not Found: Resource not found
    """
    try:
        try:
            parsed_resource_id = UUID(resource_id)
        except ValueError:
            raise ValueError(f"Invalid resource_id format: {resource_id}")
        
        resource = get_resource_by_id(db, parsed_resource_id)
        
        # Check view permission
        from app.services.project_service import get_project_by_id
        project = get_project_by_id(db, resource.project_id)
        
        if not AuthorizationService.can_view_resource(current_user, resource, project):
            logger.warning(f"User {current_user.id} denied access to resource {resource_id}")
            raise HTTPException(status_code=403, detail="You don't have permission to view this resource")
        
        return {
            "id": str(resource.id),
            "project_id": str(resource.project_id),
            "asset_type_id": str(resource.asset_type_id),
            "name": resource.name,
            "cost": float(resource.cost),
            "allocation_date": resource.allocation_date.isoformat(),
            "status": resource.status,
            "custom_field_values": resource.custom_field_values or {},
            "created_by": str(resource.created_by),
            "created_at": resource.created_at.isoformat(),
            "updated_at": resource.updated_at.isoformat(),
        }
        
    except ValueError as e:
        logger.warning(f"Invalid resource_id: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError:
        logger.warning(f"Resource not found: {resource_id}")
        raise HTTPException(status_code=404, detail="Resource not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving resource: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{resource_id}")
async def update_resource_endpoint(
    resource_id: str,
    project_id: str = Query(..., description="Project UUID"),
    name: Optional[str] = Query(None, description="New resource name"),
    cost: Optional[Decimal] = Query(None, description="New resource cost"),
    allocation_date: Optional[date] = Query(None, description="New allocation date"),
    status: Optional[str] = Query(None, description="New status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update resource details.
    
    - Authentication required (Manager or Admin role in their project)
    - RBAC enforced: Only project owner can edit resources
    - Budget constraint checked if cost changes
    - Audit logged: UPDATE
    
    Path parameters:
    - resource_id: UUID of resource
    
    Query parameters:
    - project_id: UUID of project (required)
    - name: New resource name (optional)
    - cost: New resource cost (optional)
    - allocation_date: New allocation date (optional)
    - status: New status (optional)
    
    Returns:
    - 200 OK: Updated resource object
    - 400 Bad Request: Invalid data or constraints violated
    - 403 Forbidden: No permission to update
    - 404 Not Found: Resource or project not found
    """
    try:
        # Parse UUIDs
        try:
            parsed_resource_id = UUID(resource_id)
            parsed_project_id = UUID(project_id)
        except ValueError as e:
            raise ValueError(f"Invalid UUID format: {str(e)}")
        
        # Update resource
        resource = update_resource(
            db=db,
            resource_id=parsed_resource_id,
            project_id=parsed_project_id,
            current_user_id=current_user.id,
            name=name,
            cost=cost,
            allocation_date=allocation_date,
            status=status,
        )
        
        return {
            "id": str(resource.id),
            "project_id": str(resource.project_id),
            "asset_type_id": str(resource.asset_type_id),
            "name": resource.name,
            "cost": float(resource.cost),
            "allocation_date": resource.allocation_date.isoformat(),
            "status": resource.status,
            "custom_field_values": resource.custom_field_values or {},
            "created_by": str(resource.created_by),
            "created_at": resource.created_at.isoformat(),
            "updated_at": resource.updated_at.isoformat(),
        }
        
    except ResourcePermissionError as e:
        logger.warning(f"Resource update denied: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except ResourceNotFoundError:
        logger.warning(f"Resource not found: {resource_id}")
        raise HTTPException(status_code=404, detail="Resource not found")
    except ValueError as e:
        logger.warning(f"Invalid input for resource update: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating resource: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{resource_id}", status_code=204)
async def delete_resource_endpoint(
    resource_id: str,
    project_id: str = Query(..., description="Project UUID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Soft delete a resource (set deleted_at timestamp).
    
    - Authentication required (Manager or Admin role in their project)
    - RBAC enforced: Only project owner can delete resources
    - Cost returned to project budget
    - Audit logged: DELETE
    
    Path parameters:
    - resource_id: UUID of resource
    
    Query parameters:
    - project_id: UUID of project (required)
    
    Returns:
    - 204 No Content: Resource deleted successfully
    - 403 Forbidden: No permission to delete
    - 404 Not Found: Resource or project not found
    """
    try:
        # Parse UUIDs
        try:
            parsed_resource_id = UUID(resource_id)
            parsed_project_id = UUID(project_id)
        except ValueError as e:
            raise ValueError(f"Invalid UUID format: {str(e)}")
        
        # Delete resource
        delete_resource(
            db=db,
            resource_id=parsed_resource_id,
            project_id=parsed_project_id,
            current_user_id=current_user.id,
        )
        
        return None
        
    except ResourcePermissionError as e:
        logger.warning(f"Resource deletion denied: {str(e)}")
        raise HTTPException(status_code=403, detail=str(e))
    except ResourceNotFoundError:
        logger.warning(f"Resource not found: {resource_id}")
        raise HTTPException(status_code=404, detail="Resource not found")
    except ValueError as e:
        logger.warning(f"Invalid input for resource deletion: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting resource: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")



@router.get("/{resource_id}/history")
async def get_resource_history(
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get allocation history for a resource.
    
    - Authentication required (any authenticated user)
    - RBAC enforced: User can only view history for resources in projects they have access to
    - Returns all allocation and deallocation events for the resource
    
    Path parameters:
    - resource_id: UUID of resource
    
    Returns:
    - 200 OK: { data: [...] } where each entry contains allocation details
    - 401 Unauthorized: Not authenticated
    - 403 Forbidden: No access to resource
    - 404 Not Found: Resource not found
    """
    try:
        try:
            parsed_resource_id = UUID(resource_id)
        except ValueError:
            raise ValueError(f"Invalid resource_id format: {resource_id}")
        
        # Get the resource first to check permissions
        resource = get_resource_by_id(db, parsed_resource_id)
        
        # Check view permission
        from app.services.project_service import get_project_by_id
        project = get_project_by_id(db, resource.project_id)
        
        if not AuthorizationService.can_view_resource(current_user, resource, project):
            logger.warning(f"User {current_user.id} denied access to resource history {resource_id}")
            raise HTTPException(status_code=403, detail="You don't have permission to view this resource")
        
        # Get allocation history from the allocations table
        allocations = db.query(Allocation).filter(
            Allocation.resource_id == parsed_resource_id
        ).order_by(Allocation.allocated_at.desc()).all()
        
        # Format the response
        history = []
        for allocation in allocations:
            history.append({
                "allocation_date": allocation.allocated_at.isoformat(),
                "deallocation_date": allocation.deallocated_at.isoformat() if allocation.deallocated_at else None,
                "cost_at_allocation": float(allocation.cost_at_allocation),
                "created_by": str(allocation.created_by),
            })
        
        return {
            "data": history
        }
        
    except ValueError as e:
        logger.warning(f"Invalid resource_id: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError:
        logger.warning(f"Resource not found: {resource_id}")
        raise HTTPException(status_code=404, detail="Resource not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving resource history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
