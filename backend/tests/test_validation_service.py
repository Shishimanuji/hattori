"""Tests for validation service"""
import pytest
from unittest.mock import Mock
from datetime import datetime, date

from app.models.asset_type import FieldType
from app.services.validation_service import (
    SchemaValidator,
    ValidationError,
    ValidationResult,
    validate_text_field,
    validate_number_field,
    validate_date_field,
    validate_dropdown_field,
    validate_boolean_field,
)


# Helper functions to create mock CustomField objects
def create_custom_field(
    name: str,
    field_type: str,
    is_required: bool = True,
    validation_rules: dict = None,
    options: list = None,
):
    """Create a mock CustomField"""
    field = Mock()
    field.name = name
    field.field_type = field_type
    field.is_required = is_required
    field.validation_rules = validation_rules or {}
    field.options = options or []
    return field


def create_asset_type_mock(custom_fields_list: list):
    """Create a mock AssetType"""
    asset_type = Mock()
    asset_type.custom_fields = custom_fields_list
    return asset_type


# Tests for ValidationResult and ValidationError
class TestValidationError:
    """Tests for ValidationError class"""
    
    def test_validation_error_creation(self):
        """Test creating a validation error"""
        error = ValidationError(
            field_name="email",
            field_type="text",
            error_message="Invalid email format",
            rule_violated="format",
        )
        
        assert error.field_name == "email"
        assert error.field_type == "text"
        assert error.error_message == "Invalid email format"
        assert error.rule_violated == "format"
    
    def test_validation_error_to_dict(self):
        """Test converting validation error to dictionary"""
        error = ValidationError(
            field_name="email",
            field_type="text",
            error_message="Invalid email format",
            rule_violated="format",
        )
        
        error_dict = error.to_dict()
        assert error_dict["field_name"] == "email"
        assert error_dict["field_type"] == "text"
        assert error_dict["error_message"] == "Invalid email format"
        assert error_dict["rule_violated"] == "format"


class TestValidationResult:
    """Tests for ValidationResult class"""
    
    def test_validation_result_valid(self):
        """Test creating a valid validation result"""
        result = ValidationResult(is_valid=True, errors=[])
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validation_result_invalid(self):
        """Test creating an invalid validation result with errors"""
        errors = [
            ValidationError("field1", "text", "Error 1", "rule1"),
            ValidationError("field2", "number", "Error 2", "rule2"),
        ]
        result = ValidationResult(is_valid=False, errors=errors)
        
        assert result.is_valid is False
        assert len(result.errors) == 2
    
    def test_validation_result_to_dict(self):
        """Test converting validation result to dictionary"""
        errors = [ValidationError("field1", "text", "Error 1", "rule1")]
        result = ValidationResult(is_valid=False, errors=errors)
        
        result_dict = result.to_dict()
        assert result_dict["is_valid"] is False
        assert len(result_dict["errors"]) == 1
        assert result_dict["errors"][0]["field_name"] == "field1"


# Tests for text field validation
class TestTextFieldValidation:
    """Tests for text field validation"""
    
    def test_text_field_valid(self):
        """Test valid text field"""
        field = create_custom_field(
            "Description",
            FieldType.TEXT.value,
            is_required=True,
            validation_rules={"min": 5, "max": 100},
        )
        errors = validate_text_field(
            "Description",
            FieldType.TEXT,
            field,
            "Valid text here",
        )
        assert len(errors) == 0
    
    def test_text_field_required_missing(self):
        """Test required text field is missing"""
        field = create_custom_field(
            "Description",
            FieldType.TEXT.value,
            is_required=True,
            validation_rules={"min": 5, "max": 100},
        )
        errors = validate_text_field("Description", FieldType.TEXT, field, None)
        assert len(errors) == 1
        assert errors[0].rule_violated == "required"
    
    def test_text_field_required_empty_string(self):
        """Test required text field is empty string"""
        field = create_custom_field(
            "Description",
            FieldType.TEXT.value,
            is_required=True,
            validation_rules={"min": 5, "max": 100},
        )
        errors = validate_text_field("Description", FieldType.TEXT, field, "   ")
        assert len(errors) == 1
        assert errors[0].rule_violated == "required"
    
    def test_text_field_min_length_violation(self):
        """Test text field too short"""
        field = create_custom_field(
            "Description",
            FieldType.TEXT.value,
            is_required=True,
            validation_rules={"min": 5, "max": 100},
        )
        errors = validate_text_field("Description", FieldType.TEXT, field, "Hi")
        assert len(errors) == 1
        assert errors[0].rule_violated == "min"
    
    def test_text_field_max_length_violation(self):
        """Test text field too long"""
        field = create_custom_field(
            "Description",
            FieldType.TEXT.value,
            is_required=True,
            validation_rules={"min": 5, "max": 100},
        )
        errors = validate_text_field("Description", FieldType.TEXT, field, "x" * 101)
        assert len(errors) == 1
        assert errors[0].rule_violated == "max"
    
    def test_text_field_optional_not_provided(self):
        """Test optional text field not provided"""
        field = create_custom_field(
            "Notes",
            FieldType.TEXT.value,
            is_required=False,
        )
        errors = validate_text_field("Notes", FieldType.TEXT, field, None)
        assert len(errors) == 0
    
    def test_text_field_regex_valid(self):
        """Test text field regex pattern matches"""
        field = create_custom_field(
            "Email",
            FieldType.TEXT.value,
            is_required=True,
            validation_rules={
                "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            },
        )
        errors = validate_text_field("Email", FieldType.TEXT, field, "test@example.com")
        assert len(errors) == 0
    
    def test_text_field_regex_invalid(self):
        """Test text field regex pattern doesn't match"""
        field = create_custom_field(
            "Email",
            FieldType.TEXT.value,
            is_required=True,
            validation_rules={
                "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            },
        )
        errors = validate_text_field("Email", FieldType.TEXT, field, "invalid-email")
        assert len(errors) == 1
        assert errors[0].rule_violated == "regex"


# Tests for number field validation
class TestNumberFieldValidation:
    """Tests for number field validation"""
    
    def test_number_field_valid(self):
        """Test valid number field"""
        field = create_custom_field(
            "Experience",
            FieldType.NUMBER.value,
            is_required=True,
            validation_rules={"min": 0, "max": 50},
        )
        errors = validate_number_field("Experience", FieldType.NUMBER, field, 25)
        assert len(errors) == 0
    
    def test_number_field_float_valid(self):
        """Test valid float value"""
        field = create_custom_field(
            "Experience",
            FieldType.NUMBER.value,
            is_required=True,
            validation_rules={"min": 0, "max": 50},
        )
        errors = validate_number_field("Experience", FieldType.NUMBER, field, 25.5)
        assert len(errors) == 0
    
    def test_number_field_string_valid(self):
        """Test string that can be converted to number"""
        field = create_custom_field(
            "Experience",
            FieldType.NUMBER.value,
            is_required=True,
            validation_rules={"min": 0, "max": 50},
        )
        errors = validate_number_field("Experience", FieldType.NUMBER, field, "30")
        assert len(errors) == 0
    
    def test_number_field_required_missing(self):
        """Test required number field missing"""
        field = create_custom_field(
            "Experience",
            FieldType.NUMBER.value,
            is_required=True,
            validation_rules={"min": 0, "max": 50},
        )
        errors = validate_number_field("Experience", FieldType.NUMBER, field, None)
        assert len(errors) == 1
        assert errors[0].rule_violated == "required"
    
    def test_number_field_invalid_value(self):
        """Test invalid number value"""
        field = create_custom_field(
            "Experience",
            FieldType.NUMBER.value,
            is_required=True,
            validation_rules={"min": 0, "max": 50},
        )
        errors = validate_number_field(
            "Experience", FieldType.NUMBER, field, "not_a_number"
        )
        assert len(errors) == 1
        assert errors[0].rule_violated == "invalid_number"
    
    def test_number_field_min_violation(self):
        """Test number below minimum"""
        field = create_custom_field(
            "Experience",
            FieldType.NUMBER.value,
            is_required=True,
            validation_rules={"min": 0, "max": 50},
        )
        errors = validate_number_field("Experience", FieldType.NUMBER, field, -5)
        assert len(errors) == 1
        assert errors[0].rule_violated == "min"
    
    def test_number_field_max_violation(self):
        """Test number above maximum"""
        field = create_custom_field(
            "Experience",
            FieldType.NUMBER.value,
            is_required=True,
            validation_rules={"min": 0, "max": 50},
        )
        errors = validate_number_field("Experience", FieldType.NUMBER, field, 75)
        assert len(errors) == 1
        assert errors[0].rule_violated == "max"
    
    def test_number_field_at_min_boundary(self):
        """Test number exactly at minimum"""
        field = create_custom_field(
            "Experience",
            FieldType.NUMBER.value,
            is_required=True,
            validation_rules={"min": 0, "max": 50},
        )
        errors = validate_number_field("Experience", FieldType.NUMBER, field, 0)
        assert len(errors) == 0
    
    def test_number_field_at_max_boundary(self):
        """Test number exactly at maximum"""
        field = create_custom_field(
            "Experience",
            FieldType.NUMBER.value,
            is_required=True,
            validation_rules={"min": 0, "max": 50},
        )
        errors = validate_number_field("Experience", FieldType.NUMBER, field, 50)
        assert len(errors) == 0
    
    def test_number_field_optional_not_provided(self):
        """Test optional number field not provided"""
        field = create_custom_field(
            "Count",
            FieldType.NUMBER.value,
            is_required=False,
        )
        errors = validate_number_field("Count", FieldType.NUMBER, field, None)
        assert len(errors) == 0


# Tests for date field validation
class TestDateFieldValidation:
    """Tests for date field validation"""
    
    def test_date_field_valid_datetime(self):
        """Test valid date field with datetime object"""
        field = create_custom_field(
            "StartDate",
            FieldType.DATE.value,
            is_required=True,
        )
        errors = validate_date_field(
            "StartDate",
            FieldType.DATE,
            field,
            datetime(2024, 1, 15),
        )
        assert len(errors) == 0
    
    def test_date_field_valid_iso_string(self):
        """Test valid date field with ISO format string"""
        field = create_custom_field(
            "StartDate",
            FieldType.DATE.value,
            is_required=True,
        )
        errors = validate_date_field(
            "StartDate",
            FieldType.DATE,
            field,
            "2024-01-15",
        )
        assert len(errors) == 0
    
    def test_date_field_required_missing(self):
        """Test required date field missing"""
        field = create_custom_field(
            "StartDate",
            FieldType.DATE.value,
            is_required=True,
        )
        errors = validate_date_field("StartDate", FieldType.DATE, field, None)
        assert len(errors) == 1
        assert errors[0].rule_violated == "required"
    
    def test_date_field_invalid_format(self):
        """Test invalid date format"""
        field = create_custom_field(
            "StartDate",
            FieldType.DATE.value,
            is_required=True,
        )
        errors = validate_date_field(
            "StartDate", FieldType.DATE, field, "invalid-date"
        )
        assert len(errors) == 1
        assert errors[0].rule_violated == "invalid_date"
    
    def test_date_field_optional_not_provided(self):
        """Test optional date field not provided"""
        field = create_custom_field(
            "EndDate",
            FieldType.DATE.value,
            is_required=False,
        )
        errors = validate_date_field("EndDate", FieldType.DATE, field, None)
        assert len(errors) == 0


# Tests for dropdown field validation
class TestDropdownFieldValidation:
    """Tests for dropdown field validation"""
    
    def test_dropdown_field_valid(self):
        """Test valid dropdown selection"""
        field = create_custom_field(
            "Department",
            FieldType.DROPDOWN.value,
            is_required=True,
            options=["Engineering", "Sales", "HR"],
        )
        errors = validate_dropdown_field(
            "Department", FieldType.DROPDOWN, field, "Engineering"
        )
        assert len(errors) == 0
    
    def test_dropdown_field_valid_second_option(self):
        """Test valid second option"""
        field = create_custom_field(
            "Department",
            FieldType.DROPDOWN.value,
            is_required=True,
            options=["Engineering", "Sales", "HR"],
        )
        errors = validate_dropdown_field("Department", FieldType.DROPDOWN, field, "Sales")
        assert len(errors) == 0
    
    def test_dropdown_field_required_missing(self):
        """Test required dropdown field missing"""
        field = create_custom_field(
            "Department",
            FieldType.DROPDOWN.value,
            is_required=True,
            options=["Engineering", "Sales", "HR"],
        )
        errors = validate_dropdown_field("Department", FieldType.DROPDOWN, field, None)
        assert len(errors) == 1
        assert errors[0].rule_violated == "required"
    
    def test_dropdown_field_required_empty_string(self):
        """Test required dropdown field empty string"""
        field = create_custom_field(
            "Department",
            FieldType.DROPDOWN.value,
            is_required=True,
            options=["Engineering", "Sales", "HR"],
        )
        errors = validate_dropdown_field("Department", FieldType.DROPDOWN, field, "   ")
        assert len(errors) == 1
        assert errors[0].rule_violated == "required"
    
    def test_dropdown_field_invalid_option(self):
        """Test invalid option value"""
        field = create_custom_field(
            "Department",
            FieldType.DROPDOWN.value,
            is_required=True,
            options=["Engineering", "Sales", "HR"],
        )
        errors = validate_dropdown_field(
            "Department", FieldType.DROPDOWN, field, "InvalidDept"
        )
        assert len(errors) == 1
        assert errors[0].rule_violated == "enum"
    
    def test_dropdown_field_optional_not_provided(self):
        """Test optional dropdown field not provided"""
        field = create_custom_field(
            "Priority",
            FieldType.DROPDOWN.value,
            is_required=False,
            options=["Low", "Medium", "High"],
        )
        errors = validate_dropdown_field("Priority", FieldType.DROPDOWN, field, None)
        assert len(errors) == 0


# Tests for boolean field validation
class TestBooleanFieldValidation:
    """Tests for boolean field validation"""
    
    def test_boolean_field_valid_true(self):
        """Test valid boolean true"""
        field = create_custom_field(
            "IsActive",
            FieldType.BOOLEAN.value,
            is_required=True,
        )
        errors = validate_boolean_field("IsActive", FieldType.BOOLEAN, field, True)
        assert len(errors) == 0
    
    def test_boolean_field_valid_false(self):
        """Test valid boolean false"""
        field = create_custom_field(
            "IsActive",
            FieldType.BOOLEAN.value,
            is_required=True,
        )
        errors = validate_boolean_field("IsActive", FieldType.BOOLEAN, field, False)
        assert len(errors) == 0
    
    def test_boolean_field_valid_string_true(self):
        """Test valid string representations of true"""
        field = create_custom_field(
            "IsActive",
            FieldType.BOOLEAN.value,
            is_required=True,
        )
        for val in ["true", "True", "TRUE", "1", "yes", "on"]:
            errors = validate_boolean_field("IsActive", FieldType.BOOLEAN, field, val)
            assert len(errors) == 0, f"Failed for value: {val}"
    
    def test_boolean_field_valid_string_false(self):
        """Test valid string representations of false"""
        field = create_custom_field(
            "IsActive",
            FieldType.BOOLEAN.value,
            is_required=True,
        )
        for val in ["false", "False", "FALSE", "0", "no", "off"]:
            errors = validate_boolean_field("IsActive", FieldType.BOOLEAN, field, val)
            assert len(errors) == 0, f"Failed for value: {val}"
    
    def test_boolean_field_valid_numeric_1(self):
        """Test valid numeric 1"""
        field = create_custom_field(
            "IsActive",
            FieldType.BOOLEAN.value,
            is_required=True,
        )
        errors = validate_boolean_field("IsActive", FieldType.BOOLEAN, field, 1)
        assert len(errors) == 0
    
    def test_boolean_field_valid_numeric_0(self):
        """Test valid numeric 0"""
        field = create_custom_field(
            "IsActive",
            FieldType.BOOLEAN.value,
            is_required=True,
        )
        errors = validate_boolean_field("IsActive", FieldType.BOOLEAN, field, 0)
        assert len(errors) == 0
    
    def test_boolean_field_required_missing(self):
        """Test required boolean field missing"""
        field = create_custom_field(
            "IsActive",
            FieldType.BOOLEAN.value,
            is_required=True,
        )
        errors = validate_boolean_field("IsActive", FieldType.BOOLEAN, field, None)
        assert len(errors) == 1
        assert errors[0].rule_violated == "required"
    
    def test_boolean_field_invalid_string(self):
        """Test invalid string value"""
        field = create_custom_field(
            "IsActive",
            FieldType.BOOLEAN.value,
            is_required=True,
        )
        errors = validate_boolean_field("IsActive", FieldType.BOOLEAN, field, "maybe")
        assert len(errors) == 1
        assert errors[0].rule_violated == "invalid_boolean"
    
    def test_boolean_field_invalid_number(self):
        """Test invalid numeric value"""
        field = create_custom_field(
            "IsActive",
            FieldType.BOOLEAN.value,
            is_required=True,
        )
        errors = validate_boolean_field("IsActive", FieldType.BOOLEAN, field, 5)
        assert len(errors) == 1
        assert errors[0].rule_violated == "invalid_boolean"
    
    def test_boolean_field_optional_not_provided(self):
        """Test optional boolean field not provided"""
        field = create_custom_field(
            "IsEnabled",
            FieldType.BOOLEAN.value,
            is_required=False,
        )
        errors = validate_boolean_field("IsEnabled", FieldType.BOOLEAN, field, None)
        assert len(errors) == 0


# Tests for SchemaValidator
class TestSchemaValidator:
    """Tests for SchemaValidator class"""
    
    def test_validator_initialization(self):
        """Test validator initialization"""
        fields = [
            create_custom_field(
                "Description",
                FieldType.TEXT.value,
                validation_rules={"min": 5, "max": 100},
            )
        ]
        asset_type = create_asset_type_mock(fields)
        validator = SchemaValidator(asset_type)
        assert validator.asset_type == asset_type
        assert "Description" in validator.custom_fields
    
    def test_validator_all_fields_valid(self):
        """Test validation with all fields valid"""
        fields = [
            create_custom_field(
                "Name",
                FieldType.TEXT.value,
                validation_rules={"min": 3, "max": 50},
            ),
            create_custom_field(
                "Cost",
                FieldType.NUMBER.value,
                validation_rules={"min": 0, "max": 1000000},
            ),
            create_custom_field(
                "Status",
                FieldType.DROPDOWN.value,
                options=["Active", "Inactive"],
            ),
        ]
        asset_type = create_asset_type_mock(fields)
        validator = SchemaValidator(asset_type)
        result = validator.validate({
            "Name": "Test Resource",
            "Cost": 500,
            "Status": "Active",
        })
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validator_missing_required_field(self):
        """Test validation with missing required field"""
        fields = [
            create_custom_field(
                "Name",
                FieldType.TEXT.value,
                validation_rules={"min": 3, "max": 50},
            ),
            create_custom_field(
                "Cost",
                FieldType.NUMBER.value,
                validation_rules={"min": 0, "max": 1000000},
            ),
            create_custom_field(
                "Status",
                FieldType.DROPDOWN.value,
                options=["Active", "Inactive"],
            ),
        ]
        asset_type = create_asset_type_mock(fields)
        validator = SchemaValidator(asset_type)
        result = validator.validate({
            "Name": "Test Resource",
            "Cost": 500,
            # Status is missing
        })
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field_name == "Status"
    
    def test_validator_multiple_errors(self):
        """Test validation with multiple field errors"""
        fields = [
            create_custom_field(
                "Name",
                FieldType.TEXT.value,
                validation_rules={"min": 3, "max": 50},
            ),
            create_custom_field(
                "Cost",
                FieldType.NUMBER.value,
                validation_rules={"min": 0, "max": 1000000},
            ),
            create_custom_field(
                "Status",
                FieldType.DROPDOWN.value,
                options=["Active", "Inactive"],
            ),
        ]
        asset_type = create_asset_type_mock(fields)
        validator = SchemaValidator(asset_type)
        result = validator.validate({
            "Name": "X",  # Too short
            "Cost": 2000000,  # Too high
            "Status": "Invalid",  # Not in options
        })
        
        assert result.is_valid is False
        assert len(result.errors) == 3
    
    def test_validator_partial_data(self):
        """Test validation with partial data (only some fields provided)"""
        fields = [
            create_custom_field(
                "Name",
                FieldType.TEXT.value,
                validation_rules={"min": 3, "max": 50},
            ),
            create_custom_field(
                "Cost",
                FieldType.NUMBER.value,
                validation_rules={"min": 0, "max": 1000000},
            ),
            create_custom_field(
                "Status",
                FieldType.DROPDOWN.value,
                options=["Active", "Inactive"],
            ),
        ]
        asset_type = create_asset_type_mock(fields)
        validator = SchemaValidator(asset_type)
        result = validator.validate({
            "Name": "Test Resource",
            "Cost": 500,
        })
        
        # Status is missing but required
        assert result.is_valid is False
        assert any(e.field_name == "Status" for e in result.errors)
    
    def test_validator_empty_data(self):
        """Test validation with empty data"""
        fields = [
            create_custom_field(
                "Name",
                FieldType.TEXT.value,
                validation_rules={"min": 3, "max": 50},
            ),
            create_custom_field(
                "Cost",
                FieldType.NUMBER.value,
                validation_rules={"min": 0, "max": 1000000},
            ),
            create_custom_field(
                "Status",
                FieldType.DROPDOWN.value,
                options=["Active", "Inactive"],
            ),
        ]
        asset_type = create_asset_type_mock(fields)
        validator = SchemaValidator(asset_type)
        result = validator.validate({})
        
        # All required fields missing
        assert result.is_valid is False
        assert len(result.errors) == 3  # Name, Cost, Status
    
    def test_validator_extra_fields_ignored(self):
        """Test that extra fields are ignored"""
        fields = [
            create_custom_field(
                "Name",
                FieldType.TEXT.value,
                validation_rules={"min": 3, "max": 50},
            ),
            create_custom_field(
                "Cost",
                FieldType.NUMBER.value,
                validation_rules={"min": 0, "max": 1000000},
            ),
            create_custom_field(
                "Status",
                FieldType.DROPDOWN.value,
                options=["Active", "Inactive"],
            ),
        ]
        asset_type = create_asset_type_mock(fields)
        validator = SchemaValidator(asset_type)
        result = validator.validate({
            "Name": "Test Resource",
            "Cost": 500,
            "Status": "Active",
            "ExtraField": "Should be ignored",
        })
        
        assert result.is_valid is True
        assert len(result.errors) == 0


# Integration tests
class TestValidationIntegration:
    """Integration tests for validation"""
    
    def test_validation_result_json_serializable(self):
        """Test that validation result can be converted to JSON"""
        fields = [
            create_custom_field(
                "Name",
                FieldType.TEXT.value,
                validation_rules={"min": 3, "max": 50},
            ),
            create_custom_field(
                "Cost",
                FieldType.NUMBER.value,
                validation_rules={"min": 0, "max": 1000000},
            ),
        ]
        asset_type = create_asset_type_mock(fields)
        validator = SchemaValidator(asset_type)
        result = validator.validate({
            "Name": "X",  # Invalid
            "Cost": -100,  # Invalid
        })
        
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert "is_valid" in result_dict
        assert "errors" in result_dict
        assert isinstance(result_dict["errors"], list)
    
    def test_multiple_field_types_validation(self):
        """Test validation with different field types"""
        fields = [
            create_custom_field(
                "Name",
                FieldType.TEXT.value,
                validation_rules={"min": 3, "max": 50},
            ),
            create_custom_field(
                "Cost",
                FieldType.NUMBER.value,
                validation_rules={"min": 0, "max": 1000000},
            ),
            create_custom_field(
                "Status",
                FieldType.DROPDOWN.value,
                options=["Active", "Inactive"],
            ),
        ]
        asset_type = create_asset_type_mock(fields)
        validator = SchemaValidator(asset_type)
        
        # Valid data with different types
        result = validator.validate({
            "Name": "Resource123",  # Text
            "Cost": 50000.50,  # Number
            "Status": "Active",  # Dropdown
        })
        
        assert result.is_valid is True
    
    def test_validation_error_messages_descriptive(self):
        """Test that error messages are descriptive"""
        fields = [
            create_custom_field(
                "Name",
                FieldType.TEXT.value,
                validation_rules={"min": 3, "max": 50},
            ),
            create_custom_field(
                "Cost",
                FieldType.NUMBER.value,
                validation_rules={"min": 0, "max": 1000000},
            ),
            create_custom_field(
                "Status",
                FieldType.DROPDOWN.value,
                options=["Active", "Inactive"],
            ),
        ]
        asset_type = create_asset_type_mock(fields)
        validator = SchemaValidator(asset_type)
        result = validator.validate({
            "Name": "X",
            "Cost": "not_a_number",
            "Status": "Unknown",
        })
        
        # All errors should have descriptive messages
        for error in result.errors:
            assert len(error.error_message) > 0
            assert error.field_name in error.error_message or error.field_type in error.error_message
