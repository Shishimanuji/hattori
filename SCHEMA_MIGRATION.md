# Database Schema Migration Guide

## Overview

This document describes the migration from the old project-resource-asset_type schema to the new template-driven asset management schema.

## New Schema Architecture

### Core Changes

1. **Roles Table** - Predefined user roles replacing string-based roles
   - Super Admin, Admin, Project Manager, Engineer, Viewer, Auditor

2. **Templates** - Workbook format definitions
   - Support for multiple client standards (Navy, BEL, HAL)
   - Version tracking and configuration

3. **Resource Types** - Unified representation of asset categories
   - Replaces asset_type concept
   - Display ordering ensures consistent UI presentation

4. **Dynamic Fields** - EAV pattern for flexible schema
   - resource_fields: Field definitions per resource type
   - asset_field_values: Actual field values for assets

5. **Assets** - Unified asset table
   - Single table for all asset types
   - Comprehensive tracking (warranty, audit, custodian)
   - Replaces separate resources table

6. **Supporting Tables**
   - project_summary: SEAW sheet data isolated
   - documents: File attachments
   - alerts: Dashboard notifications
   - import_history: Enhanced import tracking
   - report_templates: Reusable report configurations

## Migration Steps

### Step 1: Database Preparation

The application automatically creates tables on startup via SQLAlchemy. No manual migration is required.

### Step 2: Data Migration

For existing deployments with data:

```python
# Migration script would handle:
1. Create new roles from existing role strings
2. Migrate users to use role_id instead of role string
3. Create templates for existing projects
4. Create resource_types from existing asset_types
5. Migrate resources → assets
6. Set up field definitions from custom_fields
7. Populate asset_field_values from custom_field_values
```

### Step 3: Application Restart

After database migration, restart the application to load new models.

## Backward Compatibility

Legacy tables and models are maintained for compatibility:
- `resources` table - still populated
- `asset_types` table - still available
- Old schemas - continue to work

Gradual migration allows running both old and new code simultaneously.

## New Models

### Role Model
```python
class Role:
    id: int
    role_name: str
    description: str
    created_at: datetime
```

### Template Model
```python
class Template:
    id: UUID
    template_name: str
    version: str
    client_type: str
    is_default: bool
    template_config: JSON
```

### ResourceType Model
```python
class ResourceType:
    id: UUID
    name: str
    display_name: str
    icon: str
    display_order: int
    is_active: bool
```

### ResourceField Model
```python
class ResourceField:
    id: UUID
    resource_type_id: UUID
    field_name: str
    display_name: str
    data_type: str  # text, number, date, dropdown, boolean, decimal, email, url
    display_order: int
    is_required: bool
    is_unique: bool
    options: JSON  # for dropdowns
    validation_regex: str
```

### Asset Model
```python
class Asset:
    id: UUID
    project_id: UUID
    resource_type_id: UUID
    asset_code: str
    asset_name: str
    manufacturer: str
    model: str
    serial_number: str
    service_tag: str
    vendor: str
    location: str
    room_no: str
    custodian_id: UUID
    purchase_date: date
    installation_date: date
    warranty_start: date
    warranty_end: date
    cost: Decimal
    status: str  # Active, Inactive, Disposed, Under Repair, Reserved
    audit_status: str  # Pending, Completed, Overdue, Not Required
    last_audit_date: date
    remarks: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime  # soft delete
```

### AssetFieldValue Model
```python
class AssetFieldValue:
    id: UUID
    asset_id: UUID
    resource_field_id: UUID
    text_value: str
    number_value: Decimal
    date_value: date
    boolean_value: bool
    updated_at: datetime
```

### ProjectSummary Model
```python
class ProjectSummary:
    id: UUID
    project_id: UUID
    prepared_by: str
    approved_by: str
    project_duration: int  # days
    remarks: str
    total_budget: Decimal
    completion_percentage: Decimal
    version: str
```

### Document Model
```python
class Document:
    id: UUID
    project_id: UUID
    asset_id: UUID
    document_type: str  # Invoice, Warranty, Configuration, Drawing, Manual
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: UUID
    uploaded_at: datetime
```

### Alert Model
```python
class Alert:
    id: UUID
    project_id: UUID
    asset_id: UUID
    alert_type: str  # Warranty Expiry, Audit Due, Maintenance Due, Compliance, Budget
    severity: str  # Low, Medium, High, Critical
    title: str
    message: str
    status: str  # Active, Acknowledged, Resolved, Dismissed
    due_date: date
    created_at: datetime
    resolved_at: datetime
```

## API Endpoints

### Templates
- `POST /api/templates` - Create template
- `GET /api/templates` - List templates
- `GET /api/templates/{id}` - Get template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template

### Resource Types
- `GET /api/resource-types` - List resource types
- `GET /api/resource-types/{id}/fields` - Get fields
- `POST /api/resource-types/{id}/fields` - Create field
- `PUT /api/resource-types/fields/{id}` - Update field
- `DELETE /api/resource-types/fields/{id}` - Delete field

### Assets
- `POST /api/assets` - Create asset
- `GET /api/assets/{id}` - Get asset
- `GET /api/assets/project/{project_id}` - List project assets
- `PUT /api/assets/{id}` - Update asset
- `DELETE /api/assets/{id}` - Delete asset
- `GET /api/assets/{project_id}/warranty-expiring` - Warranty alerts
- `GET /api/assets/{project_id}/audit-due` - Audit alerts
- `GET /api/assets/{project_id}/summary` - Asset summary

## Field Types Supported

- **text** - String field (default for notes)
- **number** - Integer values
- **decimal** - Decimal/float values
- **date** - Date values (YYYY-MM-DD)
- **dropdown** - Select from predefined options
- **boolean** - True/False values
- **email** - Email address validation
- **url** - URL validation

## Data Validation

Each field has optional:
- `is_required` - Must have a value
- `is_unique` - Value must be unique per asset
- `validation_regex` - Custom validation pattern
- `default_value` - Default if not provided
- `options` - For dropdown fields

## Services

### TemplateService
- `create_template()` - Create new template
- `get_template()` - Retrieve template
- `get_all_templates()` - List all templates
- `update_template()` - Update template
- `delete_template()` - Soft delete
- `identify_template_by_sheets()` - Match Excel sheets to template
- `get_sheet_mappings()` - Get sheet → resource type mappings

### AssetService
- `create_asset()` - Create new asset
- `get_asset()` - Retrieve asset
- `get_project_assets()` - List project assets
- `update_asset()` - Update asset
- `delete_asset()` - Soft delete asset
- `set_field_value()` - Set dynamic field value
- `get_field_value()` - Get field value
- `get_all_field_values()` - Get all field values
- `get_warranty_expiring_assets()` - Find expiring warranties
- `get_assets_requiring_audit()` - Find audit due assets
- `calculate_project_asset_value()` - Total asset value
- `get_asset_summary_by_type()` - Asset summary

### ResourceTypeService
- `create_resource_type()` - Create resource type
- `get_resource_type()` - Retrieve resource type
- `get_all_resource_types()` - List all types
- `create_resource_field()` - Create field
- `get_resource_fields()` - List fields for type
- `update_resource_field()` - Update field
- `delete_resource_field()` - Delete field
- `add_field_to_end()` - Auto-assign display order
- `reorder_fields()` - Reorder fields for type

## Migration Checklist

- [ ] Database schema created (automatic on startup)
- [ ] Models imported and registered
- [ ] Routes registered in main.py
- [ ] Services initialized
- [ ] Schemas available for API
- [ ] Tests passing
- [ ] Data validation working
- [ ] Soft deletes functioning
- [ ] Indexes created for performance
- [ ] Legacy routes still working (backward compatibility)

## Testing

Run the following to verify schema:

```bash
# Check models import
python -c "from app.models import Role, Template, Asset; print('Models loaded')"

# Check services
python -c "from app.services.asset_service import AssetService; print('Services loaded')"

# Check schemas
python -c "from app.schemas.asset import AssetSchema; print('Schemas loaded')"

# Check routes
python -c "from app.routes import templates, assets; print('Routes loaded')"
```

## Performance Notes

### Indexes Created
- `idx_templates_client_type` - For template filtering
- `idx_templates_is_active` - For active template queries
- `idx_resource_types_display_order` - For UI ordering
- `idx_assets_project_id` - For project asset queries
- `idx_assets_warranty_end` - For warranty alerts
- `idx_assets_audit_status` - For audit queries
- `idx_asset_field_values_asset_id` - For field value lookups
- `idx_document_type` - For document filtering
- `idx_alerts_severity` - For alert sorting

### Composite Indexes
- `(resource_type_id, display_order)` - For field ordering
- `(project_id, status)` - For asset filtering

## Rollback Plan

If needed, the old models and tables remain available. 
Switch API routes back to legacy endpoints to revert.

## Future Enhancements

1. Full data migration tool for existing deployments
2. Template import/export functionality
3. Dynamic field validation rules JSON schema
4. Template versioning and migration paths
5. Bulk asset operations
6. Advanced alert scheduling
7. Report building UI
