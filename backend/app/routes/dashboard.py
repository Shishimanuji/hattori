"""Dashboard API routes for metrics and visualizations"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.asset import Asset
from app.models.document import Document
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.report_template import ReportTemplate
from app.utils.dependencies import get_current_user
from app.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Simple in-memory cache (in production, use Redis)
_metrics_cache = {}
_cache_ttl = 30  # 30 seconds


def _get_cached_metrics(cache_key: str) -> dict | None:
    """Get metrics from cache if not expired"""
    if cache_key in _metrics_cache:
        data, timestamp = _metrics_cache[cache_key]
        if datetime.utcnow() - timestamp < timedelta(seconds=_cache_ttl):
            return data
        else:
            del _metrics_cache[cache_key]
    return None


def _set_cached_metrics(cache_key: str, data: dict):
    """Store metrics in cache"""
    _metrics_cache[cache_key] = (data, datetime.utcnow())


@router.get("/metrics", response_model=dict)
async def get_dashboard_metrics(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all dashboard metrics.
    
    Returns aggregated data for:
    - Project overview (counts by status, budget stats)
    - Resource distribution (by type and status)
    - Utilization trends (30-day data)
    - Budget status (with warnings and critical alerts)
    
    - Authentication required (any authenticated user)
    - Response cached for 30 seconds for performance
    - Should complete within 2 seconds
    
    Returns:
    - 200 OK: Dashboard metrics object
    - 401 Unauthorized: Not authenticated
    """
    try:
        # Try to get from cache
        cache_key = f"dashboard_metrics_{current_user.id}"
        cached_metrics = _get_cached_metrics(cache_key)
        if cached_metrics:
            logger.debug(f"Returning cached metrics for user {current_user.id}")
            return cached_metrics
        
        # Get fresh metrics
        metrics = DashboardService.get_dashboard_metrics(db, current_user)
        
        # Cache the result
        _set_cached_metrics(cache_key, metrics)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error retrieving dashboard metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/projects", response_model=dict)
async def get_project_overview(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get project overview with counts and budget statistics.
    
    Returns:
    - 200 OK: Project overview object
    - 401 Unauthorized: Not authenticated
    """
    try:
        projects = DashboardService.get_project_overview(db, current_user)
        return projects
        
    except Exception as e:
        logger.error(f"Error retrieving project overview: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/resources", response_model=dict)
async def get_resource_distribution(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get resource distribution by type and status.
    
    Returns:
    - 200 OK: Resource distribution object
    - 401 Unauthorized: Not authenticated
    """
    try:
        resources = DashboardService.get_resource_distribution(db, current_user)
        return resources
        
    except Exception as e:
        logger.error(f"Error retrieving resource distribution: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trends", response_model=dict)
async def get_utilization_trends(
    request: Request,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get utilization trends over time.
    
    Query parameters:
    - days: Number of days to look back (default 30)
    
    Returns:
    - 200 OK: Trend data object
    - 401 Unauthorized: Not authenticated
    """
    try:
        trends = DashboardService.get_utilization_trends(db, days=days)
        return trends
        
    except Exception as e:
        logger.error(f"Error retrieving trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/budget-status", response_model=dict)
async def get_budget_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get budget status across all projects with warnings.
    
    Returns projects organized by:
    - All projects (array)
    - Warnings (80-99% utilization)
    - Critical (100%+ utilization)
    
    Returns:
    - 200 OK: Budget status object
    - 401 Unauthorized: Not authenticated
    """
    try:
        budget = DashboardService.get_budget_status(db, current_user)
        return budget
        
    except Exception as e:
        logger.error(f"Error retrieving budget status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cache/clear")
async def clear_cache(
    current_user: User = Depends(get_current_user),
):
    """
    Clear dashboard cache for current user.
    
    Useful for forcing a refresh of metrics.
    
    Returns:
    - 200 OK: Cache cleared
    - 401 Unauthorized: Not authenticated
    """
    try:
        cache_key = f"dashboard_metrics_{current_user.id}"
        if cache_key in _metrics_cache:
            del _metrics_cache[cache_key]
        
        return {"status": "ok", "message": "Cache cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/infrastructure/kpis", response_model=dict)
async def get_infrastructure_kpis(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get infrastructure intelligence KPIs.
    
    Returns:
    - Total assets and distribution by type
    - Warranty analysis (expired, expiring soon, healthy)
    - Antivirus compliance status
    - Asset age distribution
    - Room-wise distribution
    - Infrastructure health score (0-100)
    - Capacity summary (CPU cores, RAM, Storage)
    - Compliance status
    - Critical alerts
    
    Returns:
    - 200 OK: Infrastructure KPIs object
    - 401 Unauthorized: Not authenticated
    """
    try:
        from app.services.infrastructure_service import InfrastructureService
        
        # Try to get from cache
        cache_key = f"infrastructure_kpis_{current_user.id}"
        cached_kpis = _get_cached_metrics(cache_key)
        if cached_kpis:
            logger.debug(f"Returning cached KPIs for user {current_user.id}")
            return cached_kpis
        
        # Get fresh KPIs
        service = InfrastructureService(db)
        kpis = service.get_infrastructure_kpis()
        kpis['timestamp'] = datetime.utcnow().isoformat()
        
        # Cache the result
        _set_cached_metrics(cache_key, kpis)
        
        return kpis
        
    except Exception as e:
        logger.error(f"Error retrieving infrastructure KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# 8-TAB DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/tab/dashboard", response_model=dict)
async def get_dashboard_tab(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get Dashboard tab data - Overview metrics and KPIs.
    
    Returns:
    - Key metrics (projects, assets, resources, alerts)
    - Budget overview
    - Recent activity
    - Health indicators
    """
    try:
        cache_key = f"dashboard_tab_{current_user.id}"
        cached = _get_cached_metrics(cache_key)
        if cached:
            return cached
        
        metrics = DashboardService.get_dashboard_metrics(db, current_user)
        _set_cached_metrics(cache_key, metrics)
        return metrics
        
    except Exception as e:
        logger.error(f"Error in dashboard tab: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tab/projects", response_model=dict)
async def get_projects_tab(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    status: str = Query(None),
    search: str = Query(None),
):
    """
    Get Projects tab - Project listing with filters.
    
    Query parameters:
    - status: Filter by project status (Active, Pending, Completed, On Hold)
    - search: Search by project name or code
    - limit: Number of results (default 50, max 100)
    - offset: Pagination offset (default 0)
    """
    try:
        from app.services.authorization_service import AuthorizationService
        
        query = db.query(Project).filter(Project.deleted_at.is_(None))
        query = AuthorizationService.filter_viewable_projects(current_user, query, db)
        
        # Apply filters
        if status:
            query = query.filter(Project.status == status)
        if search:
            query = query.filter(
                (Project.name.ilike(f"%{search}%")) |
                (Project.project_code.ilike(f"%{search}%"))
            )
        
        total = query.count()
        projects = query.offset(offset).limit(limit).all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "projects": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "project_code": p.project_code,
                    "status": p.status,
                    "budget": float(p.budget),
                    "allocated_budget": float(p.allocated_budget),
                    "remaining_budget": float(p.remaining_budget),
                    "utilization_percentage": p.utilization_percentage,
                    "client": p.client,
                    "vendor": p.vendor,
                    "location": p.location,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in projects
            ],
        }
        
    except Exception as e:
        logger.error(f"Error in projects tab: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tab/assets", response_model=dict)
async def get_assets_tab(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    status: str = Query(None),
    resource_type: str = Query(None),
    search: str = Query(None),
):
    """
    Get Assets tab - Asset listing with filters.
    
    Query parameters:
    - status: Filter by asset status (Active, Inactive, Disposed, Under Repair, Reserved)
    - resource_type: Filter by resource type ID
    - search: Search by asset name or serial number
    - limit: Number of results (default 50, max 100)
    - offset: Pagination offset (default 0)
    """
    try:
        from app.services.authorization_service import AuthorizationService
        
        query = db.query(Asset).filter(Asset.deleted_at.is_(None))
        query = AuthorizationService.filter_viewable_assets(current_user, query, db)
        
        # Apply filters
        if status:
            query = query.filter(Asset.status == status)
        if resource_type:
            query = query.filter(Asset.resource_type_id == resource_type)
        if search:
            query = query.filter(
                (Asset.asset_name.ilike(f"%{search}%")) |
                (Asset.serial_number.ilike(f"%{search}%")) |
                (Asset.asset_code.ilike(f"%{search}%"))
            )
        
        total = query.count()
        assets = query.offset(offset).limit(limit).all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "assets": [
                {
                    "id": str(a.id),
                    "asset_code": a.asset_code,
                    "asset_name": a.asset_name,
                    "manufacturer": a.manufacturer,
                    "model": a.model,
                    "serial_number": a.serial_number,
                    "status": a.status,
                    "audit_status": a.audit_status,
                    "cost": float(a.cost) if a.cost else 0,
                    "warranty_end": a.warranty_end.isoformat() if a.warranty_end else None,
                    "location": a.location,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in assets
            ],
        }
        
    except Exception as e:
        logger.error(f"Error in assets tab: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tab/resources", response_model=dict)
async def get_resources_tab(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    status: str = Query(None),
):
    """
    Get Resources tab - Legacy resource compatibility.
    
    Query parameters:
    - status: Filter by resource status (Active, Inactive)
    - limit: Number of results (default 50, max 100)
    - offset: Pagination offset (default 0)
    """
    try:
        from app.models.resource import Resource
        from app.services.authorization_service import AuthorizationService
        
        query = db.query(Resource).filter(Resource.deleted_at.is_(None))
        query = AuthorizationService.filter_viewable_resources(current_user, query, db)
        
        if status:
            query = query.filter(Resource.status == status)
        
        total = query.count()
        resources = query.offset(offset).limit(limit).all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "resources": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "cost": float(r.cost),
                    "status": r.status,
                    "allocation_date": r.allocation_date.isoformat() if r.allocation_date else None,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in resources
            ],
        }
        
    except Exception as e:
        logger.error(f"Error in resources tab: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tab/documents", response_model=dict)
async def get_documents_tab(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    doc_type: str = Query(None),
):
    """
    Get Documents tab - Document listing.
    
    Query parameters:
    - doc_type: Filter by document type (Invoice, Warranty, Configuration, Drawing, Manual, Certificate, Other)
    - limit: Number of results (default 50, max 100)
    - offset: Pagination offset (default 0)
    """
    try:
        query = db.query(Document)
        
        if doc_type:
            query = query.filter(Document.document_type == doc_type)
        
        total = query.count()
        documents = query.order_by(Document.uploaded_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "documents": [
                {
                    "id": str(d.id),
                    "file_name": d.file_name,
                    "document_type": d.document_type,
                    "file_size": d.file_size,
                    "mime_type": d.mime_type,
                    "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
                    "description": d.description,
                    "project_id": str(d.project_id) if d.project_id else None,
                    "asset_id": str(d.asset_id) if d.asset_id else None,
                }
                for d in documents
            ],
        }
        
    except Exception as e:
        logger.error(f"Error in documents tab: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tab/reports", response_model=dict)
async def get_reports_tab(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
):
    """
    Get Reports tab - Report templates listing.
    
    Query parameters:
    - limit: Number of results (default 50, max 100)
    - offset: Pagination offset (default 0)
    """
    try:
        query = db.query(ReportTemplate)
        
        # Filter public reports or user's own reports
        query = query.filter(
            (ReportTemplate.is_public == True) |
            (ReportTemplate.created_by == current_user.id)
        )
        
        total = query.count()
        templates = query.order_by(ReportTemplate.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "reports": [
                {
                    "id": str(t.id),
                    "report_name": t.report_name,
                    "description": t.description,
                    "is_public": t.is_public,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "filters": t.filters_json or {},
                    "columns": t.columns_config or {},
                }
                for t in templates
            ],
        }
        
    except Exception as e:
        logger.error(f"Error in reports tab: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tab/alerts", response_model=dict)
async def get_alerts_tab(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    severity: str = Query(None),
    status: str = Query(None),
):
    """
    Get Alerts tab - Alert listing with filters.
    
    Query parameters:
    - severity: Filter by severity (Low, Medium, High, Critical)
    - status: Filter by status (Active, Acknowledged, Resolved, Dismissed)
    - limit: Number of results (default 50, max 100)
    - offset: Pagination offset (default 0)
    """
    try:
        query = db.query(Alert)
        
        if severity:
            query = query.filter(Alert.severity == severity)
        if status:
            query = query.filter(Alert.status == status)
        
        total = query.count()
        alerts = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()
        
        # Count by severity
        severity_counts = {
            "low": db.query(Alert).filter(Alert.severity == "Low").count(),
            "medium": db.query(Alert).filter(Alert.severity == "Medium").count(),
            "high": db.query(Alert).filter(Alert.severity == "High").count(),
            "critical": db.query(Alert).filter(Alert.severity == "Critical").count(),
        }
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "severity_summary": severity_counts,
            "alerts": [
                {
                    "id": str(a.id),
                    "title": a.title,
                    "message": a.message,
                    "alert_type": a.alert_type,
                    "severity": a.severity,
                    "status": a.status,
                    "due_date": a.due_date.isoformat() if a.due_date else None,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "project_id": str(a.project_id) if a.project_id else None,
                    "asset_id": str(a.asset_id) if a.asset_id else None,
                }
                for a in alerts
            ],
        }
        
    except Exception as e:
        logger.error(f"Error in alerts tab: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tab/administration", response_model=dict)
async def get_administration_tab(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get Administration tab - System stats and management (Admin only).
    
    Returns:
    - User statistics
    - Project statistics
    - Asset statistics
    - System health
    - Recent audit logs
    
    Requires: Admin role
    """
    try:
        # Check if user is admin
        if not current_user.role or current_user.role.role_name not in ['Admin', 'Super Admin']:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # User stats
        total_users = db.query(User).filter(User.deleted_at.is_(None)).count()
        active_users = db.query(User).filter(
            (User.deleted_at.is_(None)) & (User.is_active == True)
        ).count()
        
        # Project stats
        total_projects = db.query(Project).filter(Project.deleted_at.is_(None)).count()
        active_projects = db.query(Project).filter(
            (Project.deleted_at.is_(None)) & (Project.status == "Active")
        ).count()
        
        # Asset stats
        total_assets = db.query(Asset).filter(Asset.deleted_at.is_(None)).count()
        assets_by_status = db.query(Asset.status, func.count(Asset.id)).filter(
            Asset.deleted_at.is_(None)
        ).group_by(Asset.status).all()
        
        # Audit log stats (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_operations = db.query(AuditLog.operation, func.count(AuditLog.id)).filter(
            AuditLog.created_at >= thirty_days_ago
        ).group_by(AuditLog.operation).all()
        
        # Get recent audit logs
        recent_logs = db.query(AuditLog).order_by(
            AuditLog.created_at.desc()
        ).limit(10).all()
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": total_users - active_users,
            },
            "projects": {
                "total": total_projects,
                "active": active_projects,
            },
            "assets": {
                "total": total_assets,
                "by_status": {status: count for status, count in assets_by_status},
            },
            "audit_activity": {
                "period_days": 30,
                "operations": {op: count for op, count in recent_operations},
            },
            "recent_audit_logs": [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "operation": log.operation,
                    "entity_type": log.entity_type,
                    "status": log.status,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in recent_logs
            ],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in administration tab: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
