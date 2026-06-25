"""Excel import service with validation logic"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.asset_type import AssetType, CustomField, FieldType
from app.models.project import Project
from app.utils.excel_utils import ExcelParser, ExcelParsingError
from app.services.validation_service import ValidationService

logger = logging.getLogger(__name__)


class ImportService:
    """Service for Excel import operations including preview and validation"""
    
    @staticmethod
    def get_asset_type_schema(db: Session, asset_type_id: UUID) -> Dict[str, Any]:
        """
        Retrieve asset type schema with all custom fields.
        
        Args:
            db: Database session
            asset_type_id: UUID of the asset type
            
        Returns:
            Dictionary containing asset type info and custom fields
            
        Raises:
            ValueError: If asset type not found or is inactive
        """
        asset_type = db.query(AssetType).filter(
            AssetType.id == asset_type_id,
            AssetType.is_active == True
        ).first()
        
        if not asset_type:
            raise ValueError(f"Asset type {asset_type_id} not found or is inactive")
        
        # Get custom fields
        custom_fields = db.query(CustomField).filter(
            CustomField.asset_type_id == asset_type_id
        ).order_by(CustomField.display_order).all()
        
        # Standard fields that are always present
        standard_fields = [
            {'name': 'name', 'field_type': 'text', 'is_required': True},
            {'name': 'cost', 'field_type': 'number', 'is_required': True},
            {'name': 'allocation_date', 'field_type': 'date', 'is_required': True},
        ]
        
        # Build complete field list
        all_fields = standard_fields.copy()
        for field in custom_fields:
            all_fields.append({
                'id': str(field.id),
                'name': field.name,
                'field_type': field.field_type,
                'is_required': field.is_required,
                'options': field.options,
                'validation_rules': field.validation_rules,
            })
        
        return {
            'asset_type_id': str(asset_type_id),
            'asset_type_name': asset_type.name,
            'fields': all_fields,
            'required_fields': [f['name'] for f in all_fields if f.get('is_required')]
        }
    
    @staticmethod
    def validate_excel_column_mapping(
        headers: List[str],
        required_fields: List[str],
        all_fields: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Optional[Dict[str, Any]]], List[str]]:
        """
        Validate that Excel columns map to required asset type fields.
        
        Args:
            headers: List of Excel column headers
            required_fields: List of required field names
            all_fields: List of all available field definitions
            
        Returns:
            Tuple of:
            - column_mapping: Dict mapping Excel columns to field definitions
            - missing_columns: List of required columns not found in Excel
        """
        column_mapping = {}
        missing_columns = []
        
        # Map each Excel column to a field
        for header in headers:
            if header:  # Skip empty headers
                matched_field = ExcelParser.match_column_to_field(header, all_fields)
                column_mapping[header] = matched_field
        
        # Check for missing required columns
        for required_field in required_fields:
            found = False
            for header, field in column_mapping.items():
                if field and field['name'] == required_field:
                    found = True
                    break
            if not found:
                missing_columns.append(required_field)
        
        return column_mapping, missing_columns
    
    @staticmethod
    def validate_row_data(
        row_data: Dict[str, Any],
        column_mapping: Dict[str, Optional[Dict[str, Any]]],
        row_number: int
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate a single row of data against the column mapping.
        
        Args:
            row_data: Dictionary of column name -> value from Excel
            column_mapping: Mapping of Excel columns to field definitions
            row_number: Row number in Excel file (for error reporting)
            
        Returns:
            Tuple of:
            - is_valid: Whether row passed validation
            - errors: List of validation error dictionaries
        """
        errors = []
        
        for column_name, value in row_data.items():
            field_def = column_mapping.get(column_name)
            
            if not field_def:
                # Column doesn't map to any field, skip
                continue
            
            field_name = field_def.get('name')
            field_type = field_def.get('field_type')
            is_required = field_def.get('is_required', False)
            validation_rules = field_def.get('validation_rules', {})
            options = field_def.get('options')
            
            # Check required field
            if is_required and (value is None or str(value).strip() == ''):
                errors.append({
                    'row_number': row_number,
                    'column_name': column_name,
                    'error_message': f"Required field '{field_name}' is missing"
                })
                continue
            
            # Skip validation if value is empty and not required
            if value is None or str(value).strip() == '':
                continue
            
            # Type-specific validation
            type_error = ImportService._validate_field_type(
                value=value,
                field_type=field_type,
                field_name=field_name,
                row_number=row_number,
                column_name=column_name,
                validation_rules=validation_rules,
                options=options
            )
            
            if type_error:
                errors.append(type_error)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    def _validate_field_type(
        value: Any,
        field_type: str,
        field_name: str,
        row_number: int,
        column_name: str,
        validation_rules: Optional[Dict[str, Any]] = None,
        options: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Validate a field value according to its type and validation rules.
        
        Args:
            value: The value to validate
            field_type: The field type (text, number, date, dropdown, boolean)
            field_name: Name of the field (for error messages)
            row_number: Row number in Excel (for error messages)
            column_name: Column name in Excel (for error messages)
            validation_rules: Optional validation rules dictionary
            options: Options for dropdown fields
            
        Returns:
            Error dictionary if validation fails, None if valid
        """
        validation_rules = validation_rules or {}
        
        try:
            if field_type == 'text':
                # Text validation
                str_value = str(value).strip()
                if not str_value:
                    return {
                        'row_number': row_number,
                        'column_name': column_name,
                        'error_message': f"'{field_name}' cannot be empty"
                    }
                
                # Check min/max length
                min_length = validation_rules.get('min_length')
                max_length = validation_rules.get('max_length')
                
                if min_length and len(str_value) < min_length:
                    return {
                        'row_number': row_number,
                        'column_name': column_name,
                        'error_message': f"'{field_name}' must be at least {min_length} characters"
                    }
                
                if max_length and len(str_value) > max_length:
                    return {
                        'row_number': row_number,
                        'column_name': column_name,
                        'error_message': f"'{field_name}' must not exceed {max_length} characters"
                    }
                
                # Check regex pattern if provided
                pattern = validation_rules.get('pattern')
                if pattern:
                    import re
                    if not re.match(pattern, str_value):
                        return {
                            'row_number': row_number,
                            'column_name': column_name,
                            'error_message': f"'{field_name}' does not match required format"
                        }
                
            elif field_type == 'number':
                # Number validation
                try:
                    num_value = Decimal(str(value))
                except (ValueError, TypeError):
                    return {
                        'row_number': row_number,
                        'column_name': column_name,
                        'error_message': f"'{field_name}' must be a valid number"
                    }
                
                # Check min/max
                min_value = validation_rules.get('min_value')
                max_value = validation_rules.get('max_value')
                
                if min_value is not None and num_value < Decimal(str(min_value)):
                    return {
                        'row_number': row_number,
                        'column_name': column_name,
                        'error_message': f"'{field_name}' must be at least {min_value}"
                    }
                
                if max_value is not None and num_value > Decimal(str(max_value)):
                    return {
                        'row_number': row_number,
                        'column_name': column_name,
                        'error_message': f"'{field_name}' must not exceed {max_value}"
                    }
                
            elif field_type == 'date':
                # Date validation
                from datetime import datetime as dt
                date_value = None
                
                # Try parsing various date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y']:
                    try:
                        if isinstance(value, str):
                            date_value = dt.strptime(value.strip(), fmt).date()
                            break
                        else:
                            # If it's already a date object from Excel
                            if hasattr(value, 'date'):
                                date_value = value.date()
                            else:
                                date_value = dt.fromisoformat(str(value)).date()
                            break
                    except (ValueError, AttributeError):
                        continue
                
                if not date_value:
                    return {
                        'row_number': row_number,
                        'column_name': column_name,
                        'error_message': f"'{field_name}' is not a valid date (use YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY)"
                    }
                
            elif field_type == 'dropdown':
                # Dropdown validation - value must be in options
                str_value = str(value).strip()
                if options and str_value not in options:
                    return {
                        'row_number': row_number,
                        'column_name': column_name,
                        'error_message': f"'{field_name}' must be one of: {', '.join(options)}"
                    }
                
            elif field_type == 'boolean':
                # Boolean validation
                str_value = str(value).strip().lower()
                if str_value not in ['true', 'false', 'yes', 'no', '1', '0']:
                    return {
                        'row_number': row_number,
                        'column_name': column_name,
                        'error_message': f"'{field_name}' must be true/false or yes/no"
                    }
        
        except Exception as e:
            logger.error(f"Unexpected error validating field {field_name}: {str(e)}", exc_info=True)
            return {
                'row_number': row_number,
                'column_name': column_name,
                'error_message': f"Error validating '{field_name}': {str(e)}"
            }
        
        return None
    
    @staticmethod
    def preview_excel_import(
        file_content: bytes,
        filename: str,
        asset_type_id: UUID,
        project_id: UUID,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate a preview of Excel import with validation.
        
        Args:
            file_content: Binary content of Excel file
            filename: Name of the uploaded file
            asset_type_id: UUID of asset type for validation
            project_id: UUID of project to import into
            db: Database session
            
        Returns:
            Dictionary containing preview data and validation results
        """
        try:
            # Validate file format
            ExcelParser.validate_file_format(filename)
            
            # Parse Excel file
            headers, preview_rows, total_rows = ExcelParser.read_excel_file(file_content)
            
            # Verify project exists
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Get asset type schema
            schema = ImportService.get_asset_type_schema(db, asset_type_id)
            
            # Map columns to fields
            column_mapping, missing_columns = ImportService.validate_excel_column_mapping(
                headers=headers,
                required_fields=schema['required_fields'],
                all_fields=schema['fields']
            )
            
            # Validate all preview rows
            all_errors = []
            rows_with_errors = 0
            validated_rows = []
            
            for row_idx, row_data in enumerate(preview_rows, start=2):  # Excel row 2 is first data row
                is_valid, row_errors = ImportService.validate_row_data(
                    row_data=row_data,
                    column_mapping=column_mapping,
                    row_number=row_idx
                )
                
                if not is_valid:
                    rows_with_errors += 1
                    all_errors.extend(row_errors)
                
                validated_rows.append(row_data)
            
            # Build validation status
            validation_status = {
                'total_rows': total_rows,
                'rows_with_errors': rows_with_errors,
                'error_count': len(all_errors),
                'warning_count': 0,
                'required_columns_present': len(missing_columns) == 0,
                'missing_columns': missing_columns
            }
            
            # Get sample of top errors (first 10)
            sample_errors = all_errors[:10]
            
            return {
                'status': 'success',
                'headers': headers,
                'total_rows': total_rows,
                'preview_data': validated_rows,
                'validation_status': validation_status,
                'sample_errors': sample_errors,
                'error_message': None
            }
        
        except ExcelParsingError as e:
            logger.warning(f"Excel parsing error: {str(e)}")
            return {
                'status': 'error',
                'headers': [],
                'total_rows': 0,
                'preview_data': [],
                'validation_status': {
                    'total_rows': 0,
                    'rows_with_errors': 0,
                    'error_count': 0,
                    'warning_count': 0,
                    'required_columns_present': False,
                    'missing_columns': []
                },
                'sample_errors': [],
                'error_message': f"Failed to parse Excel file: {str(e)}"
            }
        
        except ValueError as e:
            logger.warning(f"Validation error: {str(e)}")
            return {
                'status': 'error',
                'headers': [],
                'total_rows': 0,
                'preview_data': [],
                'validation_status': {
                    'total_rows': 0,
                    'rows_with_errors': 0,
                    'error_count': 0,
                    'warning_count': 0,
                    'required_columns_present': False,
                    'missing_columns': []
                },
                'sample_errors': [],
                'error_message': str(e)
            }
        
        except Exception as e:
            logger.error(f"Unexpected error in preview_excel_import: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'headers': [],
                'total_rows': 0,
                'preview_data': [],
                'validation_status': {
                    'total_rows': 0,
                    'rows_with_errors': 0,
                    'error_count': 0,
                    'warning_count': 0,
                    'required_columns_present': False,
                    'missing_columns': []
                },
                'sample_errors': [],
                'error_message': f"Internal error: {str(e)}"
            }
