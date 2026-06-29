"""API routes for comprehensive dashboard tabs"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import get_db
from app.models import User
from app.utils.dependencies import get_current_user
from app.services.dashboard_service import DashboardService
from app.services.asset_service import AssetService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard-tabs"])


# ============================================================================
# 1. DASHBOARD TAB - Overview & Key Metrics
# ============================================================================
@router.get("/overview")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard overview with key metrics"""
    try:
        overview = {
            "total_projects": db.query(func.count()).select_from(
                db.query(func.count().over()).from_statement(
                    "SELECT * FROM projects WHERE deleted_at IS NULL"
                )
            ).scalar() or 0,
            "active_assets": 0,
            "pending_audits": 0,
            "warranty_expiring": 0,
            "critical_alerts": 0,
            "total_value": Decimal("0"),
            "completion_rate": 0.0,
        }
        
        from app.models import Asset, Alert, Project, ProjectSummary
        
        # Get metrics
        overview["total_projects"] = db.query(func.count(Project.id)).filter(
            Project.deleted_at == None
        ).scalar() or 0
        
        overview["active_assets"] = db.query(func.count(Asset.id)).filter(
            Asset.status == "Active",
            Asset.deleted_at == None
        ).scalar() or 0
        
        overview["pending_audits"] = db.query(func.count(Asset.id)).filter(
            Asset.audit_status.in_(["Pending", "Overdue"]),
            Asset.deleted_at == None
        ).scalar() or 0
        
        overview["warranty_expiring"] = db.query(func.count(Asset.id)).filter(
            Asset.warranty_end <= datetime.now().date() + timedelta(days=90),
            Asset.warranty_end > datetime.now().date(),
            Asset.deleted_at == None
        ).scalar() or 0
        
        overview["critical_alerts"] = db.query(func.count(Alert.id)).filter(
            Alert.severity == "Critical",
            Alert.status == "Active"
        ).scalar() or 0
        
        total_value = db.query(func.coalesce(func.sum(Asset.cost), 0)).filter(
            Asset.status == "Active",
            Asset.deleted_at == None
        ).scalar()
        overview["total_value"] = Decimal(str(total_value)) if total_value else Decimal("0")
        
        completions = db.query(func.avg(ProjectSummary.completion_percentage)).filter(
            ProjectSummary.completion_percentage > 0
        ).scalar()
        overview["completion_rate"] = float(completions) if completions else 0.0
        
        return overview
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard overview: {str(e)}"
        )


# ============================================================================
# 2. PROJECTS TAB
# ============================================================================
@router.get("/projects/summary")
def get_projects_summary(
    status: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get projects summary"""
    from app.models import Project
    
    query = db.query(Project).filter(Project.deleted_at == None)
    
    if status:
        query = query.filter(Project.status == status)
    
    projects = query.order_by(Project.created_at.desc()).limit(limit).all()
    
    return [{
        "id": str(p.id),
        "project_code": p.project_code,
        "name": p.name,
        "status": p.status,
        "client": p.client,
        "location": p.location,
        "total_assets": len([a for a in p.assets if a.deleted_at is None]),
        "completion": p.project_summary.completion_percentage if p.project_summary else 0,
        "created_at": p.created_at
    } for p in projects]


# ============================================================================
# 3. ASSETS TAB
# ============================================================================
@router.get("/assets/summary")
def get_assets_summary(
    resource_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assets summary with filtering"""
    from app.models import Asset, ResourceType
    
    query = db.query(Asset).filter(Asset.deleted_at == None)
    
    if status:
        query = query.filter(Asset.status == status)
    
    if resource_type:
        query = query.join(ResourceType).filter(ResourceType.name == resource_type)
    
    assets = query.order_by(Asset.created_at.desc()).limit(limit).all()
    
    return [{
        "id": str(a.id),
        "asset_code": a.asset_code,
        "name": a.asset_name,
        "type": a.resource_type.display_name if a.resource_type else "Unknown",
        "status": a.status,
        "cost": float(a.cost) if a.cost else 0,
        "warranty_end": a.warranty_end,
        "audit_status": a.audit_status,
        "created_at": a.created_at
    } for a in assets]


@router.get("/assets/by-type")
def get_assets_by_type(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset distribution by resource type"""
    from app.models import Asset, ResourceType
    
    result = db.query(
        ResourceType.display_name,
        func.count(Asset.id).label("count"),
        func.sum(Asset.cost).label("total_cost")
    ).join(Asset, Asset.resource_type_id == ResourceType.id).filter(
        Asset.status == "Active",
        Asset.deleted_at == None
    ).group_by(ResourceType.id, ResourceType.display_name).all()
    
    return [{
        "type": r[0],
        "count": r[1],
        "total_value": float(r[2]) if r[2] else 0
    } for r in result]


# ============================================================================
# 4. RESOURCES TAB (for legacy resource management)
# ============================================================================
@router.get("/resources/summary")
def get_resources_summary(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get resources summary (legacy resources)"""
    from app.models import Resource
    
    resources = db.query(Resource).filter(
        Resource.deleted_at == None,
        Resource.status == "Active"
    ).order_by(Resource.created_at.desc()).limit(limit).all()
    
    return [{
        "id": str(r.id),
        "name": r.name,
        "type": r.asset_type.name if r.asset_type else "Unknown",
        "cost": float(r.cost),
        "status": r.status,
        "project": r.project.name if r.project else "Unknown"
    } for r in resources]


# ============================================================================
# 5. DOCUMENTS TAB
# ============================================================================
@router.get("/documents/summary")
def get_documents_summary(
    document_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get documents summary"""
    from app.models import Document
    
    query = db.query(Document)
    
    if document_type:
        query = query.filter(Document.document_type == document_type)
    
    documents = query.order_by(Document.uploaded_at.desc()).limit(limit).all()
    
    return [{
        "id": str(d.id),
        "file_name": d.file_name,
        "type": d.document_type,
        "size": d.file_size,
        "uploaded_by": d.uploader.full_name if d.uploader else "Unknown",
        "uploaded_at": d.uploaded_at,
        "project": d.project.name if d.project else "Unknown",
        "asset": d.asset.asset_name if d.asset else "Unknown"
    } for d in documents]


@router.get("/documents/by-type")
def get_documents_by_type(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document distribution by type"""
    from app.models import Document
    
    result = db.query(
        Document.document_type,
        func.count(Document.id).label("count"),
        func.sum(Document.file_size).label("total_size")
    ).group_by(Document.document_type).all()
    
    return [{
        "type": r[0],
        "count": r[1],
        "total_size": r[2] or 0
    } for r in result]


# ============================================================================
# 6. REPORTS TAB
# ============================================================================
@router.get("/reports/list")
def get_reports_list(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available report templates"""
    from app.models import ReportTemplate
    
    reports = db.query(ReportTemplate).filter(
        (ReportTemplate.is_public == True) | 
        (ReportTemplate.created_by == current_user.id)
    ).order_by(ReportTemplate.created_at.desc()).limit(limit).all()
    
    return [{
        "id": str(r.id),
        "name": r.report_name,
        "description": r.description,
        "is_public": r.is_public,
        "created_by": r.creator.full_name if r.creator else "Unknown",
        "created_at": r.created_at
    } for r in reports]


@router.get("/reports/asset-inventory")
def get_asset_inventory_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset inventory report"""
    from app.models import Asset, ResourceType, Project
    
    result = db.query(
        Project.name.label("project"),
        ResourceType.display_name.label("type"),
        func.count(Asset.id).label("quantity"),
        func.sum(Asset.cost).label("total_value")
    ).join(Asset, Asset.project_id == Project.id).join(
        ResourceType, Asset.resource_type_id == ResourceType.id
    ).filter(
        Asset.status == "Active",
        Asset.deleted_at == None
    ).group_by(Project.id, Project.name, ResourceType.id, ResourceType.display_name).all()
    
    return [{
        "project": r[0],
        "asset_type": r[1],
        "quantity": r[2],
        "total_value": float(r[3]) if r[3] else 0
    } for r in result]


# ============================================================================
# 7. ALERTS TAB
# ============================================================================
@router.get("/alerts/summary")
def get_alerts_summary(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query("Active"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get alerts summary"""
    from app.models import Alert
    
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    if status:
        query = query.filter(Alert.status == status)
    
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    
    return [{
        "id": str(a.id),
        "title": a.title,
        "type": a.alert_type,
        "severity": a.severity,
        "status": a.status,
        "due_date": a.due_date,
        "created_at": a.created_at,
        "project": a.project.name if a.project else "Unknown",
        "asset": a.asset.asset_name if a.asset else "Unknown"
    } for a in alerts]


@router.get("/alerts/by-severity")
def get_alerts_by_severity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get alert distribution by severity"""
    from app.models import Alert
    
    result = db.query(
        Alert.severity,
        func.count(Alert.id).label("count")
    ).filter(Alert.status == "Active").group_by(Alert.severity).all()
    
    return [{
        "severity": r[0],
        "count": r[1]
    } for r in result]


# ============================================================================
# 8. ADMINISTRATION TAB
# ============================================================================
@router.get("/admin/system-stats")
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system statistics (Admin only)"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    from app.models import User, Project, Asset, AuditLog
    
    stats = {
        "total_users": db.query(func.count(User.id)).filter(User.deleted_at == None).scalar() or 0,
        "active_users": db.query(func.count(User.id)).filter(
            User.status == "Active",
            User.deleted_at == None
        ).scalar() or 0,
        "total_projects": db.query(func.count(Project.id)).filter(Project.deleted_at == None).scalar() or 0,
        "total_assets": db.query(func.count(Asset.id)).filter(Asset.deleted_at == None).scalar() or 0,
        "audit_logs_count": db.query(func.count(AuditLog.id)).scalar() or 0,
        "database_size": "N/A"  # Would require database-specific query
    }
    return stats


@router.get("/admin/audit-log")
def get_audit_log(
    action: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit log (Admin only)"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    from app.models import AuditLog
    
    query = db.query(AuditLog)
    
    if action:
        query = query.filter(AuditLog.operation == action)
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    return [{
        "id": str(l.id),
        "user": l.user.full_name if l.user else "System",
        "operation": l.operation,
        "entity": l.entity_type,
        "status": l.status,
        "timestamp": l.created_at,
        "error": l.error_message
    } for l in logs]


@router.get("/admin/users")
def get_users_management(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get users for administration (Admin only)"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    users = db.query(User).filter(User.deleted_at == None).limit(limit).all()
    
    return [{
        "id": str(u.id),
        "username": u.username,
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role.role_name if u.role else "Unknown",
        "status": u.status,
        "department": u.department,
        "last_login": u.last_login,
        "created_at": u.created_at
    } for u in users]


@router.get("/admin/system-health")
def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system health status (Admin only)"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Test database connection
        db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow(),
            "last_check": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }