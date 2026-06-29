"""API routes for resource type management"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.models import User
from app.utils.dependencies import get_current_user
from app.schemas.asset import ResourceFieldSchema
from app.services.resource_type_service import ResourceTypeService

router = APIRouter(prefix="/api/resource-types", tags=["resource-types"])


@router.get("", response_model=List[dict])
def list_resource_types(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all resource types"""
    resource_types = ResourceTypeService.get_all_resource_types(db, active_only=active_only)
    return [
        {
            "id": rt.id,
            "name": rt.name,
            "display_name": rt.display_name,
            "icon": rt.icon,
            "display_order": rt.display_order,
            "is_active": rt.is_active
        }
        for rt in resource_types
    ]


@router.get("/{resource_type_id}/fields", response_model=List[ResourceFieldSchema])
def get_resource_fields(
    resource_type_id: UUID,
    visible_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all fields for a resource type"""
    fields = ResourceTypeService.get_resource_fields(db, resource_type_id, visible_only=visible_only)
    return fields


@router.post("/{resource_type_id}/fields", response_model=ResourceFieldSchema, status_code=status.HTTP_201_CREATED)
def create_resource_field(
    resource_type_id: UUID,
    field_name: str,
    display_name: str,
    data_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new resource field (Admin only)"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create fields"
        )
    
    # Auto-assign next display order
    field = ResourceTypeService.add_field_to_end(
        db,
        resource_type_id,
        field_name,
        display_name,
        data_type
    )
    return field


@router.put("/fields/{field_id}", response_model=ResourceFieldSchema)
def update_resource_field(
    field_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    **kwargs
):
    """Update a resource field (Admin only)"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update fields"
        )
    
    field = ResourceTypeService.update_resource_field(db, field_id, **kwargs)
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found"
        )
    return field


@router.delete("/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource_field(
    field_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a resource field (Admin only)"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete fields"
        )
    
    success = ResourceTypeService.delete_resource_field(db, field_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found"
        )