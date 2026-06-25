"""Import validation service for Excel file processing and resource validation"""
import logging
from typing import Dict, List, Tuple, Any, Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from app.models.asset_type import AssetType
from app.models.project import Project
from app.services.validation_service import SchemaValidator, ValidationResult


logger = logging.getLogger(__name__)


class ColumnHeaderValidationError:
    """Represents a column header validation error"""
    
    def __init__(self, column_name: str, error_message: str, column_index: int):
        self.column_name = column_name
        self.error_message = error_message
        self.column_index = column_index
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "column_name": self.column_name,
            "error_message": self.error_message,
            "column_index": self.column_index,
        }


class RowValidationError:
    """Represents a row-level validation error"""
    
    def __init__(
        self,
        row_number: int,
        field_errors: Optional[List[Dict[str, str]]] = None,
        general_error: Optional[str] = None,
    ):
        self.row_number = row_number
        self.field_errors = field_errors or []
        self.general_error = general_error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "row_number": self.row_number,
            "field_errors": self.field_errors,
            "general_error": self.general_error,
        }


class ImportValidationService:
    """Service for validating Excel import data"""
    
    def __init__(self, db: Session):
        """Initialize import validation service
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def validate_column_headers(
        self,
        headers: List[str],
        asset_type: AssetType,
    ) -> Tuple[bool, List[ColumnHeaderValidationError]]:
        """Validate column headers against asset type schema
        
        Checks that:
        - All required fields are present
        - Column names match field names (case-insensitive)
        - No duplicate columns
        - At least one column present
        
        Args:
            headers: List of column headers from Excel file
            asset_type: AssetType with defined schema
            
        Returns:
            Tuple of (is_valid: bool, errors: List[ColumnHeaderValidationError])
        """
        errors = []
        
        # Check if headers list is empty
        if not headers:
            errors.append(
                ColumnHeaderValidationError(
                    column_name="",
                    error_message="No columns found in Excel file",
                    column_index=0,
                )
            )
            return False, errors
        
        # Normalize headers to lowercase for comparison
        normalized_headers = {h.lower().strip(): (i, h) for i, h in enumerate(headers)}
        
        # Check for duplicate headers (case-insensitive)
        if len(normalized_headers) < len(headers):
            seen = {}
            for i, h in enumerate(headers):
                norm_h = h.lower().strip()
                if norm_h in seen:
                    errors.append(
                        ColumnHeaderValidationError(
                            column_name=h,
                            error_message=f"Duplicate column header (first occurrence at column {seen[norm_h] + 1})",
                            column_index=i,
                        )
                    )
                else:
                    seen[norm_h] = i
        
        # Build list of valid field names from asset type
        valid_field_names = {}
        
        # Standard fields for resources (always present)
        standard_fields = {"name", "cost"}  # Standard resource fields
        for field_name in standard_fields:
            valid_field_names[field_name.lower()] = field_name
        
        # Add custom fields from asset type
        for custom_field in asset_type.custom_fields:
            field_name_lower = custom_field.name.lower().strip()
            valid_field_names[field_name_lower] = custom_field.name
        
        # Check for required fields presence
        required_field_names = {"name"}  # Minimum required field
        missing_required_fields = []
        for required_field in required_field_names:
            if required_field.lower() not in normalized_headers:
                missing_required_fields.append(required_field)
        
        if missing_required_fields:
            for field in missing_required_fields:
                errors.append(
                    ColumnHeaderValidationError(
                        column_name=field,
                        error_message=f"Required column '{field}' not found in Excel file",
                        column_index=-1,
                    )
                )
        
        # Check for invalid/unrecognized columns
        for norm_header, (col_idx, original_header) in normalized_headers.items():
            if norm_header not in valid_field_names:
                errors.append(
                    ColumnHeaderValidationError(
                        column_name=original_header,
                        error_message=f"Column '{original_header}' is not a recognized field for asset type '{asset_type.name}'",
                        column_index=col_idx,
                    )
                )
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def validate_row_against_schema(
        self,
        row_data: Dict[str, Any],
        asset_type: AssetType,
        row_number: int,
    ) -> Tuple[bool, Optional[RowValidationError]]:
        """Validate a single row of data against asset type schema
        
        Checks:
        - Data types for each field
        - Required field validation
        - Custom field validation rules (min/max, regex, enum)
        - Cost is a valid number
        
        Args:
            row_data: Dictionary of field_name -> value
            asset_type: AssetType with schema definition
            row_number: Row number in Excel (for error reporting)
            
        Returns:
            Tuple of (is_valid: bool, error: Optional[RowValidationError])
        """
        field_errors = []
        
        # Validate standard fields
        # Check required field: name
        if not row_data.get("name") or (isinstance(row_data.get("name"), str) and row_data.get("name").strip() == ""):
            field_errors.append({
                "field_name": "name",
                "error_message": "Field 'name' is required and cannot be empty",
                "field_type": "text",
            })
        
        # Validate cost field if present (should be numeric)
        if "cost" in row_data and row_data["cost"] is not None:
            try:
                cost_value = float(row_data["cost"])
                if cost_value < 0:
                    field_errors.append({
                        "field_name": "cost",
                        "error_message": "Cost must be a positive number",
                        "field_type": "number",
                    })
            except (ValueError, TypeError):
                field_errors.append({
                    "field_name": "cost",
                    "error_message": f"Cost must be a valid number, got '{row_data['cost']}'",
                    "field_type": "number",
                })
        
        # Validate custom fields using SchemaValidator
        custom_field_values = {}
        for custom_field in asset_type.custom_fields:
            field_name = custom_field.name
            if field_name in row_data:
                custom_field_values[field_name] = row_data[field_name]
        
        # Run custom field validation
        validator = SchemaValidator(asset_type)
        validation_result = validator.validate(custom_field_values)
        
        if not validation_result.is_valid:
            for error in validation_result.errors:
                field_errors.append({
                    "field_name": error.field_name,
                    "error_message": error.error_message,
                    "field_type": error.field_type,
                })
        
        # Create error object if there are any field errors
        if field_errors:
            error = RowValidationError(
                row_number=row_number,
                field_errors=field_errors,
                general_error=None,
            )
            return False, error
        
        return True, None
    
    def validate_budget_constraints(
        self,
        project_id: str,
        total_cost: float,
    ) -> Tuple[bool, Optional[str]]:
        """Validate that import doesn't exceed project budget
        
        Checks:
        - Project exists and is not deleted
        - Project is active
        - Adding imported resources won't exceed budget
        
        Args:
            project_id: UUID of the project
            total_cost: Total cost of resources to be imported
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        # Fetch project
        import uuid as uuid_lib
        try:
            project_uuid = uuid_lib.UUID(project_id)
        except (ValueError, AttributeError):
            return False, f"Invalid project ID format: {project_id}"
        
        project = self.db.query(Project).filter(
            Project.id == project_uuid,
            Project.deleted_at.is_(None),
        ).first()
        
        if not project:
            return False, f"Project '{project_id}' not found or has been deleted"
        
        # Check if project is active
        if project.status != "Active":
            return False, f"Project '{project.name}' is not active and cannot receive new resources"
        
        # Calculate remaining budget
        remaining_budget = float(project.remaining_budget)
        total_cost_float = float(total_cost)
        
        if total_cost_float > remaining_budget:
            budget_shortfall = total_cost_float - remaining_budget
            return False, (
                f"Import total cost (${total_cost_float:.2f}) exceeds remaining budget "
                f"(${remaining_budget:.2f}). Shortfall: ${budget_shortfall:.2f}"
            )
        
        # Check if project is at or near capacity
        if project.utilization_percentage >= 100:
            return False, f"Project '{project.name}' has reached 100% budget utilization"
        
        return True, None
    
    def validate_import_batch(
        self,
        rows: List[Dict[str, Any]],
        asset_type: AssetType,
        project_id: str,
        headers: List[str],
        start_row: int = 2,
    ) -> Tuple[bool, List[RowValidationError], List[Dict[str, Any]]]:
        """Validate an entire batch of rows for import
        
        Performs:
        - Column header validation
        - Row-by-row schema validation
        - Budget constraint validation (total cost)
        - Returns valid rows for import and error list
        
        Args:
            rows: List of row dictionaries
            asset_type: AssetType with schema definition
            project_id: UUID of target project
            headers: Column headers from Excel file
            start_row: Starting row number for error reporting (default 2 for header row)
            
        Returns:
            Tuple of (all_valid: bool, errors: List[RowValidationError], valid_rows: List[Dict])
        """
        all_errors = []
        valid_rows = []
        
        # Step 1: Validate headers
        headers_valid, header_errors = self.validate_column_headers(headers, asset_type)
        
        if not headers_valid:
            # Convert header errors to row 1 error for reporting
            header_error_messages = [e.error_message for e in header_errors]
            error = RowValidationError(
                row_number=1,  # Header row
                field_errors=[],
                general_error="Headers validation failed: " + "; ".join(header_error_messages),
            )
            all_errors.append(error)
            return False, all_errors, []
        
        # Step 2: Validate each row
        total_cost = Decimal("0")
        for idx, row_data in enumerate(rows):
            row_number = start_row + idx
            is_valid, row_error = self.validate_row_against_schema(
                row_data,
                asset_type,
                row_number,
            )
            
            if not is_valid:
                all_errors.append(row_error)
            else:
                valid_rows.append(row_data)
                # Add cost to total for budget check
                if "cost" in row_data and row_data["cost"] is not None:
                    try:
                        total_cost += Decimal(str(row_data["cost"]))
                    except:
                        pass
        
        # Step 3: Validate budget constraints for valid rows
        if valid_rows:
            budget_valid, budget_error = self.validate_budget_constraints(
                project_id,
                float(total_cost),
            )
            
            if not budget_valid:
                error = RowValidationError(
                    row_number=-1,  # Global budget error
                    field_errors=[],
                    general_error=budget_error,
                )
                all_errors.append(error)
                # Note: We don't clear valid_rows here - caller can decide whether to
                # proceed with partial import or fail entirely
        
        is_all_valid = len(all_errors) == 0
        return is_all_valid, all_errors, valid_rows


def get_import_validation_service(db: Session) -> ImportValidationService:
    """Factory function to create ImportValidationService
    
    Args:
        db: SQLAlchemy database session
        
    Returns:
        ImportValidationService instance
    """
    return ImportValidationService(db)
