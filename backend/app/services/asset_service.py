"""Service layer for asset operations"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.models import (
    Asset, AssetFieldValue, ResourceField, Project, ResourceType,
    Alert, AlertType, AlertSeverity, AlertStatus
)
from app.schemas.asset import AssetCreateSchema, AssetUpdateSchema


class AssetService:
    """Service for managing assets"""

    @staticmethod
    def create_asset(db: Session, asset_data: AssetCreateSchema, created_by: UUID) -> Asset:
        """Create a new asset"""
        asset = Asset(
            project_id=asset_data.project_id,
            resource_type_id=asset_data.resource_type_id,
            asset_code=asset_data.asset_code,
            asset_name=asset_data.asset_name,
            manufacturer=asset_data.manufacturer,
            model=asset_data.model,
            serial_number=asset_data.serial_number,
            service_tag=asset_data.service_tag,
            vendor=asset_data.vendor,
            location=asset_data.location,
            room_no=asset_data.room_no,
            custodian_id=asset_data.custodian_id,
            purchase_date=asset_data.purchase_date,
            installation_date=asset_data.installation_date,
            warranty_start=asset_data.warranty_start,
            warranty_end=asset_data.warranty_end,
            cost=asset_data.cost,
            status=asset_data.status,
            audit_status=asset_data.audit_status,
            remarks=asset_data.remarks,
            created_by=created_by,
        )

        db.add(asset)
        db.flush()

        # Add field values
        if asset_data.field_values:
            for field_name, value in asset_data.field_values.items():
                AssetService.set_field_value(db, asset, field_name, value)

        db.commit()
        db.refresh(asset)
        return asset

    @staticmethod
    def get_asset(db: Session, asset_id: UUID) -> Optional[Asset]:
        """Get asset by ID"""
        return db.query(Asset).filter(
            and_(Asset.id == asset_id, Asset.deleted_at == None)
        ).first()

    @staticmethod
    def get_project_assets(db: Session, project_id: UUID, active_only: bool = True) -> List[Asset]:
        """Get all assets in a project"""
        query = db.query(Asset).filter(
            and_(Asset.project_id == project_id, Asset.deleted_at == None)
        )
        if active_only:
            query = query.filter(Asset.status == "Active")
        return query.order_by(desc(Asset.created_at)).all()

    @staticmethod
    def get_assets_by_resource_type(
        db: Session,
        project_id: UUID,
        resource_type_id: UUID,
        active_only: bool = True
    ) -> List[Asset]:
        """Get assets of specific resource type"""
        query = db.query(Asset).filter(
            and_(
                Asset.project_id == project_id,
                Asset.resource_type_id == resource_type_id,
                Asset.deleted_at == None
            )
        )
        if active_only:
            query = query.filter(Asset.status == "Active")
        return query.order_by(desc(Asset.created_at)).all()

    @staticmethod
    def update_asset(db: Session, asset_id: UUID, asset_data: AssetUpdateSchema) -> Optional[Asset]:
        """Update asset"""
        asset = db.query(Asset).filter(
            and_(Asset.id == asset_id, Asset.deleted_at == None)
        ).first()
        if not asset:
            return None

        # Update basic fields
        update_data = asset_data.dict(exclude_unset=True, exclude={'field_values'})
        for key, value in update_data.items():
            if value is not None:
                setattr(asset, key, value)

        # Update field values
        if asset_data.field_values:
            for field_name, value in asset_data.field_values.items():
                AssetService.set_field_value(db, asset, field_name, value)

        asset.updated_at = datetime.utcnow()
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    @staticmethod
    def delete_asset(db: Session, asset_id: UUID) -> bool:
        """Soft delete asset"""
        asset = db.query(Asset).filter(
            and_(Asset.id == asset_id, Asset.deleted_at == None)
        ).first()
        if not asset:
            return False

        asset.deleted_at = datetime.utcnow()
        db.add(asset)
        db.commit()
        return True

    @staticmethod
    def set_field_value(db: Session, asset: Asset, field_name: str, value: Any) -> Optional[AssetFieldValue]:
        """Set dynamic field value for asset"""
        # Find field definition
        field_def = db.query(ResourceField).filter(
            and_(
                ResourceField.resource_type_id == asset.resource_type_id,
                ResourceField.field_name == field_name
            )
        ).first()

        if not field_def:
            raise ValueError(f"Field '{field_name}' not found for resource type")

        # Validate value
        is_valid, error_msg = field_def.validate_value(value)
        if not is_valid:
            raise ValueError(f"Invalid value for field '{field_name}': {error_msg}")

        # Find or create field value
        field_value = db.query(AssetFieldValue).filter(
            and_(
                AssetFieldValue.asset_id == asset.id,
                AssetFieldValue.resource_field_id == field_def.id
            )
        ).first()

        if not field_value:
            field_value = AssetFieldValue(
                asset_id=asset.id,
                resource_field_id=field_def.id
            )
            db.add(field_value)
            db.flush()

        field_value.set_typed_value(value, field_def.data_type)
        db.add(field_value)
        return field_value

    @staticmethod
    def get_field_value(db: Session, asset_id: UUID, field_name: str) -> Optional[Any]:
        """Get dynamic field value for asset"""
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return None

        field_def = db.query(ResourceField).filter(
            and_(
                ResourceField.resource_type_id == asset.resource_type_id,
                ResourceField.field_name == field_name
            )
        ).first()

        if not field_def:
            return None

        field_value = db.query(AssetFieldValue).filter(
            and_(
                AssetFieldValue.asset_id == asset_id,
                AssetFieldValue.resource_field_id == field_def.id
            )
        ).first()

        return field_value.get_typed_value() if field_value else None

    @staticmethod
    def get_all_field_values(db: Session, asset_id: UUID) -> Dict[str, Any]:
        """Get all dynamic field values for asset"""
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return {}

        result = {}
        for field_value in asset.field_values:
            result[field_value.resource_field.field_name] = field_value.get_typed_value()
        return result

    @staticmethod
    def get_warranty_expiring_assets(db: Session, project_id: UUID, days: int = 90) -> List[Asset]:
        """Get assets with warranty expiring within specified days"""
        from datetime import timedelta
        threshold_date = datetime.now().date() + timedelta(days=days)

        return db.query(Asset).filter(
            and_(
                Asset.project_id == project_id,
                Asset.warranty_end <= threshold_date,
                Asset.warranty_end > datetime.now().date(),
                Asset.status == "Active",
                Asset.deleted_at == None
            )
        ).all()

    @staticmethod
    def get_assets_requiring_audit(db: Session, project_id: UUID) -> List[Asset]:
        """Get assets that require audit"""
        return db.query(Asset).filter(
            and_(
                Asset.project_id == project_id,
                Asset.audit_status.in_(["Pending", "Overdue"]),
                Asset.status == "Active",
                Asset.deleted_at == None
            )
        ).all()

    @staticmethod
    def calculate_project_asset_value(db: Session, project_id: UUID) -> Decimal:
        """Calculate total value of all assets in project"""
        result = db.query(
            func.coalesce(func.sum(Asset.cost), 0).label('total')
        ).filter(
            and_(
                Asset.project_id == project_id,
                Asset.status == "Active",
                Asset.deleted_at == None
            )
        ).first()

        return Decimal(str(result.total)) if result else Decimal("0")

    @staticmethod
    def get_asset_summary_by_type(db: Session, project_id: UUID) -> List[Dict[str, Any]]:
        """Get summary of assets grouped by resource type"""
        from sqlalchemy import func

        result = db.query(
            ResourceType.display_name,
            func.count(Asset.id).label('count'),
            func.sum(Asset.cost).label('total_cost')
        ).join(Asset, Asset.resource_type_id == ResourceType.id).filter(
            and_(
                Asset.project_id == project_id,
                Asset.status == "Active",
                Asset.deleted_at == None
            )
        ).group_by(ResourceType.id, ResourceType.display_name).all()

        return [
            {
                "resource_type": r[0],
                "count": r[1],
                "total_cost": Decimal(str(r[2])) if r[2] else Decimal("0")
            }
            for r in result
        ]


from sqlalchemy import func