"""Dashboard API routes for metrics and visualizations"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.models.user import User
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
