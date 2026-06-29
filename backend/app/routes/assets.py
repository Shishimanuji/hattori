"""API routes for asset management"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.models import User
from app.utils.dependencies import get_current_user
from app.schemas.asset import (
    AssetSchema, AssetCreateSchema, AssetUpdateSchema, AssetListSchema
)
from app.services.asset_service import AssetService

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.post("", response_model=AssetSchema, status_code=status.HTTP_201_CREATED)
def create_asset(
    asset_data: AssetCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new asset"""
    if not current_user.can_manage_projects():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        asset = AssetService.create_asset(db, asset_data, current_user.id)
        return asset
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{asset_id}", response_model=AssetSchema)
def get_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset by ID"""
    asset = AssetService.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    return asset


@router.get("/project/{project_id}", response_model=List[AssetListSchema])
def list_project_assets(
    project_id: UUID,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all assets in a project"""
    assets = AssetService.get_project_assets(db, project_id, active_only=active_only)
    return assets


@router.put("/{asset_id}", response_model=AssetSchema)
def update_asset(
    asset_id: UUID,
    asset_data: AssetUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update asset"""
    if not current_user.can_manage_projects():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        asset = AssetService.update_asset(db, asset_id, asset_data)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        return asset
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete asset (soft delete)"""
    if not current_user.can_manage_projects():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    success = AssetService.delete_asset(db, asset_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )


@router.get("/{asset_id}/warranty-expiring")
def get_warranty_expiring_assets(
    project_id: UUID,
    days: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assets with warranty expiring soon"""
    assets = AssetService.get_warranty_expiring_assets(db, project_id, days)
    return assets


@router.get("/{project_id}/audit-due")
def get_assets_requiring_audit(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assets requiring audit"""
    assets = AssetService.get_assets_requiring_audit(db, project_id)
    return assets


@router.get("/{project_id}/summary")
def get_asset_summary(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset summary for project"""
    summary = AssetService.get_asset_summary_by_type(db, project_id)
    total_value = AssetService.calculate_project_asset_value(db, project_id)
    return {
        "by_type": summary,
        "total_value": total_value
    }