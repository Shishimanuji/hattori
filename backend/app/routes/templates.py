"""API routes for template management"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.models import Template, User
from app.utils.dependencies import get_current_user
from app.schemas.template import TemplateSchema, TemplateCreateSchema, TemplateUpdateSchema
from app.services.template_service import TemplateService

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.post("", response_model=TemplateSchema, status_code=status.HTTP_201_CREATED)
def create_template(
    template_data: TemplateCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new template (Admin only)"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create templates"
        )
    
    # Check if template name already exists
    existing = TemplateService.get_template_by_name(db, template_data.template_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template name already exists"
        )
    
    template = TemplateService.create_template(db, template_data)
    return template


@router.get("/{template_id}", response_model=TemplateSchema)
def get_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get template by ID"""
    template = TemplateService.get_template(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template


@router.get("", response_model=List[TemplateSchema])
def list_templates(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all templates"""
    templates = TemplateService.get_all_templates(db, active_only=active_only)
    return templates


@router.put("/{template_id}", response_model=TemplateSchema)
def update_template(
    template_id: UUID,
    template_data: TemplateUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update template (Admin only)"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update templates"
        )
    
    template = TemplateService.update_template(db, template_id, template_data)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete template (Admin only)"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete templates"
        )
    
    success = TemplateService.delete_template(db, template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )