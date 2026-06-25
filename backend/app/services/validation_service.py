"""Validation service for custom field validation during resource creation/update"""
import re
from typing import List, Optional, Any, Dict
from datetime import datetime
from decimal import Decimal

from app.models.asset_type import AssetType, CustomField, FieldType


class ValidationError:
    """Represents a single field validation error"""
    
    def __init__(
        self,
        field_name: str,
        field_type: str,
        error_message: str,
        rule_violated: str,
    ):
        self.field_name = field_name
        self.field_type = field_type
        self.error_message = error_message
        self.rule_violated = rule_violated
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "field_name": self.field_name,
            "field_type": self.field_type,
            "error_message": self.error_message,
            "rule_violated": self.rule_violated,
        }


class ValidationResult:
    """Result of schema validation containing validation status and errors"""
    
    def __init__(self, is_valid: bool = True, errors: Optional[List[ValidationError]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "is_valid": self.is_valid,
            "errors": [error.to_dict() for error in self.errors],
        }


class SchemaValidator:
    """Validates custom field values against asset type schema"""
    
    def __init__(self, asset_type: AssetType):
        """Initialize validator with asset type schema
        
        Args:
            asset_type: AssetType model containing custom field definitions
        """
        self.asset_type = asset_type
        self.custom_fields = {cf.name: cf for cf in asset_type.custom_fields}
    
    def validate(self, custom_field_values: Dict[str, Any]) -> ValidationResult:
        """Validate custom field values against asset type schema
        
        Args:
            custom_field_values: Dictionary of field name -> value
            
        Returns:
            ValidationResult with is_valid flag and list of errors
        """
        errors = []
        
        # Validate each custom field
        for field_def in self.asset_type.custom_fields:
            field_name = field_def.name
            field_value = custom_field_values.get(field_name)
            field_type = FieldType(field_def.field_type)
            
            # Validate this field
            field_errors = self._validate_field(
                field_name=field_name,
                field_value=field_value,
                field_type=field_type,
                field_config=field_def,
            )
            errors.extend(field_errors)
        
        # Return result
        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors)
    
    def _validate_field(
        self,
        field_name: str,
        field_value: Any,
        field_type: FieldType,
        field_config: CustomField,
    ) -> List[ValidationError]:
        """Validate a single field based on its type and configuration
        
        Args:
            field_name: Name of the field
            field_value: Value to validate
            field_type: Type of field (text, number, date, dropdown, boolean)
            field_config: CustomField configuration
            
        Returns:
            List of ValidationError objects (empty if valid)
        """
        # Dispatch to appropriate validator
        if field_type == FieldType.TEXT:
            return validate_text_field(field_name, field_type, field_config, field_value)
        elif field_type == FieldType.NUMBER:
            return validate_number_field(field_name, field_type, field_config, field_value)
        elif field_type == FieldType.DATE:
            return validate_date_field(field_name, field_type, field_config, field_value)
        elif field_type == FieldType.DROPDOWN:
            return validate_dropdown_field(field_name, field_type, field_config, field_value)
        elif field_type == FieldType.BOOLEAN:
            return validate_boolean_field(field_name, field_type, field_config, field_value)
        else:
            return [
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"Unknown field type: {field_type.value}",
                    rule_violated="unknown_type",
                )
            ]


def validate_text_field(
    field_name: str,
    field_type: FieldType,
    field_config: CustomField,
    field_value: Any,
) -> List[ValidationError]:
    """Validate a text field
    
    Validates:
    - Required: field must have a value
    - Min length: text must be at least N characters
    - Max length: text must be at most N characters
    - Regex: text must match pattern
    
    Args:
        field_name: Name of the field
        field_type: FieldType enum
        field_config: CustomField configuration
        field_value: Value to validate
        
    Returns:
        List of ValidationError objects
    """
    errors = []
    validation_rules = field_config.validation_rules or {}
    
    # Check if field is required
    is_required = field_config.is_required
    
    # Handle null/empty values
    if field_value is None or (isinstance(field_value, str) and field_value.strip() == ""):
        if is_required:
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"'{field_name}' is required",
                    rule_violated="required",
                )
            )
        return errors  # No further validation if empty and not required
    
    # Convert to string
    str_value = str(field_value).strip() if field_value is not None else ""
    
    # Validate min length
    if "min" in validation_rules and validation_rules["min"] is not None:
        min_length = validation_rules["min"]
        if len(str_value) < min_length:
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"'{field_name}' must be at least {min_length} characters",
                    rule_violated="min",
                )
            )
    
    # Validate max length
    if "max" in validation_rules and validation_rules["max"] is not None:
        max_length = validation_rules["max"]
        if len(str_value) > max_length:
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"'{field_name}' must be at most {max_length} characters",
                    rule_violated="max",
                )
            )
    
    # Validate regex pattern
    if "regex" in validation_rules and validation_rules["regex"] is not None:
        pattern = validation_rules["regex"]
        try:
            if not re.match(pattern, str_value):
                errors.append(
                    ValidationError(
                        field_name=field_name,
                        field_type=field_type.value,
                        error_message=f"'{field_name}' does not match required pattern: {pattern}",
                        rule_violated="regex",
                    )
                )
        except re.error as e:
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"Invalid regex pattern for '{field_name}': {str(e)}",
                    rule_violated="regex_error",
                )
            )
    
    return errors


def validate_number_field(
    field_name: str,
    field_type: FieldType,
    field_config: CustomField,
    field_value: Any,
) -> List[ValidationError]:
    """Validate a number field
    
    Validates:
    - Required: field must have a value
    - Min value: number must be >= N
    - Max value: number must be <= N
    
    Args:
        field_name: Name of the field
        field_type: FieldType enum
        field_config: CustomField configuration
        field_value: Value to validate
        
    Returns:
        List of ValidationError objects
    """
    errors = []
    validation_rules = field_config.validation_rules or {}
    
    # Check if field is required
    is_required = field_config.is_required
    
    # Handle null values
    if field_value is None:
        if is_required:
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"'{field_name}' is required",
                    rule_violated="required",
                )
            )
        return errors
    
    # Try to convert to float
    try:
        num_value = float(field_value)
    except (ValueError, TypeError):
        errors.append(
            ValidationError(
                field_name=field_name,
                field_type=field_type.value,
                error_message=f"'{field_name}' must be a valid number",
                rule_violated="invalid_number",
            )
        )
        return errors
    
    # Validate min value
    if "min" in validation_rules and validation_rules["min"] is not None:
        min_val = float(validation_rules["min"])
        if num_value < min_val:
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"'{field_name}' must be at least {min_val}",
                    rule_violated="min",
                )
            )
    
    # Validate max value
    if "max" in validation_rules and validation_rules["max"] is not None:
        max_val = float(validation_rules["max"])
        if num_value > max_val:
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"'{field_name}' must be at most {max_val}",
                    rule_violated="max",
                )
            )
    
    return errors


def validate_date_field(
    field_name: str,
    field_type: FieldType,
    field_config: CustomField,
    field_value: Any,
) -> List[ValidationError]:
    """Validate a date field
    
    Validates:
    - Required: field must have a value
    - Valid date format: must be parseable as date (ISO format or datetime object)
    - Min date: date must be >= N
    - Max date: date must be <= N
    
    Args:
        field_name: Name of the field
        field_type: FieldType enum
        field_config: CustomField configuration
        field_value: Value to validate (datetime object or ISO string)
        
    Returns:
        List of ValidationError objects
    """
    errors = []
    validation_rules = field_config.validation_rules or {}
    
    # Check if field is required
    is_required = field_config.is_required
    
    # Handle null values
    if field_value is None:
        if is_required:
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"'{field_name}' is required",
                    rule_violated="required",
                )
            )
        return errors
    
    # Try to convert to datetime
    try:
        if isinstance(field_value, datetime):
            date_value = field_value.date()
        elif isinstance(field_value, str):
            # Try ISO format
            date_value = datetime.fromisoformat(field_value.replace('Z', '+00:00')).date()
        else:
            raise ValueError(f"Cannot parse {field_value} as date")
    except (ValueError, TypeError) as e:
        errors.append(
            ValidationError(
                field_name=field_name,
                field_type=field_type.value,
                error_message=f"'{field_name}' must be a valid date (ISO format)",
                rule_violated="invalid_date",
            )
        )
        return errors
    
    # Validate min date
    if "min" in validation_rules and validation_rules["min"] is not None:
        try:
            if isinstance(validation_rules["min"], str):
                min_date = datetime.fromisoformat(validation_rules["min"].replace('Z', '+00:00')).date()
            else:
                min_date = validation_rules["min"]
            
            if date_value < min_date:
                errors.append(
                    ValidationError(
                        field_name=field_name,
                        field_type=field_type.value,
                        error_message=f"'{field_name}' must be on or after {min_date}",
                        rule_violated="min",
                    )
                )
        except (ValueError, TypeError):
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"Invalid minimum date configuration for '{field_name}'",
                    rule_violated="min_error",
                )
            )
    
    # Validate max date
    if "max" in validation_rules and validation_rules["max"] is not None:
        try:
            if isinstance(validation_rules["max"], str):
                max_date = datetime.fromisoformat(validation_rules["max"].replace('Z', '+00:00')).date()
            else:
                max_date = validation_rules["max"]
            
            if date_value > max_date:
                errors.append(
                    ValidationError(
                        field_name=field_name,
                        field_type=field_type.value,
                        error_message=f"'{field_name}' must be on or before {max_date}",
                        rule_violated="max",
                    )
                )
        except (ValueError, TypeError):
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"Invalid maximum date configuration for '{field_name}'",
                    rule_violated="max_error",
                )
            )
    
    return errors


def validate_dropdown_field(
    field_name: str,
    field_type: FieldType,
    field_config: CustomField,
    field_value: Any,
) -> List[ValidationError]:
    """Validate a dropdown field (enum)
    
    Validates:
    - Required: field must have a value
    - Enum: value must be one of the allowed options
    
    Args:
        field_name: Name of the field
        field_type: FieldType enum
        field_config: CustomField configuration
        field_value: Value to validate
        
    Returns:
        List of ValidationError objects
    """
    errors = []
    
    # Check if field is required
    is_required = field_config.is_required
    
    # Handle null/empty values
    if field_value is None or (isinstance(field_value, str) and field_value.strip() == ""):
        if is_required:
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"'{field_name}' is required",
                    rule_violated="required",
                )
            )
        return errors
    
    # Get allowed options
    options = field_config.options
    if not options:
        errors.append(
            ValidationError(
                field_name=field_name,
                field_type=field_type.value,
                error_message=f"No options defined for '{field_name}'",
                rule_violated="no_options",
            )
        )
        return errors
    
    # Convert value to string for comparison
    str_value = str(field_value).strip()
    
    # Check if value is in options (case-sensitive)
    if str_value not in options:
        errors.append(
            ValidationError(
                field_name=field_name,
                field_type=field_type.value,
                error_message=f"'{field_name}' must be one of: {', '.join(options)}",
                rule_violated="enum",
            )
        )
    
    return errors


def validate_boolean_field(
    field_name: str,
    field_type: FieldType,
    field_config: CustomField,
    field_value: Any,
) -> List[ValidationError]:
    """Validate a boolean field
    
    Validates:
    - Required: field must have a value
    - Valid boolean: value must be boolean or parseable as boolean
    
    Args:
        field_name: Name of the field
        field_type: FieldType enum
        field_config: CustomField configuration
        field_value: Value to validate
        
    Returns:
        List of ValidationError objects
    """
    errors = []
    
    # Check if field is required
    is_required = field_config.is_required
    
    # Handle null values
    if field_value is None:
        if is_required:
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"'{field_name}' is required",
                    rule_violated="required",
                )
            )
        return errors
    
    # Check if already boolean
    if isinstance(field_value, bool):
        return errors
    
    # Try to parse as boolean
    if isinstance(field_value, str):
        if field_value.lower() in ("true", "1", "yes", "on"):
            return errors
        elif field_value.lower() in ("false", "0", "no", "off"):
            return errors
        else:
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"'{field_name}' must be a valid boolean value (true/false)",
                    rule_violated="invalid_boolean",
                )
            )
    elif isinstance(field_value, (int, float)):
        if field_value in (0, 1):
            return errors
        else:
            errors.append(
                ValidationError(
                    field_name=field_name,
                    field_type=field_type.value,
                    error_message=f"'{field_name}' must be a valid boolean value (0 or 1)",
                    rule_violated="invalid_boolean",
                )
            )
    else:
        errors.append(
            ValidationError(
                field_name=field_name,
                field_type=field_type.value,
                error_message=f"'{field_name}' must be a valid boolean value",
                rule_violated="invalid_boolean",
            )
        )
    
    return errors
