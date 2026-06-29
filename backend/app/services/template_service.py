"""Service layer for template operations"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from typing import List, Optional
from app.models import Template, TemplateResourceType, SheetMapping, ResourceType
from app.schemas.template import TemplateCreateSchema, TemplateUpdateSchema


class TemplateService:
    """Service for managing templates"""

    @staticmethod
    def create_template(db: Session, template_data: TemplateCreateSchema) -> Template:
        """Create a new template"""
        template = Template(
            template_name=template_data.template_name,
            description=template_data.description,
            version=template_data.version,
            client_type=template_data.client_type,
            is_default=template_data.is_default,
            template_config=template_data.template_config,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def get_template(db: Session, template_id: UUID) -> Optional[Template]:
        """Get template by ID"""
        return db.query(Template).filter(Template.id == template_id).first()

    @staticmethod
    def get_template_by_name(db: Session, template_name: str) -> Optional[Template]:
        """Get template by name"""
        return db.query(Template).filter(Template.template_name == template_name).first()

    @staticmethod
    def get_all_templates(db: Session, active_only: bool = True) -> List[Template]:
        """Get all templates"""
        query = db.query(Template)
        if active_only:
            query = query.filter(Template.is_active == True)
        return query.order_by(Template.created_at.desc()).all()

    @staticmethod
    def update_template(db: Session, template_id: UUID, template_data: TemplateUpdateSchema) -> Optional[Template]:
        """Update template"""
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            return None

        update_data = template_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(template, key, value)

        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_template(db: Session, template_id: UUID) -> bool:
        """Soft delete template by marking as inactive"""
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            return False

        template.is_active = False
        db.add(template)
        db.commit()
        return True

    @staticmethod
    def get_template_resource_types(db: Session, template_id: UUID) -> List[TemplateResourceType]:
        """Get resource types for a template"""
        return db.query(TemplateResourceType).filter(
            TemplateResourceType.template_id == template_id
        ).order_by(TemplateResourceType.display_order).all()

    @staticmethod
    def add_resource_type_to_template(
        db: Session,
        template_id: UUID,
        resource_type_id: UUID,
        display_order: int,
        is_required: bool = False
    ) -> TemplateResourceType:
        """Add resource type to template"""
        trt = TemplateResourceType(
            template_id=template_id,
            resource_type_id=resource_type_id,
            display_order=display_order,
            is_required=is_required,
        )
        db.add(trt)
        db.commit()
        db.refresh(trt)
        return trt

    @staticmethod
    def get_sheet_mappings(db: Session, template_id: UUID) -> List[SheetMapping]:
        """Get sheet mappings for a template"""
        return db.query(SheetMapping).filter(
            SheetMapping.template_id == template_id
        ).order_by(SheetMapping.display_order).all()

    @staticmethod
    def get_sheet_mapping(db: Session, template_id: UUID, sheet_name: str) -> Optional[SheetMapping]:
        """Get specific sheet mapping"""
        return db.query(SheetMapping).filter(
            and_(
                SheetMapping.template_id == template_id,
                SheetMapping.sheet_name == sheet_name
            )
        ).first()

    @staticmethod
    def add_sheet_mapping(
        db: Session,
        template_id: UUID,
        sheet_name: str,
        resource_type_id: UUID,
        display_order: int,
        is_summary_sheet: bool = False
    ) -> SheetMapping:
        """Add sheet mapping to template"""
        mapping = SheetMapping(
            template_id=template_id,
            sheet_name=sheet_name,
            resource_type_id=resource_type_id,
            display_order=display_order,
            is_summary_sheet=is_summary_sheet,
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)
        return mapping

    @staticmethod
    def identify_template_by_sheets(db: Session, sheet_names: List[str]) -> Optional[Template]:
        """Identify template based on sheet names"""
        # Find templates that have mappings for these sheets
        from sqlalchemy import func

        # Count matching sheets per template
        matching_templates = db.query(
            SheetMapping.template_id,
            func.count(SheetMapping.id).label('matching_sheets')
        ).filter(
            SheetMapping.sheet_name.in_(sheet_names)
        ).group_by(SheetMapping.template_id).all()

        if not matching_templates:
            return None

        # Sort by number of matches (descending) and get best match
        best_match_template_id = max(matching_templates, key=lambda x: x[1])[0]

        return db.query(Template).filter(Template.id == best_match_template_id).first()