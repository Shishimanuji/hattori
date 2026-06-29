"""Service layer for resource type operations"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.models import ResourceType, ResourceField
from app.schemas.asset import ResourceFieldSchema


class ResourceTypeService:
    """Service for managing resource types"""

    @staticmethod
    def create_resource_type(
        db: Session,
        name: str,
        display_name: str,
        icon: Optional[str] = None,
        display_order: int = 0
    ) -> ResourceType:
        """Create a new resource type"""
        resource_type = ResourceType(
            name=name,
            display_name=display_name,
            icon=icon,
            display_order=display_order,
            is_active=True
        )
        db.add(resource_type)
        db.commit()
        db.refresh(resource_type)
        return resource_type

    @staticmethod
    def get_resource_type(db: Session, resource_type_id: UUID) -> Optional[ResourceType]:
        """Get resource type by ID"""
        return db.query(ResourceType).filter(ResourceType.id == resource_type_id).first()

    @staticmethod
    def get_resource_type_by_name(db: Session, name: str) -> Optional[ResourceType]:
        """Get resource type by name"""
        return db.query(ResourceType).filter(ResourceType.name == name).first()

    @staticmethod
    def get_all_resource_types(db: Session, active_only: bool = True) -> List[ResourceType]:
        """Get all resource types"""
        query = db.query(ResourceType)
        if active_only:
            query = query.filter(ResourceType.is_active == True)
        return query.order_by(ResourceType.display_order).all()

    @staticmethod
    def create_resource_field(
        db: Session,
        resource_type_id: UUID,
        field_name: str,
        display_name: str,
        data_type: str,
        display_order: int,
        is_required: bool = False,
        is_unique: bool = False,
        unit: Optional[str] = None,
        default_value: Optional[str] = None,
        validation_regex: Optional[str] = None,
        options: Optional[List[str]] = None
    ) -> ResourceField:
        """Create a new resource field"""
        field = ResourceField(
            resource_type_id=resource_type_id,
            field_name=field_name,
            display_name=display_name,
            data_type=data_type,
            display_order=display_order,
            is_required=is_required,
            is_unique=is_unique,
            unit=unit,
            default_value=default_value,
            validation_regex=validation_regex,
            options=options,
            is_visible=True
        )
        db.add(field)
        db.commit()
        db.refresh(field)
        return field

    @staticmethod
    def get_resource_field(db: Session, field_id: UUID) -> Optional[ResourceField]:
        """Get resource field by ID"""
        return db.query(ResourceField).filter(ResourceField.id == field_id).first()

    @staticmethod
    def get_resource_fields(
        db: Session,
        resource_type_id: UUID,
        visible_only: bool = True
    ) -> List[ResourceField]:
        """Get all fields for a resource type"""
        query = db.query(ResourceField).filter(
            ResourceField.resource_type_id == resource_type_id
        )
        if visible_only:
            query = query.filter(ResourceField.is_visible == True)
        return query.order_by(ResourceField.display_order).all()

    @staticmethod
    def update_resource_field(
        db: Session,
        field_id: UUID,
        **kwargs
    ) -> Optional[ResourceField]:
        """Update resource field"""
        field = db.query(ResourceField).filter(ResourceField.id == field_id).first()
        if not field:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(field, key):
                setattr(field, key, value)

        db.add(field)
        db.commit()
        db.refresh(field)
        return field

    @staticmethod
    def delete_resource_field(db: Session, field_id: UUID) -> bool:
        """Delete resource field by marking as invisible"""
        field = db.query(ResourceField).filter(ResourceField.id == field_id).first()
        if not field:
            return False

        field.is_visible = False
        db.add(field)
        db.commit()
        return True

    @staticmethod
    def add_field_to_end(
        db: Session,
        resource_type_id: UUID,
        field_name: str,
        display_name: str,
        data_type: str,
        **kwargs
    ) -> ResourceField:
        """Add field to resource type (automatically gets next display order)"""
        # Get current max display order
        max_order = db.query(
            func.max(ResourceField.display_order)
        ).filter(
            ResourceField.resource_type_id == resource_type_id
        ).scalar() or 0

        return ResourceTypeService.create_resource_field(
            db,
            resource_type_id,
            field_name,
            display_name,
            data_type,
            display_order=max_order + 1,
            **kwargs
        )

    @staticmethod
    def reorder_fields(db: Session, resource_type_id: UUID, field_order: List[UUID]) -> bool:
        """Reorder fields for a resource type"""
        for order, field_id in enumerate(field_order, start=1):
            field = db.query(ResourceField).filter(
                and_(
                    ResourceField.id == field_id,
                    ResourceField.resource_type_id == resource_type_id
                )
            ).first()
            if not field:
                return False
            field.display_order = order

        db.commit()
        return True


from sqlalchemy import and_, func