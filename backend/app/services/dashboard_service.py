"""Dashboard metrics and aggregation service"""
from typing import Dict, List, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import logging

from app.models.project import Project
from app.models.resource import Resource
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard metrics and data aggregation"""
    
    @staticmethod
    def get_project_overview(db: Session, current_user: User) -> Dict[str, Any]:
        """
        Get project overview with counts and statuses.
        Applies RBAC filtering based on user role.
        
        Args:
            db: Database session
            current_user: Current user for RBAC filtering
            
        Returns:
            Dictionary with project overview data
        """
        try:
            from app.services.authorization_service import AuthorizationService
            
            # Get active projects (not deleted)
            base_query = db.query(Project).filter(Project.deleted_at.is_(None))
            
            # Apply role-based filtering
            base_query = AuthorizationService.filter_viewable_projects(current_user, base_query, db)
            
            # Count by status
            active_count = base_query.filter(Project.status == "Active").count()
            pending_count = base_query.filter(Project.status == "Pending").count()
            completed_count = base_query.filter(Project.status == "Completed").count()
            on_hold_count = base_query.filter(Project.status == "On Hold").count()
            
            # Total project count
            total_projects = base_query.count()
            
            # Get budget statistics from filtered projects
            # Note: utilization_percentage is a property, so we calculate it separately
            projects = base_query.all()
            
            total_budget = sum(float(p.budget) for p in projects)
            total_allocated = sum(float(p.allocated_budget) for p in projects)
            
            if projects and total_budget > 0:
                avg_utilization = sum(p.utilization_percentage for p in projects) / len(projects)
            else:
                avg_utilization = 0.0
            
            return {
                "total_projects": total_projects,
                "by_status": {
                    "active": active_count,
                    "pending": pending_count,
                    "completed": completed_count,
                    "on_hold": on_hold_count,
                },
                "budget": {
                    "total": float(total_budget),
                    "allocated": float(total_allocated),
                    "remaining": float(total_budget - total_allocated),
                    "avg_utilization": float(avg_utilization),
                },
            }
        except Exception as e:
            logger.error(f"Error getting project overview: {str(e)}")
            return {
                "total_projects": 0,
                "by_status": {"active": 0, "pending": 0, "completed": 0, "on_hold": 0},
                "budget": {"total": 0.0, "allocated": 0.0, "remaining": 0.0, "avg_utilization": 0.0},
            }
    
    @staticmethod
    def get_resource_distribution(db: Session, current_user: User) -> Dict[str, Any]:
        """
        Get resource distribution by type and status.
        Applies RBAC filtering based on user role.
        
        Args:
            db: Database session
            current_user: Current user for RBAC filtering
            
        Returns:
            Dictionary with resource distribution data
        """
        try:
            from app.services.authorization_service import AuthorizationService
            
            # Get non-deleted resources with RBAC filtering
            base_query = db.query(
                Resource.asset_type_id,
                func.count(Resource.id).label("count"),
                Resource.status,
            ).filter(Resource.deleted_at.is_(None))
            
            # Apply RBAC filtering
            base_query_with_rbac = db.query(Resource).filter(Resource.deleted_at.is_(None))
            base_query_with_rbac = AuthorizationService.filter_viewable_resources(
                current_user, 
                base_query_with_rbac, 
                db
            )
            
            # Get the filtered IDs to use in the distribution query
            resource_ids = [r.id for r in base_query_with_rbac.all()]
            
            # If no resources visible, return empty results
            if not resource_ids:
                return {
                    "by_type": {},
                    "by_status": {},
                    "total_resources": 0,
                }
            
            # Import AssetType model
            from app.models.asset_type import AssetType
            
            # Re-query with distribution grouping, filtered by visible resource IDs
            results = db.query(
                Resource.asset_type_id,
                AssetType.name,
                func.count(Resource.id).label("count"),
                Resource.status,
            ).join(AssetType, Resource.asset_type_id == AssetType.id).filter(
                Resource.id.in_(resource_ids),
                Resource.deleted_at.is_(None)
            ).group_by(
                Resource.asset_type_id,
                AssetType.name,
                Resource.status,
            ).all()
            
            # Format results
            distribution = {
                "by_type": {},
                "by_status": {},
                "total_resources": sum(r.count for r in results),
            }
            
            for asset_type_id, asset_type_name, count, status in results:
                # By type - use asset type name instead of ID
                if asset_type_name not in distribution["by_type"]:
                    distribution["by_type"][asset_type_name] = 0
                distribution["by_type"][asset_type_name] += count
                
                # By status
                if status not in distribution["by_status"]:
                    distribution["by_status"][status] = 0
                distribution["by_status"][status] += count
            
            return distribution
        except Exception as e:
            logger.error(f"Error getting resource distribution: {str(e)}")
            return {"by_type": {}, "by_status": {}, "total_resources": 0}
    
    @staticmethod
    def get_utilization_trends(db: Session, days: int = 30) -> Dict[str, Any]:
        """
        Get 30-day allocation trend data by resource type and date.
        
        Args:
            db: Database session
            days: Number of days to look back (default 30)
            
        Returns:
            Dictionary with trend data
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get daily resource counts
            trends = db.query(
                func.date(Resource.created_at).label("date"),
                Resource.asset_type_id,
                func.count(Resource.id).label("count"),
            ).filter(
                Resource.created_at >= start_date,
                Resource.deleted_at.is_(None),
            ).group_by(
                func.date(Resource.created_at),
                Resource.asset_type_id,
            ).order_by(
                func.date(Resource.created_at),
            ).all()
            
            # Format results
            trend_data = {}
            for date_val, asset_type_id, count in trends:
                # Handle both date objects and strings (SQLite might return strings)
                if isinstance(date_val, str):
                    date_str = date_val
                else:
                    date_str = date_val.isoformat() if date_val else "unknown"
                
                if date_str not in trend_data:
                    trend_data[date_str] = {}
                trend_data[date_str][str(asset_type_id)] = count
            
            return {
                "days": days,
                "trends": trend_data,
                "period_start": start_date.isoformat(),
                "period_end": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting utilization trends: {str(e)}")
            return {"days": days, "trends": {}, "period_start": "", "period_end": ""}
    
    @staticmethod
    def get_budget_status(db: Session, current_user: User) -> Dict[str, Any]:
        """
        Get budget status across projects with warnings.
        Applies RBAC filtering based on user role.
        
        Args:
            db: Database session
            current_user: Current user for RBAC filtering
            
        Returns:
            Dictionary with budget status data
        """
        try:
            from app.services.authorization_service import AuthorizationService
            
            # Get all non-deleted projects
            base_query = db.query(Project).filter(Project.deleted_at.is_(None))
            
            # Apply role-based filtering
            filtered_query = AuthorizationService.filter_viewable_projects(current_user, base_query, db)
            
            projects = filtered_query.all()
            
            budget_status = {
                "projects": [],
                "warnings": [],
                "critical": [],
                "total_budget": 0.0,
                "total_allocated": 0.0,
                "total_remaining": 0.0,
            }
            
            for project in projects:
                total = float(project.budget)
                allocated = float(project.allocated_budget)
                remaining = float(project.remaining_budget)
                utilization = project.utilization_percentage
                
                budget_status["total_budget"] += total
                budget_status["total_allocated"] += allocated
                budget_status["total_remaining"] += remaining
                
                project_status = {
                    "project_id": str(project.id),
                    "project_name": project.name,
                    "total_budget": total,
                    "allocated": allocated,
                    "remaining": remaining,
                    "utilization_percentage": utilization,
                }
                
                # Categorize by utilization level
                if utilization >= 100:
                    budget_status["critical"].append(project_status)
                elif utilization >= 80:
                    budget_status["warnings"].append(project_status)
                
                budget_status["projects"].append(project_status)
            
            return budget_status
        except Exception as e:
            logger.error(f"Error getting budget status: {str(e)}")
            return {
                "projects": [],
                "warnings": [],
                "critical": [],
                "total_budget": 0.0,
                "total_allocated": 0.0,
                "total_remaining": 0.0,
            }
    
    @staticmethod
    def get_dashboard_metrics(db: Session, current_user: User, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get all dashboard metrics in one call.
        
        Args:
            db: Database session
            current_user: Current user for RBAC filtering
            use_cache: Whether to use cache (default True, cache logic in routes)
            
        Returns:
            Dictionary with all dashboard metrics
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "user": {
                "id": str(current_user.id),
                "username": current_user.username,
                "role": current_user.role.role_name if current_user.role else "No Role",
            },
            "projects": DashboardService.get_project_overview(db, current_user),
            "resources": DashboardService.get_resource_distribution(db, current_user),
            "trends": DashboardService.get_utilization_trends(db),
            "budget_status": DashboardService.get_budget_status(db, current_user),
        }
