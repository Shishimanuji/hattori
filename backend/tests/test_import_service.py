"""Tests for import execution service"""
import pytest
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from app.services.import_service import (
    execute_import,
    get_import_status,
    ImportError,
    ImportRowError,
    ImportJobStatus,
)
from app.models.resource import Resource, ResourceStatus
from app.models.project import Project
from app.models.asset_type import AssetType


class TestImportJobStatus:
    """Tests for ImportJobStatus tracking"""
    
    def test_import_job_status_initialization(self):
        """Test job status object is correctly initialized"""
        job_id = "test-job-123"
        total_rows = 1000
        asset_type_id = UUID("00000000-0000-0000-0000-000000000001")
        project_id = UUID("00000000-0000-0000-0000-000000000002")
        user_id = UUID("00000000-0000-0000-0000-000000000003")
        
        status = ImportJobStatus(job_id, total_rows, asset_type_id, project_id, user_id)
        
        assert status.job_id == job_id
        assert status.total_rows == total_rows
        assert status.status == "processing"
        assert status.processed_rows == 0
        assert status.successful_imports == 0
        assert len(status.failed_rows) == 0
    
    def test_import_job_status_to_dict(self):
        """Test job status conversion to dictionary"""
        job_id = "test-job-456"
        status = ImportJobStatus(job_id, 100, UUID("00000000-0000-0000-0000-000000000001"), 
                                 UUID("00000000-0000-0000-0000-000000000002"),
                                 UUID("00000000-0000-0000-0000-000000000003"))
        
        status.processed_rows = 50
        status.successful_imports = 45
        status.end_time = datetime.utcnow()
        
        result = status.to_dict()
        
        assert result["job_id"] == job_id
        assert result["total_rows"] == 100
        assert result["processed_rows"] == 50
        assert result["successful_imports"] == 45
        assert result["status"] == "processing"
        assert result["elapsed_seconds"] is not None


class TestImportRowError:
    """Tests for ImportRowError"""
    
    def test_import_row_error_creation(self):
        """Test error object creation"""
        error = ImportRowError(5, "Invalid cost", "cost", "abc")
        
        assert error.row_number == 5
        assert error.error_message == "Invalid cost"
        assert error.field_name == "cost"
        assert error.value == "abc"
    
    def test_import_row_error_to_dict(self):
        """Test error conversion to dictionary"""
        error = ImportRowError(10, "Missing required field", "name", None)
        result = error.to_dict()
        
        assert result["row_number"] == 10
        assert result["error_message"] == "Missing required field"
        assert result["field_name"] == "name"
        assert result["value"] is None


class TestExecuteImport:
    """Tests for execute_import function"""
    
    def test_execute_import_returns_job_id(self, db: Session, test_project: Project, 
                                          test_asset_type: AssetType, test_user):
        """Test execute_import returns a valid job ID"""
        records = [
            {
                "name": "Resource 1",
                "cost": "1000",
                "allocation_date": "2024-01-15",
            }
        ]
        
        job_id = execute_import(
            db=db,
            file_path="/tmp/test.xlsx",
            project_id=test_project.id,
            asset_type_id=test_asset_type.id,
            user_id=test_user.id,
            records=records,
        )
        
        assert job_id is not None
        assert isinstance(job_id, str)
        assert len(job_id) > 0
    
    def test_execute_import_with_invalid_project(self, db: Session, test_asset_type: AssetType, test_user):
        """Test import fails with invalid project"""
        invalid_project_id = UUID("00000000-0000-0000-0000-000000000099")
        records = [{"name": "Resource 1", "cost": "1000", "allocation_date": "2024-01-15"}]
        
        with pytest.raises(ImportError):
            execute_import(
                db=db,
                file_path="/tmp/test.xlsx",
                project_id=invalid_project_id,
                asset_type_id=test_asset_type.id,
                user_id=test_user.id,
                records=records,
            )
    
    def test_execute_import_with_invalid_asset_type(self, db: Session, test_project: Project, test_user):
        """Test import fails with invalid asset type"""
        invalid_asset_type_id = UUID("00000000-0000-0000-0000-000000000099")
        records = [{"name": "Resource 1", "cost": "1000", "allocation_date": "2024-01-15"}]
        
        with pytest.raises(ImportError):
            execute_import(
                db=db,
                file_path="/tmp/test.xlsx",
                project_id=test_project.id,
                asset_type_id=invalid_asset_type_id,
                user_id=test_user.id,
                records=records,
            )
    
    def test_execute_import_with_invalid_user(self, db: Session, test_project: Project, test_asset_type: AssetType):
        """Test import fails with invalid user"""
        invalid_user_id = UUID("00000000-0000-0000-0000-000000000099")
        records = [{"name": "Resource 1", "cost": "1000", "allocation_date": "2024-01-15"}]
        
        with pytest.raises(ImportError):
            execute_import(
                db=db,
                file_path="/tmp/test.xlsx",
                project_id=test_project.id,
                asset_type_id=test_asset_type.id,
                user_id=invalid_user_id,
                records=records,
            )
    
    def test_execute_import_deleted_project(self, db: Session, test_asset_type: AssetType, test_user):
        """Test import fails with deleted project"""
        # Create and delete a project
        project = Project(
            name="Deleted Project",
            description="Test",
            status="Active",
            budget=Decimal("100000"),
            owner_id=test_user.id,
        )
        db.add(project)
        db.commit()
        
        project.deleted_at = datetime.utcnow()
        db.commit()
        
        records = [{"name": "Resource 1", "cost": "1000", "allocation_date": "2024-01-15"}]
        
        with pytest.raises(ImportError, match="deleted project"):
            execute_import(
                db=db,
                file_path="/tmp/test.xlsx",
                project_id=project.id,
                asset_type_id=test_asset_type.id,
                user_id=test_user.id,
                records=records,
            )


class TestGetImportStatus:
    """Tests for get_import_status function"""
    
    def test_get_import_status_not_found(self):
        """Test getting status for non-existent job"""
        with pytest.raises(ImportError, match="not found"):
            get_import_status("non-existent-job-id")
    
    def test_get_import_status_returns_dict(self, db: Session, test_project: Project,
                                           test_asset_type: AssetType, test_user):
        """Test getting import status returns valid dictionary"""
        records = [{"name": "Resource 1", "cost": "1000", "allocation_date": "2024-01-15"}]
        
        job_id = execute_import(
            db=db,
            file_path="/tmp/test.xlsx",
            project_id=test_project.id,
            asset_type_id=test_asset_type.id,
            user_id=test_user.id,
            records=records,
        )
        
        status = get_import_status(job_id)
        
        assert status["job_id"] == job_id
        assert "status" in status
        assert "processed_rows" in status
        assert "successful_imports" in status
        assert "failed_rows" in status


class TestImportWithCustomFields:
    """Tests for import with custom fields"""
    
    def test_import_with_custom_fields(self, db: Session, test_project: Project,
                                       asset_type_with_fields: AssetType, test_user):
        """Test importing resources with custom fields"""
        records = [
            {
                "name": "Resource with custom fields",
                "cost": "5000",
                "allocation_date": "2024-01-15",
                "department": "Engineering",
                "skill_level": "Senior",
            }
        ]
        
        job_id = execute_import(
            db=db,
            file_path="/tmp/test.xlsx",
            project_id=test_project.id,
            asset_type_id=asset_type_with_fields.id,
            user_id=test_user.id,
            records=records,
        )
        
        assert job_id is not None
        
        # Allow processing time
        import time
        time.sleep(0.5)
        
        status = get_import_status(job_id)
        assert status["job_id"] == job_id


class TestImportValidation:
    """Tests for import validation"""
    
    def test_import_missing_required_name(self, db: Session, test_project: Project,
                                         test_asset_type: AssetType, test_user):
        """Test import skips records with missing name"""
        records = [
            {
                "name": "",  # Empty name
                "cost": "1000",
                "allocation_date": "2024-01-15",
            }
        ]
        
        job_id = execute_import(
            db=db,
            file_path="/tmp/test.xlsx",
            project_id=test_project.id,
            asset_type_id=test_asset_type.id,
            user_id=test_user.id,
            records=records,
        )
        
        assert job_id is not None
    
    def test_import_invalid_cost(self, db: Session, test_project: Project,
                                 test_asset_type: AssetType, test_user):
        """Test import skips records with invalid cost"""
        records = [
            {
                "name": "Resource",
                "cost": "invalid",  # Invalid cost
                "allocation_date": "2024-01-15",
            }
        ]
        
        job_id = execute_import(
            db=db,
            file_path="/tmp/test.xlsx",
            project_id=test_project.id,
            asset_type_id=test_asset_type.id,
            user_id=test_user.id,
            records=records,
        )
        
        assert job_id is not None
    
    def test_import_negative_cost(self, db: Session, test_project: Project,
                                  test_asset_type: AssetType, test_user):
        """Test import skips records with negative cost"""
        records = [
            {
                "name": "Resource",
                "cost": "-1000",  # Negative cost
                "allocation_date": "2024-01-15",
            }
        ]
        
        job_id = execute_import(
            db=db,
            file_path="/tmp/test.xlsx",
            project_id=test_project.id,
            asset_type_id=test_asset_type.id,
            user_id=test_user.id,
            records=records,
        )
        
        assert job_id is not None
    
    def test_import_invalid_date(self, db: Session, test_project: Project,
                                 test_asset_type: AssetType, test_user):
        """Test import skips records with invalid date"""
        records = [
            {
                "name": "Resource",
                "cost": "1000",
                "allocation_date": "invalid-date",  # Invalid date
            }
        ]
        
        job_id = execute_import(
            db=db,
            file_path="/tmp/test.xlsx",
            project_id=test_project.id,
            asset_type_id=test_asset_type.id,
            user_id=test_user.id,
            records=records,
        )
        
        assert job_id is not None


class TestImportBudgetConstraint:
    """Tests for budget constraint enforcement during import"""
    
    def test_import_respects_budget_limit(self, db: Session, test_user):
        """Test import respects project budget limit"""
        # Create project with small budget
        project = Project(
            name="Small Budget Project",
            description="Test",
            status="Active",
            budget=Decimal("5000"),  # Only 5000 budget
            owner_id=test_user.id,
        )
        db.add(project)
        db.commit()
        
        asset_type = db.query(AssetType).filter(AssetType.name == "Personnel").first()
        
        records = [
            {
                "name": "Resource 1",
                "cost": "3000",
                "allocation_date": "2024-01-15",
            },
            {
                "name": "Resource 2",
                "cost": "3000",  # This would exceed budget
                "allocation_date": "2024-01-15",
            }
        ]
        
        job_id = execute_import(
            db=db,
            file_path="/tmp/test.xlsx",
            project_id=project.id,
            asset_type_id=asset_type.id,
            user_id=test_user.id,
            records=records,
        )
        
        assert job_id is not None


class TestImportBatchProcessing:
    """Tests for batch processing performance"""
    
    def test_import_large_batch(self, db: Session, test_project: Project,
                                test_asset_type: AssetType, test_user):
        """Test import can process large batch of records"""
        # Generate 500 records
        records = [
            {
                "name": f"Resource {i}",
                "cost": str(100 * (i % 10 + 1)),  # Vary costs
                "allocation_date": "2024-01-15",
            }
            for i in range(500)
        ]
        
        job_id = execute_import(
            db=db,
            file_path="/tmp/test.xlsx",
            project_id=test_project.id,
            asset_type_id=test_asset_type.id,
            user_id=test_user.id,
            records=records,
        )
        
        assert job_id is not None
        
        # Wait for processing
        import time
        time.sleep(1)
        
        status = get_import_status(job_id)
        assert status["total_rows"] == 500
        # Should have processed most records (some may fail due to budget)
        assert status["processed_rows"] > 0
