"""Phase 14: Dashboard Backend - Metrics Queries and Aggregations Tests"""
import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import uuid4
import time

from app.models.project import Project, ProjectStatus
from app.models.resource import Resource, ResourceStatus, Allocation
from app.models.asset_type import AssetType, CustomField
from app.models.user import User, UserRole
from app.services.dashboard_service import DashboardService


class TestProjectOverviewQuery:
    """Test 14.1: Project overview query service"""
    
    def test_get_project_overview_basic(self, db, test_user):
        """Test getting basic project overview"""
        # Create test project
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="Test Description",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("100000"),
            allocated_budget=Decimal("50000"),
            owner_id=test_user.id,
            start_date=date.today(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        
        # Get overview
        overview = DashboardService.get_project_overview(db, test_user)
        
        # Verify structure
        assert "total_projects" in overview
        assert "by_status" in overview
        assert "budget" in overview
        
        # Verify counts
        assert overview["total_projects"] == 1
        assert overview["by_status"]["active"] == 1
        
        # Verify budget info
        assert overview["budget"]["total"] == 100000.0
        assert overview["budget"]["allocated"] == 50000.0
        assert overview["budget"]["remaining"] == 50000.0
    
    def test_get_project_overview_multiple_projects(self, db, test_user):
        """Test project overview with multiple projects in different statuses"""
        # Create projects with different statuses
        statuses = [
            ProjectStatus.ACTIVE,
            ProjectStatus.PENDING,
            ProjectStatus.COMPLETED,
            ProjectStatus.ON_HOLD,
            ProjectStatus.ACTIVE  # Second active project
        ]
        
        for i, status in enumerate(statuses):
            project = Project(
                id=uuid4(),
                name=f"Project {i}",
                status=status,
                budget=Decimal("10000"),
                allocated_budget=Decimal("5000"),
                owner_id=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(project)
        
        db.commit()
        
        overview = DashboardService.get_project_overview(db, test_user)
        
        # Verify counts
        assert overview["total_projects"] == 5
        assert overview["by_status"]["active"] == 2
        assert overview["by_status"]["pending"] == 1
        assert overview["by_status"]["completed"] == 1
        assert overview["by_status"]["on_hold"] == 1
        
        # Verify aggregated budget
        assert overview["budget"]["total"] == 50000.0
        assert overview["budget"]["allocated"] == 25000.0
    
    def test_project_overview_excludes_deleted_projects(self, db, test_user):
        """Test that soft-deleted projects are excluded"""
        # Create regular and deleted projects
        active_project = Project(
            id=uuid4(),
            name="Active Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("10000"),
            allocated_budget=Decimal("5000"),
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        deleted_project = Project(
            id=uuid4(),
            name="Deleted Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("20000"),
            allocated_budget=Decimal("10000"),
            owner_id=test_user.id,
            deleted_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(active_project)
        db.add(deleted_project)
        db.commit()
        
        overview = DashboardService.get_project_overview(db, test_user)
        
        # Only active project should be counted
        assert overview["total_projects"] == 1
        assert overview["budget"]["total"] == 10000.0
    
    def test_project_overview_role_based_filtering(self, db, test_user, test_admin_user):
        """Test RBAC filtering in project overview"""
        # Create project owned by admin
        admin_project = Project(
            id=uuid4(),
            name="Admin Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("50000"),
            allocated_budget=Decimal("25000"),
            owner_id=test_admin_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Create project owned by test user
        user_project = Project(
            id=uuid4(),
            name="User Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("10000"),
            allocated_budget=Decimal("5000"),
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(admin_project)
        db.add(user_project)
        db.commit()
        
        # Admin should see all projects
        admin_overview = DashboardService.get_project_overview(db, test_admin_user)
        assert admin_overview["total_projects"] >= 2
        
        # Manager/regular user should see owned projects
        user_overview = DashboardService.get_project_overview(db, test_user)
        assert user_overview["total_projects"] >= 1


class TestResourceDistributionAggregation:
    """Test 14.2: Resource distribution aggregation"""
    
    def test_resource_distribution_by_type(self, db, test_user):
        """Test resource distribution grouped by type"""
        # Create asset types
        asset_type1 = AssetType(id=uuid4(), name="Personnel")
        asset_type2 = AssetType(id=uuid4(), name="Equipment")
        db.add(asset_type1)
        db.add(asset_type2)
        
        # Create project
        project = Project(
            id=uuid4(),
            name="Test Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("100000"),
            allocated_budget=Decimal("0"),
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        
        # Create resources of different types
        for i in range(3):
            resource = Resource(
                id=uuid4(),
                project_id=project.id,
                asset_type_id=asset_type1.id,
                name=f"Personnel {i}",
                cost=Decimal("5000"),
                allocation_date=date.today(),
                status=ResourceStatus.ACTIVE,
                created_by=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(resource)
        
        for i in range(2):
            resource = Resource(
                id=uuid4(),
                project_id=project.id,
                asset_type_id=asset_type2.id,
                name=f"Equipment {i}",
                cost=Decimal("10000"),
                allocation_date=date.today(),
                status=ResourceStatus.ACTIVE,
                created_by=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(resource)
        
        db.commit()
        
        # Get distribution
        distribution = DashboardService.get_resource_distribution(db, test_user)
        
        # Verify structure
        assert "by_type" in distribution
        assert "by_status" in distribution
        assert "total_resources" in distribution
        
        # Verify counts
        assert distribution["total_resources"] == 5
        assert str(asset_type1.id) in distribution["by_type"]
        assert str(asset_type2.id) in distribution["by_type"]
        assert distribution["by_type"][str(asset_type1.id)] == 3
        assert distribution["by_type"][str(asset_type2.id)] == 2
    
    def test_resource_distribution_by_status(self, db, test_user):
        """Test resource distribution grouped by status"""
        asset_type = AssetType(id=uuid4(), name="Personnel")
        db.add(asset_type)
        
        project = Project(
            id=uuid4(),
            name="Test Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("100000"),
            allocated_budget=Decimal("0"),
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        
        # Create active and inactive resources
        for i in range(3):
            resource = Resource(
                id=uuid4(),
                project_id=project.id,
                asset_type_id=asset_type.id,
                name=f"Resource {i}",
                cost=Decimal("5000"),
                allocation_date=date.today(),
                status=ResourceStatus.ACTIVE,
                created_by=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(resource)
        
        for i in range(2):
            resource = Resource(
                id=uuid4(),
                project_id=project.id,
                asset_type_id=asset_type.id,
                name=f"Inactive {i}",
                cost=Decimal("5000"),
                allocation_date=date.today(),
                status=ResourceStatus.INACTIVE,
                created_by=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(resource)
        
        db.commit()
        
        distribution = DashboardService.get_resource_distribution(db, test_user)
        
        # Verify status breakdown
        assert distribution["by_status"]["Active"] == 3
        assert distribution["by_status"]["Inactive"] == 2
        assert distribution["total_resources"] == 5
    
    def test_resource_distribution_excludes_deleted(self, db, test_user):
        """Test that soft-deleted resources are excluded"""
        asset_type = AssetType(id=uuid4(), name="Personnel")
        db.add(asset_type)
        
        project = Project(
            id=uuid4(),
            name="Test Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("100000"),
            allocated_budget=Decimal("0"),
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        
        # Create active resource
        active_resource = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name="Active",
            cost=Decimal("5000"),
            allocation_date=date.today(),
            status=ResourceStatus.ACTIVE,
            created_by=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Create deleted resource
        deleted_resource = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name="Deleted",
            cost=Decimal("5000"),
            allocation_date=date.today(),
            status=ResourceStatus.ACTIVE,
            deleted_at=datetime.utcnow(),
            created_by=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(active_resource)
        db.add(deleted_resource)
        db.commit()
        
        distribution = DashboardService.get_resource_distribution(db, test_user)
        
        # Only active resource should be counted
        assert distribution["total_resources"] == 1
        assert distribution["by_status"]["Active"] == 1


class TestUtilizationTrendCalculation:
    """Test 14.3: Utilization trend calculation"""
    
    def test_utilization_trends_30_days(self, db, test_user):
        """Test 30-day utilization trends"""
        asset_type = AssetType(id=uuid4(), name="Personnel")
        db.add(asset_type)
        
        project = Project(
            id=uuid4(),
            name="Test Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("100000"),
            allocated_budget=Decimal("0"),
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        
        # Create resources across different dates
        base_date = datetime.utcnow()
        
        for day_offset in [0, 5, 10, 15, 20]:
            for i in range(2):
                resource = Resource(
                    id=uuid4(),
                    project_id=project.id,
                    asset_type_id=asset_type.id,
                    name=f"Resource {day_offset}_{i}",
                    cost=Decimal("5000"),
                    allocation_date=date.today(),
                    status=ResourceStatus.ACTIVE,
                    created_by=test_user.id,
                    created_at=base_date - timedelta(days=day_offset),
                    updated_at=base_date - timedelta(days=day_offset)
                )
                db.add(resource)
        
        db.commit()
        
        trends = DashboardService.get_utilization_trends(db, days=30)
        
        # Verify structure
        assert "days" in trends
        assert "trends" in trends
        assert "period_start" in trends
        assert "period_end" in trends
        
        # Verify trend data exists
        assert len(trends["trends"]) > 0
        assert trends["days"] == 30
    
    def test_utilization_trends_by_type(self, db, test_user):
        """Test that trends track resources by asset type"""
        asset_type1 = AssetType(id=uuid4(), name="Personnel")
        asset_type2 = AssetType(id=uuid4(), name="Equipment")
        db.add(asset_type1)
        db.add(asset_type2)
        
        project = Project(
            id=uuid4(),
            name="Test Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("100000"),
            allocated_budget=Decimal("0"),
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        
        # Create resources of different types with same creation date
        creation_date = datetime.utcnow()
        
        for i in range(3):
            resource = Resource(
                id=uuid4(),
                project_id=project.id,
                asset_type_id=asset_type1.id,
                name=f"Personnel {i}",
                cost=Decimal("5000"),
                allocation_date=date.today(),
                status=ResourceStatus.ACTIVE,
                created_by=test_user.id,
                created_at=creation_date,
                updated_at=creation_date
            )
            db.add(resource)
        
        for i in range(2):
            resource = Resource(
                id=uuid4(),
                project_id=project.id,
                asset_type_id=asset_type2.id,
                name=f"Equipment {i}",
                cost=Decimal("10000"),
                allocation_date=date.today(),
                status=ResourceStatus.ACTIVE,
                created_by=test_user.id,
                created_at=creation_date,
                updated_at=creation_date
            )
            db.add(resource)
        
        db.commit()
        
        trends = DashboardService.get_utilization_trends(db, days=30)
        
        # Get today's date from trends
        today = creation_date.date().isoformat()
        
        if today in trends["trends"]:
            assert str(asset_type1.id) in trends["trends"][today]
            assert str(asset_type2.id) in trends["trends"][today]
            assert trends["trends"][today][str(asset_type1.id)] == 3
            assert trends["trends"][today][str(asset_type2.id)] == 2
    
    def test_utilization_trends_excludes_deleted(self, db, test_user):
        """Test that soft-deleted resources are excluded from trends"""
        asset_type = AssetType(id=uuid4(), name="Personnel")
        db.add(asset_type)
        
        project = Project(
            id=uuid4(),
            name="Test Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("100000"),
            allocated_budget=Decimal("0"),
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        
        creation_date = datetime.utcnow()
        
        # Create active resource
        active_resource = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name="Active",
            cost=Decimal("5000"),
            allocation_date=date.today(),
            status=ResourceStatus.ACTIVE,
            created_by=test_user.id,
            created_at=creation_date,
            updated_at=creation_date
        )
        
        # Create deleted resource
        deleted_resource = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name="Deleted",
            cost=Decimal("5000"),
            allocation_date=date.today(),
            status=ResourceStatus.ACTIVE,
            deleted_at=creation_date,
            created_by=test_user.id,
            created_at=creation_date,
            updated_at=creation_date
        )
        
        db.add(active_resource)
        db.add(deleted_resource)
        db.commit()
        
        trends = DashboardService.get_utilization_trends(db, days=30)
        
        # Count resources in today's trend
        today = creation_date.date().isoformat()
        if today in trends["trends"]:
            total_count = sum(trends["trends"][today].values())
            # Only active resource should be counted
            assert total_count == 1


class TestDashboardMetricsEndpoint:
    """Test 14.4: Dashboard metrics endpoint"""
    
    def test_get_dashboard_metrics_combined(self, db, test_user):
        """Test combined dashboard metrics"""
        # Create test data
        project = Project(
            id=uuid4(),
            name="Test Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("100000"),
            allocated_budget=Decimal("50000"),
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        
        # Get combined metrics
        metrics = DashboardService.get_dashboard_metrics(db, test_user)
        
        # Verify structure
        assert "timestamp" in metrics
        assert "user" in metrics
        assert "projects" in metrics
        assert "resources" in metrics
        assert "trends" in metrics
        assert "budget_status" in metrics
        
        # Verify user info
        assert metrics["user"]["id"] == str(test_user.id)
        assert metrics["user"]["username"] == test_user.username
        assert metrics["user"]["role"] == test_user.role
        
        # Verify each section has data
        assert "total_projects" in metrics["projects"]
        assert "total_resources" in metrics["resources"]
        assert "projects" in metrics["budget_status"]
    
    def test_dashboard_metrics_performance(self, db, test_user):
        """Test that dashboard metrics query completes within 2 seconds"""
        # Create multiple projects and resources
        for i in range(10):
            project = Project(
                id=uuid4(),
                name=f"Project {i}",
                status=ProjectStatus.ACTIVE,
                budget=Decimal("100000"),
                allocated_budget=Decimal("50000"),
                owner_id=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(project)
        
        db.commit()
        
        # Measure performance
        start_time = time.time()
        metrics = DashboardService.get_dashboard_metrics(db, test_user)
        elapsed = time.time() - start_time
        
        # Should complete within 2 seconds
        assert elapsed < 2.0, f"Dashboard metrics took {elapsed}s, expected < 2s"
        assert metrics is not None


class TestBudgetStatusEndpoint:
    """Test 14.5: Budget status endpoint"""
    
    def test_budget_status_warning_threshold(self, db, test_user):
        """Test budget status warning at 80% utilization"""
        project = Project(
            id=uuid4(),
            name="Test Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("10000"),
            allocated_budget=Decimal("8000"),  # 80% utilization
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        
        budget_status = DashboardService.get_budget_status(db, test_user)
        
        # Verify structure
        assert "projects" in budget_status
        assert "warnings" in budget_status
        assert "critical" in budget_status
        
        # Project should be in warnings (80-99%)
        assert len(budget_status["warnings"]) == 1
        assert len(budget_status["critical"]) == 0
        assert budget_status["warnings"][0]["utilization_percentage"] == 80.0
    
    def test_budget_status_critical_threshold(self, db, test_user):
        """Test budget status critical at 100% utilization"""
        project = Project(
            id=uuid4(),
            name="Critical Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("10000"),
            allocated_budget=Decimal("10000"),  # 100% utilization
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        
        budget_status = DashboardService.get_budget_status(db, test_user)
        
        # Project should be in critical
        assert len(budget_status["critical"]) == 1
        assert budget_status["critical"][0]["utilization_percentage"] == 100.0
    
    def test_budget_status_multiple_projects(self, db, test_user):
        """Test budget status aggregation across multiple projects"""
        projects = [
            Project(
                id=uuid4(),
                name="Under Budget",
                status=ProjectStatus.ACTIVE,
                budget=Decimal("10000"),
                allocated_budget=Decimal("5000"),  # 50%
                owner_id=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Project(
                id=uuid4(),
                name="Warning Project",
                status=ProjectStatus.ACTIVE,
                budget=Decimal("10000"),
                allocated_budget=Decimal("8500"),  # 85%
                owner_id=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Project(
                id=uuid4(),
                name="Critical Project",
                status=ProjectStatus.ACTIVE,
                budget=Decimal("10000"),
                allocated_budget=Decimal("10000"),  # 100%
                owner_id=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
        ]
        
        for project in projects:
            db.add(project)
        
        db.commit()
        
        budget_status = DashboardService.get_budget_status(db, test_user)
        
        # Verify all projects are returned
        assert len(budget_status["projects"]) == 3
        assert len(budget_status["warnings"]) == 1
        assert len(budget_status["critical"]) == 1
        
        # Verify aggregated totals
        assert budget_status["total_budget"] == 30000.0
        assert budget_status["total_allocated"] == 23500.0
        assert budget_status["total_remaining"] == 6500.0


class TestCacheInvalidation:
    """Test cache invalidation on mutations"""
    
    def test_cache_invalidation_on_create(self, db, test_user):
        """Test that creating resources doesn't affect cache integrity"""
        # Create test data
        project = Project(
            id=uuid4(),
            name="Test Project",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("100000"),
            allocated_budget=Decimal("50000"),
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        
        # Get metrics once
        metrics1 = DashboardService.get_dashboard_metrics(db, test_user)
        assert metrics1["projects"]["total_projects"] == 1
        
        # Create another project
        project2 = Project(
            id=uuid4(),
            name="Test Project 2",
            status=ProjectStatus.ACTIVE,
            budget=Decimal("50000"),
            allocated_budget=Decimal("25000"),
            owner_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(project2)
        db.commit()
        
        # Get metrics again - should reflect new project
        metrics2 = DashboardService.get_dashboard_metrics(db, test_user)
        assert metrics2["projects"]["total_projects"] == 2
