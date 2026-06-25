"""Tests for import validation service"""
import pytest
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.asset_type import AssetType, CustomField, FieldType
from app.models.project import Project, ProjectStatus
from app.models.user import User, UserRole
from app.services.import_validation_service import (
    ImportValidationService,
    ColumnHeaderValidationError,
    RowValidationError,
)


@pytest.fixture
def validation_service(db: Session) -> ImportValidationService:
    """Create an import validation service"""
    return ImportValidationService(db)


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user"""
    user = User(
        username="test_user",
        email="test@example.com",
        password_hash="hashed_password",
        role=UserRole.MANAGER,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def test_project(db: Session, test_user: User) -> Project:
    """Create a test project with budget"""
    project = Project(
        name="Test Project",
        description="Test project for import validation",
        status=ProjectStatus.ACTIVE,
        budget=Decimal("10000.00"),
        allocated_budget=Decimal("2000.00"),
        owner_id=test_user.id,
    )
    db.add(project)
    db.commit()
    return project


@pytest.fixture
def asset_type_with_fields(db: Session) -> AssetType:
    """Create asset type with various custom fields"""
    asset_type = AssetType(
        name="Equipment",
        description="Equipment asset type",
        is_active=True,
    )
    
    # Add custom fields
    text_field = CustomField(
        asset_type=asset_type,
        name="department",
        field_type=FieldType.TEXT,
        is_required=False,
        validation_rules={"min": 1, "max": 50},
    )
    
    number_field = CustomField(
        asset_type=asset_type,
        name="quantity",
        field_type=FieldType.NUMBER,
        is_required=True,
        validation_rules={"min": 1, "max": 1000},
    )
    
    dropdown_field = CustomField(
        asset_type=asset_type,
        name="status",
        field_type=FieldType.DROPDOWN,
        is_required=False,
        options=["New", "Used", "Refurbished"],
    )
    
    asset_type.custom_fields = [text_field, number_field, dropdown_field]
    
    db.add(asset_type)
    db.add(text_field)
    db.add(number_field)
    db.add(dropdown_field)
    db.commit()
    
    return asset_type


class TestColumnHeaderValidation:
    """Tests for column header validation"""
    
    def test_validate_headers_with_required_fields(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Headers with required fields should pass validation"""
        headers = ["name", "cost", "department"]
        is_valid, errors = validation_service.validate_column_headers(
            headers,
            asset_type_with_fields,
        )
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_headers_missing_required_field(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Headers without required 'name' field should fail"""
        headers = ["cost", "department"]
        is_valid, errors = validation_service.validate_column_headers(
            headers,
            asset_type_with_fields,
        )
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("name" in e.error_message for e in errors)
    
    def test_validate_headers_case_insensitive(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Header validation should be case-insensitive"""
        headers = ["NAME", "Cost", "DEPARTMENT"]
        is_valid, errors = validation_service.validate_column_headers(
            headers,
            asset_type_with_fields,
        )
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_headers_with_invalid_column(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Headers with unrecognized columns should report errors"""
        headers = ["name", "cost", "invalid_field"]
        is_valid, errors = validation_service.validate_column_headers(
            headers,
            asset_type_with_fields,
        )
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("invalid_field" in e.error_message for e in errors)
    
    def test_validate_headers_with_duplicate_columns(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Headers with duplicate columns should fail"""
        headers = ["name", "cost", "name"]
        is_valid, errors = validation_service.validate_column_headers(
            headers,
            asset_type_with_fields,
        )
        
        assert is_valid is False
        assert any("Duplicate" in e.error_message for e in errors)
    
    def test_validate_headers_empty_list(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Empty headers list should fail"""
        headers = []
        is_valid, errors = validation_service.validate_column_headers(
            headers,
            asset_type_with_fields,
        )
        
        assert is_valid is False
        assert len(errors) > 0


class TestRowValidation:
    """Tests for row-level validation"""
    
    def test_validate_row_with_required_fields(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Row with required fields should pass"""
        row_data = {
            "name": "Equipment 1",
            "cost": "1000.00",
            "quantity": 5,
        }
        is_valid, error = validation_service.validate_row_against_schema(
            row_data,
            asset_type_with_fields,
            row_number=2,
        )
        
        assert is_valid is True
        assert error is None
    
    def test_validate_row_missing_required_field(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Row without required 'name' field should fail"""
        row_data = {
            "cost": "1000.00",
            "quantity": 5,
        }
        is_valid, error = validation_service.validate_row_against_schema(
            row_data,
            asset_type_with_fields,
            row_number=2,
        )
        
        assert is_valid is False
        assert error is not None
        assert any("name" in str(f) for f in error.field_errors)
    
    def test_validate_row_with_empty_name(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Row with empty name field should fail"""
        row_data = {
            "name": "   ",  # Empty/whitespace only
            "quantity": 5,
        }
        is_valid, error = validation_service.validate_row_against_schema(
            row_data,
            asset_type_with_fields,
            row_number=2,
        )
        
        assert is_valid is False
        assert error is not None
    
    def test_validate_row_with_invalid_cost(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Row with invalid cost format should fail"""
        row_data = {
            "name": "Equipment 1",
            "cost": "not_a_number",
            "quantity": 5,
        }
        is_valid, error = validation_service.validate_row_against_schema(
            row_data,
            asset_type_with_fields,
            row_number=2,
        )
        
        assert is_valid is False
        assert error is not None
        assert any("cost" in str(f) for f in error.field_errors)
    
    def test_validate_row_with_negative_cost(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Row with negative cost should fail"""
        row_data = {
            "name": "Equipment 1",
            "cost": "-500.00",
            "quantity": 5,
        }
        is_valid, error = validation_service.validate_row_against_schema(
            row_data,
            asset_type_with_fields,
            row_number=2,
        )
        
        assert is_valid is False
        assert error is not None
    
    def test_validate_row_with_invalid_number_field(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Row with invalid number in required numeric field should fail"""
        row_data = {
            "name": "Equipment 1",
            "cost": "1000.00",
            "quantity": "not_a_number",
        }
        is_valid, error = validation_service.validate_row_against_schema(
            row_data,
            asset_type_with_fields,
            row_number=2,
        )
        
        assert is_valid is False
        assert error is not None
    
    def test_validate_row_with_out_of_range_number(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Row with number outside min/max range should fail"""
        row_data = {
            "name": "Equipment 1",
            "cost": "1000.00",
            "quantity": 5000,  # Max is 1000
        }
        is_valid, error = validation_service.validate_row_against_schema(
            row_data,
            asset_type_with_fields,
            row_number=2,
        )
        
        assert is_valid is False
        assert error is not None
    
    def test_validate_row_with_invalid_dropdown(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Row with invalid dropdown value should fail"""
        row_data = {
            "name": "Equipment 1",
            "cost": "1000.00",
            "quantity": 5,
            "status": "Invalid Option",
        }
        is_valid, error = validation_service.validate_row_against_schema(
            row_data,
            asset_type_with_fields,
            row_number=2,
        )
        
        assert is_valid is False
        assert error is not None
    
    def test_validate_row_with_valid_dropdown(
        self,
        validation_service: ImportValidationService,
        asset_type_with_fields: AssetType,
    ):
        """Row with valid dropdown value should pass"""
        row_data = {
            "name": "Equipment 1",
            "cost": "1000.00",
            "quantity": 5,
            "status": "New",
        }
        is_valid, error = validation_service.validate_row_against_schema(
            row_data,
            asset_type_with_fields,
            row_number=2,
        )
        
        assert is_valid is True
        assert error is None


class TestBudgetConstraintValidation:
    """Tests for budget constraint validation"""
    
    def test_validate_budget_within_remaining(
        self,
        validation_service: ImportValidationService,
        test_project: Project,
    ):
        """Import cost within remaining budget should pass"""
        # Project has $10000 budget, $2000 allocated, so $8000 remaining
        import_cost = 5000.00
        is_valid, error = validation_service.validate_budget_constraints(
            str(test_project.id),
            import_cost,
        )
        
        assert is_valid is True
        assert error is None
    
    def test_validate_budget_exceeds_remaining(
        self,
        validation_service: ImportValidationService,
        test_project: Project,
    ):
        """Import cost exceeding remaining budget should fail"""
        # Project has $10000 budget, $2000 allocated, so $8000 remaining
        import_cost = 9000.00
        is_valid, error = validation_service.validate_budget_constraints(
            str(test_project.id),
            import_cost,
        )
        
        assert is_valid is False
        assert error is not None
        assert "exceeds remaining budget" in error
    
    def test_validate_budget_exactly_remaining(
        self,
        validation_service: ImportValidationService,
        test_project: Project,
    ):
        """Import cost exactly equal to remaining budget should pass"""
        # Project has $10000 budget, $2000 allocated, so $8000 remaining
        import_cost = 8000.00
        is_valid, error = validation_service.validate_budget_constraints(
            str(test_project.id),
            import_cost,
        )
        
        assert is_valid is True
        assert error is None
    
    def test_validate_budget_invalid_project_id(
        self,
        validation_service: ImportValidationService,
    ):
        """Invalid project ID format should fail"""
        is_valid, error = validation_service.validate_budget_constraints(
            "invalid-uuid",
            1000.00,
        )
        
        assert is_valid is False
        assert "Invalid project ID format" in error
    
    def test_validate_budget_nonexistent_project(
        self,
        validation_service: ImportValidationService,
    ):
        """Non-existent project should fail"""
        fake_id = str(uuid4())
        is_valid, error = validation_service.validate_budget_constraints(
            fake_id,
            1000.00,
        )
        
        assert is_valid is False
        assert "not found" in error or "deleted" in error
    
    def test_validate_budget_inactive_project(
        self,
        db: Session,
        validation_service: ImportValidationService,
        test_user: User,
    ):
        """Inactive project should fail"""
        project = Project(
            name="Inactive Project",
            status=ProjectStatus.COMPLETED,
            budget=Decimal("10000.00"),
            allocated_budget=Decimal("0"),
            owner_id=test_user.id,
        )
        db.add(project)
        db.commit()
        
        is_valid, error = validation_service.validate_budget_constraints(
            str(project.id),
            1000.00,
        )
        
        assert is_valid is False
        assert "not active" in error


class TestBatchValidation:
    """Tests for batch import validation"""
    
    def test_validate_import_batch_all_valid(
        self,
        validation_service: ImportValidationService,
        test_project: Project,
        asset_type_with_fields: AssetType,
    ):
        """Batch with all valid rows should pass"""
        headers = ["name", "cost", "quantity"]
        rows = [
            {"name": "Equipment 1", "cost": "1000.00", "quantity": 5},
            {"name": "Equipment 2", "cost": "2000.00", "quantity": 3},
        ]
        
        is_valid, errors, valid_rows = validation_service.validate_import_batch(
            rows,
            asset_type_with_fields,
            str(test_project.id),
            headers,
        )
        
        assert is_valid is True
        assert len(errors) == 0
        assert len(valid_rows) == 2
    
    def test_validate_import_batch_some_invalid_rows(
        self,
        validation_service: ImportValidationService,
        test_project: Project,
        asset_type_with_fields: AssetType,
    ):
        """Batch with some invalid rows should return partial results"""
        headers = ["name", "cost", "quantity"]
        rows = [
            {"name": "Equipment 1", "cost": "1000.00", "quantity": 5},
            {"name": "", "cost": "2000.00", "quantity": 3},  # Invalid: empty name
            {"name": "Equipment 3", "cost": "500.00", "quantity": 2},
        ]
        
        is_valid, errors, valid_rows = validation_service.validate_import_batch(
            rows,
            asset_type_with_fields,
            str(test_project.id),
            headers,
        )
        
        assert is_valid is False
        assert len(errors) > 0
        assert len(valid_rows) == 2  # Two valid rows
    
    def test_validate_import_batch_invalid_headers(
        self,
        validation_service: ImportValidationService,
        test_project: Project,
        asset_type_with_fields: AssetType,
    ):
        """Batch with invalid headers should fail before row processing"""
        headers = ["cost", "quantity"]  # Missing 'name'
        rows = [
            {"cost": "1000.00", "quantity": 5},
        ]
        
        is_valid, errors, valid_rows = validation_service.validate_import_batch(
            rows,
            asset_type_with_fields,
            str(test_project.id),
            headers,
        )
        
        assert is_valid is False
        assert len(errors) > 0
        assert len(valid_rows) == 0
    
    def test_validate_import_batch_budget_exceeded(
        self,
        validation_service: ImportValidationService,
        test_project: Project,
        asset_type_with_fields: AssetType,
    ):
        """Batch exceeding budget should report budget error"""
        # Project has $8000 remaining
        headers = ["name", "cost", "quantity"]
        rows = [
            {"name": "Equipment 1", "cost": "6000.00", "quantity": 5},
            {"name": "Equipment 2", "cost": "3000.00", "quantity": 3},  # Total: $9000
        ]
        
        is_valid, errors, valid_rows = validation_service.validate_import_batch(
            rows,
            asset_type_with_fields,
            str(test_project.id),
            headers,
        )
        
        assert is_valid is False
        # Should have budget error
        assert any("budget" in str(e.general_error).lower() if e.general_error else False for e in errors)
        # Valid rows should still be returned
        assert len(valid_rows) == 2
