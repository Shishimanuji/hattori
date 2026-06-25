"""Project management API routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal
from typing import Optional
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
)
from app.utils.dependencies import get_current_user, get_current_manager_user
from app.services.project_service import (
    get_projects_paginated,
    get_project_by_id,
    create_project,
    update_project,
    delete_project,
    get_project_resource_summary,
    check_can_add_resources,
    ProjectNotFoundError,
    ProjectPermissionError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("", response_model=dict)
async def list_projects(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status: Active, Pending, Completed, On Hold"),
    search: Optional[str] = Query(None, description="Search by project name"),
    sort_by: str = Query("created_at", description="Sort by: name, budget, created_at, updated_at"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
):
    """
    List projects with pagination, filtering, and sorting.
    
    - Authentication required (any authenticated user)
    - Returns paginated list of projects filtered by user role
    - Supports filtering by status and search by name
    - Supports sorting by various fields
    
    RBAC applied:
    - Admin: Sees all projects
    - Manager: Sees all projects (can edit only their own)
    - Analyst: Sees all projects (read-only)
    - Viewer: Sees only assigned projects
    
    Query parameters:
    - page: Page number (default 1)
    - page_size: Items per page (default 20, max 100)
    - status: Filter by status (Active, Pending, Completed, On Hold)
    - search: Search by project name (substring match, case-insensitive)
    - sort_by: Sort field (name, budget, created_at, updated_at)
    - sort_order: asc or desc
    
    Returns:
    - 200 OK: { projects: [...], total: int, page: int, page_size: int, total_pages: int }
    - 400 Bad Request: Invalid parameters
    - 401 Unauthorized: Not authenticated
    """
    from app.services.authorization_service import AuthorizationService
    
    try:
        # Calculate offset from page number
        skip = (page - 1) * page_size
        
        # Start with base query
        query = db.query(Project)
        
        # Apply RBAC filtering based on user role
        query = AuthorizationService.filter_viewable_projects(current_user, query, db)
        
        # Get projects with pagination (will apply additional filters in the service)
        projects, total_count = get_projects_paginated(
            db=db,
            skip=skip,
            limit=page_size,
            status_filter=status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            user=current_user,  # Pass user for filtering
        )
        
        # Convert to response models
        project_responses = [
            ProjectResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                status=p.status,
                budget=p.budget,
                owner_id=p.owner_id,
                allocated_budget=p.allocated_budget,
                remaining_budget=p.remaining_budget,
                utilization_percentage=p.utilization_percentage,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in projects
        ]
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "projects": project_responses,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
        
    except ValueError as e:
        logger.warning(f"Invalid parameters in list_projects: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project_endpoint(
    request: Request,
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new project.
    
    - Authentication required (Manager or Admin role)
    - Auto-set: owner_id = current_user_id
    - Audit logged: CREATE_PROJECT
    - RBAC enforced: Only Admin and Manager can create
    
    Request body:
    - name: string (required, 1-255 characters)
    - budget: decimal (required, > 0)
    - description: string (optional)
    - status: string (optional, default: "Active")
    - start_date: date (optional)
    - end_date: date (optional)
    
    Returns:
    - 201 Created: Project object
    - 400 Bad Request: Invalid data
    - 403 Forbidden: Insufficient permissions
    - 422 Unprocessable Entity: Validation error
    """
    from app.services.authorization_service import AuthorizationService
    
    try:
        # Check authorization
        if not AuthorizationService.can_create_project(current_user):
            logger.warning(f"User {current_user.id} with role {current_user.role} denied project creation")
            raise HTTPException(
                status_code=403,
                detail="Only Admin and Manager roles can create projects"
            )
        
        project = create_project(
            db=db,
            name=project_data.name,
            budget=project_data.budget,
            description=project_data.description,
            status=project_data.status,
            start_date=project_data.start_date,
            end_date=project_data.end_date,
            current_user_id=current_user.id,
        )
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            budget=project.budget,
            owner_id=project.owner_id,
            allocated_budget=project.allocated_budget,
            remaining_budget=project.remaining_budget,
            utilization_percentage=project.utilization_percentage,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get project details with resource summary.
    
    - Authentication required (any authenticated user)
    - Returns project with resource count and allocation details
    
    Path parameters:
    - project_id: UUID of project
    
    Returns:
    - 200 OK: Detailed project object with resource summary
    - 401 Unauthorized: Not authenticated
    - 404 Not Found: Project not found
    """
    try:
        project = get_project_by_id(db=db, project_id=project_id)
        
        # Get resource summary
        resource_summary = get_project_resource_summary(db=db, project_id=project_id)
        
        return ProjectDetailResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            budget=project.budget,
            owner_id=project.owner_id,
            allocated_budget=project.allocated_budget,
            remaining_budget=project.remaining_budget,
            utilization_percentage=project.utilization_percentage,
            created_at=project.created_at,
            updated_at=project.updated_at,
            resource_count=resource_summary["total_count"],
            resources_by_type=resource_summary["by_type"],
        )
        
    except ProjectNotFoundError:
        logger.warning(f"Project not found: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        logger.error(f"Error retrieving project: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project_endpoint(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update project details.
    
    - Authentication required (Project owner)
    - Cannot change owner (admin-only later)
    - Updates updated_at timestamp
    - Audit logged: UPDATE_PROJECT
    
    Path parameters:
    - project_id: UUID of project
    
    Request body (all optional):
    - name: string
    - description: string
    - status: string
    - budget: decimal (> 0)
    - start_date: date
    - end_date: date
    
    Returns:
    - 200 OK: Updated project object
    - 400 Bad Request: Invalid data
    - 403 Forbidden: Not project owner
    - 404 Not Found: Project not found
    - 422 Unprocessable Entity: Validation error
    """
    try:
        project = update_project(
            db=db,
            project_id=project_id,
            current_user_id=current_user.id,
            name=project_data.name,
            description=project_data.description,
            status=project_data.status,
            budget=project_data.budget,
            start_date=project_data.start_date,
            end_date=project_data.end_date,
        )
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            budget=project.budget,
            owner_id=project.owner_id,
            allocated_budget=project.allocated_budget,
            remaining_budget=project.remaining_budget,
            utilization_percentage=project.utilization_percentage,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        
    except ProjectNotFoundError:
        logger.warning(f"Project not found: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")
    except ProjectPermissionError:
        logger.warning(f"User {current_user.id} lacks permission to update project {project_id}")
        raise HTTPException(status_code=403, detail="You don't have permission to update this project")
    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{project_id}", status_code=204)
async def delete_project_endpoint(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Soft delete a project (set deleted_at timestamp).
    
    - Authentication required (Project owner)
    - Prevents adding resources to deleted projects
    - Data is retained for historical queries
    - Audit logged: DELETE_PROJECT
    
    Path parameters:
    - project_id: UUID of project
    
    Returns:
    - 204 No Content: Project deleted successfully
    - 403 Forbidden: Not project owner
    - 404 Not Found: Project not found
    """
    try:
        delete_project(
            db=db,
            project_id=project_id,
            current_user_id=current_user.id,
        )
        
        return None
        
    except ProjectNotFoundError:
        logger.warning(f"Project not found: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")
    except ProjectPermissionError:
        logger.warning(f"User {current_user.id} lacks permission to delete project {project_id}")
        raise HTTPException(status_code=403, detail="You don't have permission to delete this project")
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
