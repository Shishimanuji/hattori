"""Phase 7: Project Management Backend Tests

Tests for:
- 7.1: Project model and schemas
- 7.2: Project API endpoints (CRUD, pagination, filtering, sorting)
- 7.3: Project budget tracking
- 7.4: Project soft deletes
- 7.5: Property tests for budget updates

Validates Requirements: 5.1, 5.2, 5.3, 5.6, 5.7, 10.1, 10.2
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus
from app.models.user import User, UserRole
from app.models.resource import Resource, Allocation
from app.models.asset_type import AssetType
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
)
from app.services.project_service import (
    get_projects_paginated,
    get_project_by_id,
    create_project,
    update_project,
    delete_project,
    get_project_resource_summary,
    check_can_add_resources,
    update_project_allocated_budget,
    ProjectNotFoundError,
    ProjectPermissionError,
)
from app.core.database import get_db


def create_test_user(db: Session, username: str = "testuser", role: UserRole = UserRole.MANAGER):
    """Helper to create a test user"""
    user = User(
        id=uuid4(),
        username=username,
        email=f"{username}@example.com",
        password_hash="hashed_password",
        role=role.value,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_test_asset_type(db: Session, name: str = "Personnel"):
    """Helper to create a test asset type"""
    asset_type = AssetType(
        id=uuid4(),
        name=name,
        description=f"{name} resources",
    )
    db.add(asset_type)
    db.commit()
    db.refresh(asset_type)
    return asset_type


def create_test_project(db: Session, user_id: UUID, name: str = "Test Project"):
    """Helper to create a test project"""
    project = Project(
        id=uuid4(),
        name=name,
        description="A test project",
        status=ProjectStatus.ACTIVE,
        budget=Decimal("10000.00"),
        allocated_budget=Decimal("0.00"),
        owner_id=user_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


class TestProjectModel:
    """Test Project model functionality"""

    def test_project_creation(self, db: Session):
        """Test creating a project - Validates Requirement 5.1"""
        user = create_test_user(db)
        
        project = create_project(
            db=db,
            name="New Project",
            budget=Decimal("50000.00"),
            current_user_id=user.id,
            description="Project description",
            status=ProjectStatus.ACTIVE,
        )

        assert project.id is not None
        assert project.name == "New Project"
        assert project.budget == Decimal("50000.00")
        assert project.allocated_budget == Decimal("0.00")
        assert project.owner_id == user.id
        assert project.deleted_at is None

    def test_project_remaining_budget_calculation(self, db: Session):
        """Test remaining budget property - Validates Requirement 10.1"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        project.allocated_budget = Decimal("3000.00")
        remaining = project.remaining_budget

        assert remaining == Decimal("7000.00")

    def test_project_utilization_percentage(self, db: Session):
        """Test budget utilization percentage - Validates Requirement 10.2"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        project.allocated_budget = Decimal("2500.00")
        utilization = project.utilization_percentage

        assert utilization == 25.0

    def test_project_utilization_percentage_at_100(self, db: Session):
        """Test utilization percentage when budget is fully allocated"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        project.allocated_budget = Decimal("10000.00")
        utilization = project.utilization_percentage

        assert utilization == 100.0

    def test_project_soft_delete(self, db: Session):
        """Test soft delete sets deleted_at - Validates Requirement 5.6"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        assert project.deleted_at is None
        
        project.deleted_at = datetime.utcnow()
        assert project.is_deleted() is True

    def test_can_add_resources_to_active_project(self, db: Session):
        """Test can_add_resources returns True for active project"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        can_add = check_can_add_resources(db, project.id)
        assert can_add is True

    def test_cannot_add_resources_to_deleted_project(self, db: Session):
        """Test can_add_resources returns False for deleted project - Validates Requirement 5.7"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        project.deleted_at = datetime.utcnow()
        db.commit()

        can_add = check_can_add_resources(db, project.id)
        assert can_add is False


class TestProjectSchemas:
    """Test Pydantic schemas for validation"""

    def test_project_create_schema_validation(self):
        """Test ProjectCreate schema validates input"""
        # Valid data
        data = ProjectCreate(
            name="Valid Project",
            budget=Decimal("5000.00"),
            status="Active",
        )
        assert data.name == "Valid Project"

    def test_project_create_negative_budget_rejected(self):
        """Test ProjectCreate schema rejects negative budget"""
        with pytest.raises(ValueError):
            ProjectCreate(
                name="Bad Project",
                budget=Decimal("-1000.00"),
            )

    def test_project_create_schema_end_date_validation(self):
        """Test ProjectCreate schema validates end_date >= start_date"""
        start = date(2024, 1, 1)
        end = date(2023, 12, 31)

        with pytest.raises(ValueError):
            ProjectCreate(
                name="Bad Dates",
                budget=Decimal("5000.00"),
                start_date=start,
                end_date=end,
            )


class TestProjectCRUDOperations:
    """Test Project CRUD operations via service layer"""

    def test_create_project_service(self, db: Session):
        """Test create_project service - Validates Requirement 5.1"""
        user = create_test_user(db)
        
        project = create_project(
            db=db,
            name="Service Test Project",
            budget=Decimal("15000.00"),
            current_user_id=user.id,
            description="Service test",
        )

        assert project.id is not None
        assert project.name == "Service Test Project"
        assert project.owner_id == user.id

    def test_get_project_by_id(self, db: Session):
        """Test get_project_by_id service"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        retrieved = get_project_by_id(db, project.id)

        assert retrieved.id == project.id
        assert retrieved.name == project.name

    def test_get_nonexistent_project_raises_error(self, db: Session):
        """Test get_project_by_id raises ProjectNotFoundError"""
        fake_id = UUID("00000000-0000-0000-0000-000000000000")

        with pytest.raises(ProjectNotFoundError):
            get_project_by_id(db, fake_id)

    def test_update_project_by_owner(self, db: Session):
        """Test update_project by owner - Validates Requirement 5.2"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        updated = update_project(
            db=db,
            project_id=project.id,
            current_user_id=user.id,
            name="Updated Project Name",
            budget=Decimal("20000.00"),
        )

        assert updated.name == "Updated Project Name"
        assert updated.budget == Decimal("20000.00")

    def test_update_project_non_owner_raises_error(self, db: Session):
        """Test update_project raises error for non-owner"""
        owner = create_test_user(db, "owner", UserRole.MANAGER)
        other_user = create_test_user(db, "other", UserRole.MANAGER)
        project = create_test_project(db, owner.id)
        
        with pytest.raises(ProjectPermissionError):
            update_project(
                db=db,
                project_id=project.id,
                current_user_id=other_user.id,
                name="Hacker Project",
            )

    def test_delete_project_soft_delete(self, db: Session):
        """Test delete_project performs soft delete - Validates Requirement 5.6"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        delete_project(db, project.id, user.id)

        # Retrieve and verify deleted_at is set
        deleted = get_project_by_id(db, project.id)
        assert deleted.deleted_at is not None

    def test_delete_project_non_owner_raises_error(self, db: Session):
        """Test delete_project raises error for non-owner"""
        owner = create_test_user(db, "owner", UserRole.MANAGER)
        other_user = create_test_user(db, "other", UserRole.MANAGER)
        project = create_test_project(db, owner.id)
        
        with pytest.raises(ProjectPermissionError):
            delete_project(db, project.id, other_user.id)

    def test_deleted_project_data_retained(self, db: Session):
        """Test deleted project data is retained for queries - Validates Requirement 5.7"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        original_name = project.name
        
        delete_project(db, project.id, user.id)

        # Data should still be queryable
        deleted = get_project_by_id(db, project.id)
        assert deleted.name == original_name
        assert deleted.deleted_at is not None


class TestProjectListingFiltering:
    """Test project listing with pagination, filtering, sorting"""

    def test_list_projects_pagination(self, db: Session):
        """Test get_projects_paginated - Validates Requirement 5.8"""
        user = create_test_user(db)
        
        # Create multiple projects
        for i in range(5):
            create_project(
                db=db,
                name=f"Project {i}",
                budget=Decimal("5000.00"),
                current_user_id=user.id,
            )

        projects, total = get_projects_paginated(db, skip=0, limit=2)

        assert len(projects) == 2
        assert total == 5

    def test_list_projects_with_status_filter(self, db: Session):
        """Test get_projects_paginated with status filtering"""
        user = create_test_user(db)
        
        # Create projects with different statuses
        active = create_project(
            db=db,
            name="Active Project",
            budget=Decimal("5000.00"),
            current_user_id=user.id,
            status=ProjectStatus.ACTIVE,
        )
        
        pending = create_project(
            db=db,
            name="Pending Project",
            budget=Decimal("5000.00"),
            current_user_id=user.id,
            status=ProjectStatus.PENDING,
        )

        projects, total = get_projects_paginated(
            db, skip=0, limit=10, status_filter=ProjectStatus.ACTIVE
        )

        assert total == 1
        assert projects[0].id == active.id

    def test_list_projects_with_search(self, db: Session):
        """Test get_projects_paginated with search filtering - Validates Requirement 5.9"""
        user = create_test_user(db)
        
        create_project(
            db=db,
            name="Engineering Project",
            budget=Decimal("5000.00"),
            current_user_id=user.id,
        )
        
        create_project(
            db=db,
            name="Sales Project",
            budget=Decimal("5000.00"),
            current_user_id=user.id,
        )

        projects, total = get_projects_paginated(db, skip=0, limit=10, search="Engineering")

        assert len(projects) == 1
        assert projects[0].name == "Engineering Project"

    def test_list_projects_sorted_by_name(self, db: Session):
        """Test get_projects_paginated with name sorting"""
        user = create_test_user(db)
        
        create_project(
            db=db,
            name="Zebra Project",
            budget=Decimal("5000.00"),
            current_user_id=user.id,
        )
        
        create_project(
            db=db,
            name="Apple Project",
            budget=Decimal("5000.00"),
            current_user_id=user.id,
        )

        projects, _ = get_projects_paginated(
            db, skip=0, limit=10, sort_by="name", sort_order="asc"
        )

        assert projects[0].name == "Apple Project"
        assert projects[1].name == "Zebra Project"

    def test_list_projects_sorted_by_budget(self, db: Session):
        """Test get_projects_paginated with budget sorting"""
        user = create_test_user(db)
        
        create_project(
            db=db,
            name="High Budget",
            budget=Decimal("50000.00"),
            current_user_id=user.id,
        )
        
        create_project(
            db=db,
            name="Low Budget",
            budget=Decimal("5000.00"),
            current_user_id=user.id,
        )

        projects, _ = get_projects_paginated(
            db, skip=0, limit=10, sort_by="budget", sort_order="asc"
        )

        assert projects[0].budget == Decimal("5000.00")
        assert projects[1].budget == Decimal("50000.00")

    def test_list_excludes_deleted_projects(self, db: Session):
        """Test that soft-deleted projects are excluded from list"""
        user = create_test_user(db)
        
        active = create_project(
            db=db,
            name="Active",
            budget=Decimal("5000.00"),
            current_user_id=user.id,
        )
        
        deleted = create_project(
            db=db,
            name="Deleted",
            budget=Decimal("5000.00"),
            current_user_id=user.id,
        )
        
        delete_project(db, deleted.id, user.id)

        projects, total = get_projects_paginated(db, skip=0, limit=10)

        assert total == 1
        assert projects[0].id == active.id


class TestProjectBudgetTracking:
    """Test budget tracking and allocation - Validates Requirement 10.1, 10.2"""

    def test_update_allocated_budget_add(self, db: Session):
        """Test adding to allocated budget - Validates Requirement 10.1"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        initial_allocated = project.allocated_budget
        
        updated = update_project_allocated_budget(
            db,
            project.id,
            Decimal("1000.00"),
            operation="add",
        )

        assert updated.allocated_budget == initial_allocated + Decimal("1000.00")

    def test_update_allocated_budget_subtract(self, db: Session):
        """Test subtracting from allocated budget"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        project.allocated_budget = Decimal("5000.00")
        db.commit()

        updated = update_project_allocated_budget(
            db,
            project.id,
            Decimal("1000.00"),
            operation="subtract",
        )

        assert updated.allocated_budget == Decimal("4000.00")

    def test_allocated_budget_cannot_go_negative(self, db: Session):
        """Test allocated budget doesn't go negative"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        project.allocated_budget = Decimal("500.00")
        db.commit()

        updated = update_project_allocated_budget(
            db,
            project.id,
            Decimal("1000.00"),
            operation="subtract",
        )

        assert updated.allocated_budget == Decimal("0.00")

    def test_project_resource_summary(self, db: Session):
        """Test get_project_resource_summary"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        asset_type = create_test_asset_type(db)
        
        # Create resources
        resource1 = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name="Resource 1",
            cost=Decimal("1000.00"),
            allocation_date=date.today(),
            status="Active",
            created_by=user.id,
        )
        
        resource2 = Resource(
            id=uuid4(),
            project_id=project.id,
            asset_type_id=asset_type.id,
            name="Resource 2",
            cost=Decimal("2000.00"),
            allocation_date=date.today(),
            status="Active",
            created_by=user.id,
        )
        
        db.add_all([resource1, resource2])
        db.commit()

        summary = get_project_resource_summary(db, project.id)

        assert summary["total_count"] == 2
        assert summary["by_type"]["Personnel"] == 2


class TestProjectBudgetConstraints:
    """Test budget constraint enforcement - Validates Requirement 10.4"""

    def test_project_with_100_percent_budget_utilization(self, db: Session):
        """Test utilization percentage at 100%"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        project.allocated_budget = project.budget
        
        assert project.utilization_percentage == 100.0

    def test_project_with_80_percent_budget_utilization(self, db: Session):
        """Test warning threshold at 80%"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        project.allocated_budget = project.budget * Decimal("0.8")
        
        assert project.utilization_percentage == 80.0

    def test_remaining_budget_calculation(self, db: Session):
        """Test remaining budget calculation"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        project.allocated_budget = Decimal("7000.00")
        remaining = project.remaining_budget
        
        assert remaining == Decimal("3000.00")


class TestProjectPropertyBased:
    """Property-based tests for project operations

    Validates: Requirements 5.1, 10.1
    """

    def test_property_13_budget_updates_follow_resource_allocation(self, db: Session):
        """Property 13: Budget updates follow resource allocation

        When resources are allocated/deallocated, the project's allocated_budget
        should update accordingly, maintaining consistency between allocations
        and project budget state.

        Validates: Requirements 5.1, 10.1, 10.2
        """
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        # Initial state
        assert project.allocated_budget == Decimal("0.00")
        assert project.remaining_budget == Decimal("10000.00")

        # Allocate $3000
        after_allocation_1 = update_project_allocated_budget(
            db, project.id, Decimal("3000.00"), operation="add"
        )
        assert after_allocation_1.allocated_budget == Decimal("3000.00")
        assert after_allocation_1.remaining_budget == Decimal("7000.00")
        assert after_allocation_1.utilization_percentage == 30.0

        # Allocate another $2000
        after_allocation_2 = update_project_allocated_budget(
            db, project.id, Decimal("2000.00"), operation="add"
        )
        assert after_allocation_2.allocated_budget == Decimal("5000.00")
        assert after_allocation_2.remaining_budget == Decimal("5000.00")
        assert after_allocation_2.utilization_percentage == 50.0

        # Deallocate $1000
        after_deallocation = update_project_allocated_budget(
            db, project.id, Decimal("1000.00"), operation="subtract"
        )
        assert after_deallocation.allocated_budget == Decimal("4000.00")
        assert after_deallocation.remaining_budget == Decimal("6000.00")
        assert after_deallocation.utilization_percentage == 40.0

        # Allocate to 100%
        full_allocation = update_project_allocated_budget(
            db, project.id, Decimal("6000.00"), operation="add"
        )
        assert full_allocation.allocated_budget == Decimal("10000.00")
        assert full_allocation.remaining_budget == Decimal("0.00")
        assert full_allocation.utilization_percentage == 100.0

    def test_project_state_consistency_across_operations(self, db: Session):
        """Property: Project state remains consistent across create, update, delete"""
        user = create_test_user(db)
        
        # Create state
        created = create_project(
            db=db,
            name="Consistency Test",
            budget=Decimal("25000.00"),
            current_user_id=user.id,
        )
        assert created.status == ProjectStatus.ACTIVE
        assert created.deleted_at is None

        # Update state
        updated = update_project(
            db=db,
            project_id=created.id,
            current_user_id=user.id,
            status=ProjectStatus.PENDING,
        )
        assert updated.status == ProjectStatus.PENDING
        assert updated.deleted_at is None

        # Delete state
        delete_project(db, created.id, user.id)
        
        retrieved = get_project_by_id(db, created.id)
        assert retrieved.deleted_at is not None

    def test_budget_zero_utilization_percentage(self, db: Session):
        """Property: Projects with zero budget handle utilization gracefully"""
        user = create_test_user(db)
        project = create_test_project(db, user.id)
        
        project.budget = Decimal("0.00")
        project.allocated_budget = Decimal("0.00")
        
        # Should return 0 when budget is 0
        assert project.utilization_percentage == 0.0
