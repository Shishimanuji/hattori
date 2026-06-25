"""Import request/response schemas"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime


class ValidationError(BaseModel):
    """Validation error details for a specific row"""
    row_number: int = Field(..., description="1-indexed row number in Excel file")
    column_name: str = Field(..., description="Name of the column with error")
    error_message: str = Field(..., description="Description of the validation error")


class RowValidationStatus(BaseModel):
    """Validation status for a single row"""
    row_number: int = Field(..., description="1-indexed row number in Excel file (2 = first data row)")
    has_errors: bool = Field(..., description="Whether this row has validation errors")
    errors: List[ValidationError] = Field(default_factory=list, description="List of validation errors")


class ImportPreviewResponse(BaseModel):
    """Response from import preview endpoint"""
    status: str = Field(..., description="Status: 'success' or 'error'")
    
    # File information
    headers: List[str] = Field(..., description="Column headers from Excel file")
    total_rows: int = Field(..., description="Total number of data rows in Excel file")
    
    # Preview data
    preview_data: List[Dict[str, Any]] = Field(
        ...,
        description="First 100 rows of data from Excel file"
    )
    
    # Validation results
    validation_status: Dict[str, Any] = Field(
        ...,
        description="Validation summary including error counts"
    )
    
    # Error details
    sample_errors: List[ValidationError] = Field(
        default_factory=list,
        description="Sample validation errors found (up to 10 most critical)"
    )
    
    # Optional error message if status is 'error'
    error_message: Optional[str] = Field(
        None,
        description="Error message if preview failed"
    )


class ImportPreviewValidationStatus(BaseModel):
    """Validation status summary"""
    total_rows: int = Field(..., description="Total rows to import")
    rows_with_errors: int = Field(..., description="Number of rows with validation errors")
    error_count: int = Field(..., description="Total number of errors found")
    warning_count: int = Field(..., description="Total number of warnings")
    required_columns_present: bool = Field(..., description="Whether all required columns are present")
    missing_columns: List[str] = Field(default_factory=list, description="Required columns that are missing")


class ColumnMappingInfo(BaseModel):
    """Information about column to field mapping"""
    excel_column: str = Field(..., description="Column name from Excel file")
    asset_type_field: Optional[str] = Field(None, description="Matched asset type field name")
    field_type: Optional[str] = Field(None, description="Field type (text, number, date, etc.)")
    is_required: Optional[bool] = Field(None, description="Whether this field is required")
    mapping_confidence: str = Field(default="exact", description="exact, fuzzy, or none")
