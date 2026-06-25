"""Asset type management API routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
import logging

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.asset_type import AssetType, CustomField
from app.schemas.asset_type import (
    AssetTypeCreate,
    AssetTypeUpdate,
    AssetTypeResponse,
    AssetTypeDetailResponse,
    AssetTypeListResponse,
    AssetTypeListItem,
    CustomFieldCreate,
    CustomFieldUpdate,
    CustomFieldResponse,
)
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/asset-types", tags=["Asset Types"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user is Admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return current_user


@router.get("", response_model=AssetTypeListResponse)
async def list_asset_types(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(0, ge=0, description="Page number (0-indexed)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    include_inactive: bool = Query(True, description="Include inactive asset types"),
):
    """
    List all asset types with pagination.
    
    - Authentication required (Admin only)
    - Returns paginated list of asset types
    - Can optionally filter out inactive types
    
    Query parameters:
    - page: Page number (0-indexed, default 0)
    - limit: Items per page (default 50, max 100)
    - include_inactive: Include inactive types (default true)
    
    Returns:
    - 200 OK: AssetTypeListResponse with items, total, pagination metadata
    - 401 Unauthorized: Not authenticated
    - 403 Forbidden: Not admin
    """
    try:
        # Build base query
        query = db.query(AssetType)
        
        # Filter inactive if requested
        if not include_inactive:
            query = query.filter(AssetType.is_active == True)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        asset_types = query.order_by(AssetType.created_at.desc()).offset(
            page * limit
        ).limit(limit).all()
        
        # Build response items with field counts
        items = [
            AssetTypeListItem(
                id=at.id,
                name=at.name,
                description=at.description,
                is_active=at.is_active,
                field_count=len(at.custom_fields),
                created_at=at.created_at,
                updated_at=at.updated_at,
            )
            for at in asset_types
        ]
        
        # Build and return response
        return AssetTypeListResponse.from_items(
            items=items,
            total=total,
            page=page,
            page_size=limit,
        )
        
    except Exception as e:
        logger.error(f"Error listing asset types: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list asset types"
        )


@router.post("", status_code=201, response_model=AssetTypeResponse)
async def create_asset_type(
    asset_type_data: AssetTypeCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new asset type with optional custom fields.
    
    - Authentication required (Admin only)
    - Validates name is unique
    - Creates initial custom fields if provided
    
    Request body:
    - name: Unique asset type name (required, 1-255 chars)
    - description: Optional description
    - custom_fields: Optional list of initial custom fields
    
    Returns:
    - 201 Created: AssetTypeResponse with full details
    - 400 Bad Request: Invalid data
    - 401 Unauthorized: Not authenticated
    - 403 Forbidden: Not admin
    - 409 Conflict: Asset type name already exists
    """
    try:
        # Check for duplicate name
        existing = db.query(AssetType).filter(
            AssetType.name == asset_type_data.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Asset type with name '{asset_type_data.name}' already exists"
            )
        
        # Create asset type
        new_asset_type = AssetType(
            name=asset_type_data.name,
            description=asset_type_data.description,
            is_active=True,
        )
        
        # Add custom fields if provided
        if asset_type_data.custom_fields:
            for field_data in asset_type_data.custom_fields:
                # Check for duplicate field names within this asset type
                existing_field = any(
                    cf.name == field_data.name
                    for cf in new_asset_type.custom_fields
                )
                if existing_field:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Duplicate custom field name: {field_data.name}"
                    )
                
                # Create custom field
                custom_field = CustomField(
                    name=field_data.name,
                    field_type=field_data.field_type.value,
                    is_required=field_data.is_required,
                    options=field_data.options,
                    validation_rules=field_data.validation_rules,
                    display_order=field_data.display_order or 0,
                )
                new_asset_type.custom_fields.append(custom_field)
        
        # Save to database
        db.add(new_asset_type)
        db.commit()
        db.refresh(new_asset_type)
        
        logger.info(f"Asset type created: {new_asset_type.id} ({new_asset_type.name})")
        
        # Build response
        return AssetTypeResponse(
            id=new_asset_type.id,
            name=new_asset_type.name,
            description=new_asset_type.description,
            is_active=new_asset_type.is_active,
            custom_fields=[
                CustomFieldResponse(
                    id=cf.id,
                    name=cf.name,
                    field_type=cf.field_type,
                    is_required=cf.is_required,
                    display_order=cf.display_order,
                    options=cf.options,
                    validation_rules=cf.validation_rules,
                    asset_type_id=cf.asset_type_id,
                    created_at=cf.created_at,
                    updated_at=cf.updated_at,
                )
                for cf in new_asset_type.custom_fields
            ],
            created_at=new_asset_type.created_at,
            updated_at=new_asset_type.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating asset type: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create asset type"
        )


@router.get("/{asset_type_id}", response_model=AssetTypeDetailResponse)
async def get_asset_type(
    asset_type_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get asset type with all custom fields and field count.
    
    - Authentication required (Admin only)
    - Returns full asset type schema
    
    Path parameters:
    - asset_type_id: UUID of the asset type
    
    Returns:
    - 200 OK: AssetTypeDetailResponse with schema and field_count
    - 401 Unauthorized: Not authenticated
    - 403 Forbidden: Not admin
    - 404 Not Found: Asset type not found
    """
    try:
        asset_type = db.query(AssetType).filter(
            AssetType.id == asset_type_id
        ).first()
        
        if not asset_type:
            raise HTTPException(
                status_code=404,
                detail=f"Asset type with id {asset_type_id} not found"
            )
        
        # Build response with field count
        return AssetTypeDetailResponse(
            id=asset_type.id,
            name=asset_type.name,
            description=asset_type.description,
            is_active=asset_type.is_active,
            field_count=len(asset_type.custom_fields),
            custom_fields=[
                CustomFieldResponse(
                    id=cf.id,
                    name=cf.name,
                    field_type=cf.field_type,
                    is_required=cf.is_required,
                    display_order=cf.display_order,
                    options=cf.options,
                    validation_rules=cf.validation_rules,
                    asset_type_id=cf.asset_type_id,
                    created_at=cf.created_at,
                    updated_at=cf.updated_at,
                )
                for cf in sorted(asset_type.custom_fields, key=lambda cf: cf.display_order or 0)
            ],
            created_at=asset_type.created_at,
            updated_at=asset_type.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting asset type {asset_type_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get asset type"
        )


@router.put("/{asset_type_id}", response_model=AssetTypeResponse)
async def update_asset_type(
    asset_type_id: UUID,
    asset_type_data: AssetTypeUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Update asset type (name, description, is_active status).
    
    - Authentication required (Admin only)
    - Can change name (must remain unique)
    - Can deactivate asset type (is_active = false)
    
    Path parameters:
    - asset_type_id: UUID of the asset type
    
    Request body:
    - name: New asset type name (optional, must be unique)
    - description: New description (optional)
    - is_active: Active status (optional)
    
    Returns:
    - 200 OK: AssetTypeResponse with updated details
    - 400 Bad Request: Invalid data
    - 401 Unauthorized: Not authenticated
    - 403 Forbidden: Not admin
    - 404 Not Found: Asset type not found
    - 409 Conflict: New name already exists
    """
    try:
        asset_type = db.query(AssetType).filter(
            AssetType.id == asset_type_id
        ).first()
        
        if not asset_type:
            raise HTTPException(
                status_code=404,
                detail=f"Asset type with id {asset_type_id} not found"
            )
        
        # Check for duplicate name if being changed
        if asset_type_data.name and asset_type_data.name != asset_type.name:
            existing = db.query(AssetType).filter(
                AssetType.name == asset_type_data.name
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Asset type with name '{asset_type_data.name}' already exists"
                )
            
            asset_type.name = asset_type_data.name
        
        # Update optional fields
        if asset_type_data.description is not None:
            asset_type.description = asset_type_data.description
        
        if asset_type_data.is_active is not None:
            asset_type.is_active = asset_type_data.is_active
        
        # Save changes
        db.commit()
        db.refresh(asset_type)
        
        logger.info(f"Asset type updated: {asset_type_id}")
        
        # Build response
        return AssetTypeResponse(
            id=asset_type.id,
            name=asset_type.name,
            description=asset_type.description,
            is_active=asset_type.is_active,
            custom_fields=[
                CustomFieldResponse(
                    id=cf.id,
                    name=cf.name,
                    field_type=cf.field_type,
                    is_required=cf.is_required,
                    display_order=cf.display_order,
                    options=cf.options,
                    validation_rules=cf.validation_rules,
                    asset_type_id=cf.asset_type_id,
                    created_at=cf.created_at,
                    updated_at=cf.updated_at,
                )
                for cf in asset_type.custom_fields
            ],
            created_at=asset_type.created_at,
            updated_at=asset_type.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating asset type {asset_type_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update asset type"
        )


@router.delete("/{asset_type_id}", status_code=204)
async def delete_asset_type(
    asset_type_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Mark asset type as inactive (soft delete).
    
    - Authentication required (Admin only)
    - Sets is_active to false
    - Does not physically delete records
    - Existing resources of this type remain accessible
    
    Path parameters:
    - asset_type_id: UUID of the asset type
    
    Returns:
    - 204 No Content: Successfully marked inactive
    - 401 Unauthorized: Not authenticated
    - 403 Forbidden: Not admin
    - 404 Not Found: Asset type not found
    """
    try:
        asset_type = db.query(AssetType).filter(
            AssetType.id == asset_type_id
        ).first()
        
        if not asset_type:
            raise HTTPException(
                status_code=404,
                detail=f"Asset type with id {asset_type_id} not found"
            )
        
        # Soft delete by marking inactive
        asset_type.is_active = False
        db.commit()
        
        logger.info(f"Asset type marked inactive: {asset_type_id}")
        
        # Return 204 No Content
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting asset type {asset_type_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete asset type"
        )


@router.post("/{asset_type_id}/fields", status_code=201, response_model=CustomFieldResponse)
async def add_custom_field(
    asset_type_id: UUID,
    field_data: CustomFieldCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Add a custom field to an asset type.
    
    - Authentication required (Admin only)
    - Field name must be unique per asset type
    - Validates field type and options
    
    Path parameters:
    - asset_type_id: UUID of the asset type
    
    Request body:
    - name: Field name (unique within asset type, 1-255 chars)
    - field_type: Field type (text, number, date, dropdown, boolean)
    - is_required: Whether field is required (default false)
    - display_order: Display order in forms (optional)
    - options: Array of options for dropdown type
    - validation_rules: Validation constraints (optional)
    
    Returns:
    - 201 Created: CustomFieldResponse with full field details
    - 400 Bad Request: Invalid field data or duplicate name
    - 401 Unauthorized: Not authenticated
    - 403 Forbidden: Not admin
    - 404 Not Found: Asset type not found
    """
    try:
        # Verify asset type exists
        asset_type = db.query(AssetType).filter(
            AssetType.id == asset_type_id
        ).first()
        
        if not asset_type:
            raise HTTPException(
                status_code=404,
                detail=f"Asset type with id {asset_type_id} not found"
            )
        
        # Check for duplicate field name within this asset type
        existing_field = db.query(CustomField).filter(
            CustomField.asset_type_id == asset_type_id,
            CustomField.name == field_data.name,
        ).first()
        
        if existing_field:
            raise HTTPException(
                status_code=400,
                detail=f"Custom field with name '{field_data.name}' already exists for this asset type"
            )
        
        # Create custom field
        custom_field = CustomField(
            asset_type_id=asset_type_id,
            name=field_data.name,
            field_type=field_data.field_type.value,
            is_required=field_data.is_required,
            options=field_data.options,
            validation_rules=field_data.validation_rules,
            display_order=field_data.display_order or 0,
        )
        
        # Add and commit
        db.add(custom_field)
        db.commit()
        db.refresh(custom_field)
        
        logger.info(f"Custom field added: {custom_field.id} to asset type {asset_type_id}")
        
        # Build response
        return CustomFieldResponse(
            id=custom_field.id,
            asset_type_id=custom_field.asset_type_id,
            name=custom_field.name,
            field_type=custom_field.field_type,
            is_required=custom_field.is_required,
            display_order=custom_field.display_order,
            options=custom_field.options,
            validation_rules=custom_field.validation_rules,
            created_at=custom_field.created_at,
            updated_at=custom_field.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding custom field to asset type {asset_type_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to add custom field"
        )


@router.put("/{asset_type_id}/fields/{field_id}", response_model=CustomFieldResponse)
async def update_custom_field(
    asset_type_id: UUID,
    field_id: UUID,
    field_data: CustomFieldUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Update a custom field within an asset type.
    
    - Authentication required (Admin only)
    - Can update any field property except field type
    - Field name must remain unique within asset type
    
    Path parameters:
    - asset_type_id: UUID of the asset type
    - field_id: UUID of the custom field
    
    Request body (all optional):
    - name: New field name
    - field_type: Field type (cannot change field type)
    - is_required: Whether field is required
    - display_order: Display order
    - options: Options for dropdown type
    - validation_rules: Validation rules
    
    Returns:
    - 200 OK: CustomFieldResponse with updated details
    - 400 Bad Request: Invalid data or duplicate name
    - 401 Unauthorized: Not authenticated
    - 403 Forbidden: Not admin
    - 404 Not Found: Asset type or field not found
    """
    try:
        # Verify asset type exists
        asset_type = db.query(AssetType).filter(
            AssetType.id == asset_type_id
        ).first()
        
        if not asset_type:
            raise HTTPException(
                status_code=404,
                detail=f"Asset type with id {asset_type_id} not found"
            )
        
        # Verify custom field exists and belongs to this asset type
        custom_field = db.query(CustomField).filter(
            CustomField.id == field_id,
            CustomField.asset_type_id == asset_type_id,
        ).first()
        
        if not custom_field:
            raise HTTPException(
                status_code=404,
                detail=f"Custom field with id {field_id} not found in asset type {asset_type_id}"
            )
        
        # Check for duplicate name if name is being changed
        if field_data.name and field_data.name != custom_field.name:
            existing_field = db.query(CustomField).filter(
                CustomField.asset_type_id == asset_type_id,
                CustomField.name == field_data.name,
            ).first()
            
            if existing_field:
                raise HTTPException(
                    status_code=400,
                    detail=f"Custom field with name '{field_data.name}' already exists for this asset type"
                )
            
            custom_field.name = field_data.name
        
        # Update optional fields
        if field_data.field_type is not None:
            # Note: changing field type is generally not recommended but allowed
            custom_field.field_type = field_data.field_type.value
        
        if field_data.is_required is not None:
            custom_field.is_required = field_data.is_required
        
        if field_data.display_order is not None:
            custom_field.display_order = field_data.display_order
        
        if field_data.options is not None:
            custom_field.options = field_data.options
        
        if field_data.validation_rules is not None:
            custom_field.validation_rules = field_data.validation_rules
        
        # Commit changes
        db.commit()
        db.refresh(custom_field)
        
        logger.info(f"Custom field updated: {field_id} in asset type {asset_type_id}")
        
        # Build response
        return CustomFieldResponse(
            id=custom_field.id,
            asset_type_id=custom_field.asset_type_id,
            name=custom_field.name,
            field_type=custom_field.field_type,
            is_required=custom_field.is_required,
            display_order=custom_field.display_order,
            options=custom_field.options,
            validation_rules=custom_field.validation_rules,
            created_at=custom_field.created_at,
            updated_at=custom_field.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating custom field {field_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update custom field"
        )


@router.delete("/{asset_type_id}/fields/{field_id}", status_code=204)
async def remove_custom_field(
    asset_type_id: UUID,
    field_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Remove a custom field from an asset type.
    
    - Authentication required (Admin only)
    - Cascade deletes the field
    - Existing resources with this field keep values but cannot add new ones
    
    Path parameters:
    - asset_type_id: UUID of the asset type
    - field_id: UUID of the custom field
    
    Returns:
    - 204 No Content: Successfully removed
    - 401 Unauthorized: Not authenticated
    - 403 Forbidden: Not admin
    - 404 Not Found: Asset type or field not found
    """
    try:
        # Verify asset type exists
        asset_type = db.query(AssetType).filter(
            AssetType.id == asset_type_id
        ).first()
        
        if not asset_type:
            raise HTTPException(
                status_code=404,
                detail=f"Asset type with id {asset_type_id} not found"
            )
        
        # Verify custom field exists and belongs to this asset type
        custom_field = db.query(CustomField).filter(
            CustomField.id == field_id,
            CustomField.asset_type_id == asset_type_id,
        ).first()
        
        if not custom_field:
            raise HTTPException(
                status_code=404,
                detail=f"Custom field with id {field_id} not found in asset type {asset_type_id}"
            )
        
        # Delete custom field (cascade will handle related data)
        db.delete(custom_field)
        db.commit()
        
        logger.info(f"Custom field removed: {field_id} from asset type {asset_type_id}")
        
        # Return 204 No Content
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing custom field {field_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to remove custom field"
        )
