# Implementation Plan: Project Resource Management System (PRMS)

## Overview

The PRMS implementation follows a multi-layered architecture with FastAPI backend (Python) and React frontend (TypeScript). Implementation proceeds from infrastructure setup through core features, with integration and testing checkpoints throughout. The design includes 24 correctness properties that will be validated through property-based tests embedded alongside implementation tasks.

## Tasks

- [x] 1. Backend project setup - FastAPI, PostgreSQL, dependencies
  - Initialize FastAPI project with Poetry/pip
  - Configure PostgreSQL connection and SQLAlchemy ORM
  - Set up environment variables (.env configuration)
  - Install core dependencies: fastapi, sqlalchemy, pydantic, psycopg2, bcrypt, python-jose
  - Initialize project structure (models/, schemas/, routes/, services/, utils/)
  - _Requirements: 11.1, 13.1_

- [x] 2. Frontend project setup - React, TypeScript, Vite, Tailwind CSS
  - Initialize React + TypeScript project with Vite
  - Configure Tailwind CSS and ShadCN UI component library
  - Set up project structure (src/pages, src/components, src/hooks, src/services, src/types)
  - Install core dependencies: react-query (TanStack Query), axios, react-router-dom, echarts
  - Configure environment variables and API base URL
  - _Requirements: 13.1_

- [x] 3. Database schema creation and migrations
  - [x] 3.1 Create core database tables (users, projects, resources, asset_types, custom_fields)
    - Create users, projects, asset_types, custom_fields tables with proper types and constraints
    - Implement soft delete columns (deleted_at) for all resource tables
    - _Requirements: 11.1, 18.1_

  - [x] 3.2 Create relationships and foreign keys
    - Add foreign key constraints between resources, projects, asset_types
    - Create allocations table for budget tracking
    - Create audit_logs table for change history
    - _Requirements: 11.1, 18.1_

  - [x] 3.3 Create performance indexes
    - Add indexes on frequently searched columns (project_id, asset_type_id, status, deleted_at)
    - Create composite indexes for common filter combinations
    - _Requirements: 13.1, 18.2_

  - [x] 3.4 Create sessions table for authentication
    - Create sessions table with token_hash, user_id, expiration
    - Create index on sessions.expires_at for cleanup
    - _Requirements: 20.1_

  - [ ]* 3.5 Write property tests for schema integrity
    - **Property 20: Data persistence round-trip**
    - **Validates: Requirements 11.1**

- [x] 4. Backend authentication setup - Login, JWT, session management
  - [x] 4.1 Implement user model and password hashing
    - Create User SQLAlchemy model with password_hash field
    - Implement bcrypt password hashing utilities
    - _Requirements: 3.1, 14.1_

  - [x] 4.2 Implement JWT token generation and validation
    - Create JWT token utilities with 24-hour expiration
    - Implement token signature verification and expiration checking
    - _Requirements: 3.2, 20.1_

  - [x] 4.3 Implement login endpoint
    - Create POST /api/auth/login endpoint
    - Validate credentials against bcrypt hash
    - Return JWT token on success, 401 on failure
    - _Requirements: 3.1, 3.2_

  - [x] 4.4 Implement logout endpoint
    - Create POST /api/auth/logout endpoint
    - Invalidate session token immediately
    - _Requirements: 3.10, 20.3_

  - [x] 4.5 Implement authentication middleware
    - Create middleware to extract and validate JWT from request headers
    - Add user context to request state
    - Return 401 for invalid/missing tokens
    - _Requirements: 3.1_

  - [x] 4.6 Implement session timeout management
    - Implement 30-minute idle timeout with warning
    - Implement 35-minute auto-logout
    - Track last activity on each request
    - _Requirements: 20.4, 20.5_

  - [ ]* 4.7 Write property tests for authentication
    - **Property 6: Authentication is required for all system access**
    - **Property 7: Session tokens have correct expiration**
    - **Property 10: Expired sessions redirect to login on next action**
    - **Validates: Requirements 3.1, 3.2, 20.1**

- [x] 5. Frontend authentication - Login form, token management, auth context
  - [x] 5.1 Create AuthContext and useAuth hook
    - Implement React Context for authentication state
    - Store user info and JWT token
    - Handle token refresh and expiration
    - _Requirements: 3.1_

  - [x] 5.2 Create Login page component
    - Create form with username and password fields
    - Implement form validation and error display
    - Call login API endpoint
    - Store JWT token on successful login
    - _Requirements: 3.1_

  - [x] 5.3 Implement request interceptor with JWT
    - Configure Axios to automatically add Authorization header
    - Handle 401 responses by redirecting to login
    - Implement token refresh logic
    - _Requirements: 3.1_

  - [x] 5.4 Implement logout functionality
    - Create logout button in navbar
    - Call POST /api/auth/logout endpoint
    - Clear stored token and redirect to login
    - _Requirements: 3.10_

  - [ ]* 5.5 Write unit tests for authentication components
    - Test login form submission
    - Test token storage and retrieval
    - Test 401 redirect behavior
    - _Requirements: 3.1_

- [x] 6. User management backend - CRUD, role assignment, validation
  - [x] 6.1 Create User API endpoints
    - GET /api/users - List all users with pagination
    - POST /api/users - Create new user with role
    - GET /api/users/{id} - Get user details
    - PUT /api/users/{id} - Update user
    - DELETE /api/users/{id} - Archive user (soft delete)
    - _Requirements: 4.1, 4.2, 12.1_

  - [x] 6.2 Implement user role assignment and validation
    - Validate role values (Admin, Manager, Analyst, Viewer)
    - Implement role update with audit logging
    - Enforce unique email addresses
    - _Requirements: 4.2, 4.3_

  - [x] 6.3 Implement password reset functionality
    - Generate temporary password and one-time token
    - Create password reset endpoint
    - Require user to set new password on first login after reset
    - _Requirements: 4.7_

  - [ ]* 6.4 Write unit tests for user management
    - Test role assignment validation
    - Test email uniqueness constraint
    - Test user archiving (soft delete)
    - _Requirements: 4.1_

- [x] 7. Project management backend - CRUD, endpoints, database operations
  - [x] 7.1 Create Project model and schemas
    - Create Project SQLAlchemy model with all fields
    - Create Pydantic schemas for request/response validation
    - _Requirements: 5.1, 5.2_

  - [x] 7.2 Create Project API endpoints
    - GET /api/projects - List projects with pagination, filtering, sorting
    - POST /api/projects - Create new project
    - GET /api/projects/{id} - Get project details with resource summary
    - PUT /api/projects/{id} - Update project details
    - DELETE /api/projects/{id} - Soft delete project
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 7.3 Implement project budget tracking
    - Create service method to calculate allocated_budget and remaining_budget
    - Update allocations on resource creation/deletion
    - _Requirements: 10.1, 10.2_

  - [x] 7.4 Implement project soft deletes
    - Projects with deleted_at cannot receive new resources
    - Historical data retained for queries
    - _Requirements: 5.6, 5.7_

  - [ ]* 7.5 Write property tests for project operations
    - **Property 13: Budget updates follow resource allocation**
    - **Validates: Requirements 5.1, 10.1**

- [x] 8. Project management frontend - UI, list, detail, form components
  - [x] 8.1 Create ProjectList component
    - Display paginated list of projects
    - Implement filtering by status, search by name
    - Show project status color coding
    - Display budget utilization percentage
    - _Requirements: 5.1, 1.1_

  - [x] 8.2 Create ProjectDetail component
    - Display project information, budget details, resource count
    - Show resources by type breakdown
    - Implement edit and delete buttons
    - _Requirements: 5.4_

  - [x] 8.3 Create ProjectForm component (create and edit)
    - Form fields for name, description, status, budget, dates
    - Client-side validation with error display
    - Submit to API and handle responses
    - _Requirements: 5.1_

  - [x] 8.4 Create Project allocation summary component
    - Display allocated vs remaining budget
    - Show warning at 80% utilization (yellow)
    - Show error at 100% utilization (red)
    - _Requirements: 10.2_

  - [ ]* 8.5 Write unit tests for project components
    - Test project list rendering
    - Test form validation
    - Test budget calculation display
    - _Requirements: 5.1_

- [x] 9. Asset type management backend - Schema discovery, CRUD, validation
  - [x] 9.1 Create AssetType and CustomField models
    - Create AssetType SQLAlchemy model
    - Create CustomField model with type, validation rules, options
    - _Requirements: 7.1, 7.2_

  - [x] 9.2 Create Asset Type API endpoints
    - GET /api/asset-types - List asset types
    - POST /api/asset-types - Create asset type
    - GET /api/asset-types/{id} - Get with schema
    - PUT /api/asset-types/{id} - Update asset type
    - DELETE /api/asset-types/{id} - Mark inactive
    - _Requirements: 7.1, 7.2_

  - [x] 9.3 Create custom field management endpoints
    - POST /api/asset-types/{id}/fields - Add custom field
    - PUT /api/asset-types/{id}/fields/{field-id} - Update field
    - DELETE /api/asset-types/{id}/fields/{field-id} - Remove field
    - _Requirements: 7.3, 7.4_

  - [x] 9.4 Implement dynamic schema validation
    - Create validation rule engine (required, min/max, regex, enum)
    - Apply validation during resource creation/update
    - Return specific error messages per field
    - _Requirements: 8.1, 8.2_

  - [ ]* 9.5 Write property tests for schema discovery
    - **Property 15: Dynamic asset type schema discovery works for resource creation**
    - **Property 16: Custom field validation rules are enforced**
    - **Validates: Requirements 7.1, 7.2, 8.1**

- [x] 10. Asset type management frontend - UI, forms, validation display
  - [x] 10.1 Create AssetTypeList component
    - Display all active asset types
    - Show field count and creation date
    - Implement edit and deactivate buttons
    - _Requirements: 7.1_

  - [x] 10.2 Create AssetTypeForm component
    - Form to create/edit asset types
    - Dynamic custom field definition interface
    - Support field type selection (text, number, date, dropdown, boolean)
    - Allow validation rule configuration
    - _Requirements: 7.2, 7.3_

  - [x] 10.3 Create CustomFieldInput component
    - Renders different input types based on field_type
    - Applies validation and displays errors
    - Supports dropdown options from asset type schema
    - _Requirements: 7.5, 8.5_

  - [ ]* 10.4 Write unit tests for asset type components
    - Test asset type listing
    - Test custom field form rendering
    - _Requirements: 7.1_

- [x] 11. Resource management backend - CRUD, custom fields, allocation tracking
  - [x] 11.1 Create Resource model with dynamic custom fields
    - Create Resource SQLAlchemy model
    - Store custom_field_values as JSON
    - Implement getter/setter for typed field access
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 11.2 Create Resource API endpoints
    - GET /api/resources - List with filtering, pagination
    - POST /api/resources - Create with validation
    - GET /api/resources/{id} - Get details
    - PUT /api/resources/{id} - Update
    - DELETE /api/resources/{id} - Soft delete
    - _Requirements: 6.1, 6.2_

  - [x] 11.3 Implement allocation tracking service
    - Create Allocations table to track allocation history
    - Record cost_at_allocation for historical accuracy
    - Implement deallocation with cost return to budget
    - _Requirements: 10.3, 10.4_

  - [x] 11.4 Implement resource search and filtering
    - Filter by asset type, status, project, allocation date
    - Search by name
    - _Requirements: 6.7, 6.8_

  - [ ]* 11.5 Write property tests for resource operations
    - **Property 11: Resource creation validates all required fields**
    - **Property 12: Created resources receive unique identifiers and metadata**
    - **Property 14: Soft deletes preserve data integrity**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.5**

- [x] 12. Resource management frontend - UI, forms, custom field rendering
  - [ ] 12.1 Create ResourceList component
    - Display paginated list of resources
    - Implement filtering by asset type, status, project
    - Show search functionality
    - Display resource details with status badges
    - _Requirements: 6.1, 6.7_

  - [ ] 12.2 Create ResourceForm component
    - Dynamically load asset type schema
    - Render all standard and custom field inputs
    - Implement form validation with error display
    - Submit to API
    - _Requirements: 6.1_

  - [ ] 12.3 Create ResourceDetail component
    - Display all resource information
    - Show allocation history with dates and costs
    - Implement edit and delete buttons
    - _Requirements: 6.4, 6.10_

  - [ ] 12.4 Implement allocation UI controls
    - Show allocated vs available budget
    - Display warning/error when budget exceeded
    - Implement deallocate functionality
    - _Requirements: 10.1, 10.2_

  - [ ]* 12.5 Write unit tests for resource components
    - Test resource form with custom fields
    - Test resource list filtering
    - _Requirements: 6.1_

- [x] 13. RBAC enforcement backend - Middleware, decorators, permission checks
  - [ ] 13.1 Implement role-based access control decorator
    - Create @require_role(*roles) decorator for FastAPI routes
    - Check user role against required roles
    - Return 403 Forbidden for unauthorized access
    - _Requirements: 3.5, 3.6, 3.7, 3.8_

  - [ ] 13.2 Implement RBAC service layer
    - Create authorization checks for create_project, edit_project, delete_project
    - Enforce permission matrix from design document
    - Check project ownership for Manager role
    - _Requirements: 3.6, 3.7_

  - [ ] 13.3 Implement Viewer/Analyst project scope limiting
    - Limit Viewer access to only assigned projects
    - Allow Analyst access to all projects for read-only
    - Filter project lists based on user role
    - _Requirements: 1.5, 3.8_

  - [ ] 13.4 Implement resource-level authorization checks
    - Enforce permissions on resource CRUD operations
    - Apply role-based filtering to resource lists
    - _Requirements: 3.5, 3.6_

  - [ ]* 13.5 Write property tests for RBAC
    - **Property 8: Unauthorized access is blocked with 403 response**
    - **Property 9: Role-based permissions are consistently enforced**
    - **Validates: Requirements 3.3, 3.5, 3.6, 3.7, 3.8**

- [x] 14. Dashboard backend - Metrics queries, aggregations, performance
  - [x] 14.1 Implement project overview query service
    - Query projects with resource count by type
    - Calculate allocated and remaining budget
    - Apply role-based filtering
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 14.2 Implement resource distribution aggregation
    - Group resources by type, count by status
    - Calculate utilization percentages
    - _Requirements: 2.1, 2.3_

  - [x] 14.3 Implement utilization trend calculation
    - Calculate 30-day allocation trend data
    - Group by resource type and date
    - _Requirements: 2.2_

  - [x] 14.4 Create dashboard metrics endpoint
    - GET /api/dashboard/metrics - Return all dashboard data
    - Implement caching with 30-second TTL
    - Ensure response completes within 2 seconds
    - _Requirements: 1.4, 13.1_

  - [x] 14.5 Implement budget status endpoint
    - GET /api/dashboard/budget-status - Return budget summaries
    - Show warning at 80%, error at 100%
    - _Requirements: 10.2, 10.3_

  - [ ]* 14.6 Write property tests for dashboard metrics
    - **Property 2: Resource type counts are accurate**
    - **Property 3: Dashboard reflects concurrent changes**
    - **Property 4: Resource utilization trends are accurately calculated**
    - **Validates: Requirements 1.1, 1.3, 1.8, 2.1, 2.2**

- [x] 15. Dashboard frontend - Charts, cards, visualizations with ECharts
  - [x] 15.1 Create Dashboard page layout
    - Implement responsive grid layout
    - Add ProjectOverviewCard, ResourceDistributionChart, etc.
    - _Requirements: 1.1, 2.1_

  - [x] 15.2 Create ProjectOverviewCard component
    - Display project list with name, status, budget info
    - Color-code status (Active/green, Pending/yellow, Completed/blue, On Hold/gray)
    - Show resource count summary
    - _Requirements: 1.2, 1.7_

  - [x] 15.3 Create ResourceDistributionChart component (ECharts pie)
    - Display resource distribution by type
    - Show resource count per type
    - Implement hover tooltips with percentages
    - _Requirements: 2.1, 2.4_

  - [x] 15.4 Create UtilizationTrendChart component (ECharts line)
    - Display 30-day trend data
    - Show lines for each resource type
    - _Requirements: 2.2, 2.4_

  - [x] 15.5 Create BudgetVisualization component
    - Show allocated vs available budget bars
    - Display utilization percentage
    - Show warning/error indicators
    - _Requirements: 1.6, 2.3_

  - [x] 15.6 Create MetricsCard components
    - Reusable card for key metrics
    - Display value, label, trend (if applicable)
    - _Requirements: 1.2_

  - [x] 15.7 Implement chart refresh with TanStack Query
    - Set up query with 30-second stale time
    - Implement real-time updates without page reload
    - _Requirements: 1.8, 2.6_

  - [ ]* 15.8 Write unit tests for dashboard components
    - Test chart rendering with mock data
    - Test status color coding
    - _Requirements: 1.1_

- [x] 16. Checkpoint - Dashboard and basic CRUD
  - [x] 16.1 Verify database connectivity and schema
    - Run migrations and verify tables exist
    - Test basic CRUD operations

  - [x] 16.2 Verify authentication flow end-to-end
    - Test login, token generation, logout

  - [x] 16.3 Verify project and resource CRUD
    - Create, read, update, delete projects and resources
    - Verify soft deletes work correctly

  - [x] 16.4 Verify dashboard displays correctly
    - Load dashboard, verify metrics display
    - Check performance (should load in <2 seconds)

  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Excel import backend - Parsing, validation, processing
  - [ ] 17.1 Create Excel file parsing utilities
    - Read .xlsx and .xls files using openpyxl/pandas
    - Extract headers and data rows
    - _Requirements: 9.2_

  - [ ] 17.2 Create import preview endpoint
    - POST /api/import/preview - Parse file and return preview
    - Validate file format and required columns
    - Return first 100 rows with validation status
    - _Requirements: 9.3, 9.4_

  - [ ] 17.3 Implement import validation logic
    - Validate column headers against asset type fields
    - Check data types per field
    - Apply custom field validation rules
    - Check budget constraints
    - _Requirements: 9.4, 9.5_

  - [ ] 17.4 Create import execution service
    - Implement background job for large imports
    - Process up to 10,000 records within 30 seconds
    - Create resource records in database
    - Assign to specified project
    - _Requirements: 9.6, 9.10_

  - [ ] 17.5 Create import status endpoint
    - GET /api/import/status/{job-id} - Return progress
    - Implement job tracking and progress reporting
    - _Requirements: 9.7_

  - [ ] 17.6 Create import report generation
    - Summarize successful imports, skipped rows, errors
    - Include row numbers and error reasons
    - _Requirements: 9.8_

  - [ ]* 17.7 Write property tests for import pipeline
    - **Property 17: Excel file format validation**
    - **Property 18: Excel column mapping is consistent**
    - **Validates: Requirements 9.1, 9.2_

- [x] 18. Excel import frontend - Upload, preview, status display
  - [ ] 18.1 Create ImportPage layout
    - Implement upload interface with drag-and-drop
    - Show file selection and project selection
    - _Requirements: 9.1_

  - [ ] 18.2 Implement file upload and preview
    - Upload file to POST /api/import/preview
    - Display preview table with validation status
    - Show row count and error count
    - _Requirements: 9.4, 9.5_

  - [ ] 18.3 Create import confirmation flow
    - Display preview results
    - Allow user to confirm import
    - Disable import if validation errors exist
    - _Requirements: 9.5, 9.6_

  - [ ] 18.4 Implement import progress tracking
    - Poll import status endpoint
    - Display progress bar
    - Show completion summary with results
    - _Requirements: 9.8_

  - [ ] 18.5 Create error report display
    - Display detailed error messages per row
    - Show problematic values and reasons
    - Allow user to download error report
    - _Requirements: 9.5_

  - [ ]* 18.6 Write unit tests for import components
    - Test file upload handling
    - Test preview display
    - _Requirements: 9.1_

- [x] 19. Audit logging backend - Implementation, log retrieval, queries
  - [ ] 19.1 Create audit log model and service
    - Create AuditLog SQLAlchemy model
    - Implement audit logging for create/update/delete operations
    - Capture old_values and new_values as JSON
    - _Requirements: 11.8, 19.1_

  - [ ] 19.2 Implement audit log integration
    - Add audit log creation to all resource mutations
    - Record user ID, timestamp, IP address
    - _Requirements: 19.1_

  - [ ] 19.3 Create audit log retrieval endpoint
    - GET /api/audit-logs - List logs with filtering
    - Support filtering by user, entity type, date range
    - Return with pagination
    - _Requirements: 19.8_

  - [ ] 19.4 Implement audit log retention policy
    - Maintain logs for at least 12 months
    - Implement log archive strategy
    - Protect logs from unauthorized access
    - _Requirements: 19.6, 19.7_

  - [ ]* 19.5 Write unit tests for audit logging
    - Test audit log creation on mutations
    - Test log retrieval filtering
    - _Requirements: 19.1_

- [x] 20. Budget tracking implementation - Allocation, calculations, constraints
  - [ ] 20.1 Implement budget calculation service
    - Calculate project allocated_budget from active allocations
    - Calculate remaining_budget
    - Track utilization percentage
    - _Requirements: 10.1, 10.2_

  - [ ] 20.2 Implement budget constraint enforcement
    - Block resource allocation when budget at 100%
    - Return 409 Conflict with error message
    - _Requirements: 10.4, 10.5_

  - [ ] 20.3 Implement allocation history tracking
    - Record cost_at_allocation for historical accuracy
    - Track deallocation dates
    - _Requirements: 10.8_

  - [ ] 20.4 Create budget metrics endpoints
    - GET /api/projects/{id}/budget-status - Budget details
    - GET /api/budget/summary - Organization-wide budget summary
    - _Requirements: 10.2, 10.3_

  - [ ]* 20.5 Write property tests for budget tracking
    - **Property 19: Budget constraints prevent over-allocation**
    - **Validates: Requirements 10.2, 10.4_

- [x] 21. Error handling and validation frontend - Messages, highlighting, UX
  - [ ] 21.1 Create global error boundary component
    - Catch React errors and display error page
    - Show error reference number for support
    - _Requirements: 15.5_

  - [ ] 21.2 Implement form field error display
    - Highlight invalid fields with red borders
    - Display field-specific error messages
    - Clear errors when field is corrected
    - _Requirements: 15.3_

  - [ ] 21.3 Implement API error handling
    - Parse API error responses
    - Display user-friendly error messages
    - Preserve form data on validation failure
    - _Requirements: 15.1, 15.6_

  - [ ] 21.4 Create validation utility functions
    - Email format validation
    - Required field checking
    - Min/max length validation
    - Custom validation rules
    - _Requirements: 15.1_

  - [ ]* 21.5 Write unit tests for error handling
    - Test error boundary rendering
    - Test form validation display
    - _Requirements: 15.1_

- [x] 22. Error handling and validation backend - Pydantic, response formats
  - [ ] 22.1 Create standardized error response format
    - Define ErrorResponse schema with error, code, details, timestamp
    - Implement consistent error formatting
    - _Requirements: 12.6, 15.1_

  - [ ] 22.2 Implement input validation with Pydantic
    - Create strict Pydantic models for all requests
    - Validate data types, required fields, constraints
    - Return 400 Bad Request with validation errors
    - _Requirements: 15.1, 15.2_

  - [ ] 22.3 Create custom validation rules
    - Implement async validators for database constraints
    - Validate unique emails, project names, etc.
    - Return specific error messages
    - _Requirements: 8.1, 8.2_

  - [ ] 22.4 Implement exception handlers
    - Create handlers for common exceptions
    - Return appropriate HTTP status codes
    - Log errors with context (never log passwords)
    - _Requirements: 15.2, 19.2_

  - [ ]* 22.5 Write unit tests for validation
    - Test Pydantic model validation
    - Test error response formatting
    - _Requirements: 15.1_

- [x] 23. Security hardening - Input sanitization, CSRF, XSS, rate limiting
  - [ ] 23.1 Implement SQL injection prevention
    - Use SQLAlchemy ORM exclusively (no raw SQL)
    - Use parameterized queries for all database operations
    - _Requirements: 14.4_

  - [ ] 23.2 Implement XSS prevention
    - Sanitize all user input with DOMPurify on frontend
    - Use React's built-in XSS protection
    - Escape special characters in output
    - _Requirements: 14.5_

  - [ ] 23.3 Implement CSRF protection
    - Generate CSRF tokens on login
    - Validate tokens on state-changing requests
    - Return 403 for invalid CSRF tokens
    - _Requirements: 14.6_

  - [ ] 23.4 Implement rate limiting on authentication
    - Limit login attempts to 5 per minute per IP
    - Implement exponential backoff after failed attempts
    - Return 429 Too Many Requests when limit exceeded
    - _Requirements: 14.8_

  - [ ] 23.5 Implement content security policy headers
    - Set CSP headers on all responses
    - Restrict script sources, style sources
    - _Requirements: 14.2_

  - [ ]* 23.6 Write security tests
    - Test SQL injection protection
    - Test XSS payload handling
    - _Requirements: 14.1_

- [x] 24. API endpoints and documentation - Complete REST API, Swagger docs
  - [ ] 24.1 Create OpenAPI/Swagger documentation
    - Generate Swagger/OpenAPI spec from FastAPI
    - Include request/response examples for all endpoints
    - Document error codes and status codes
    - _Requirements: 12.10_

  - [ ] 24.2 Implement API response pagination
    - Add limit and offset parameters to list endpoints
    - Include total count in response metadata
    - Default limit: 50, max: 100
    - _Requirements: 12.7_

  - [ ] 24.3 Implement API sorting and filtering
    - Add sort_by, sort_order, filter parameters
    - Support filtering by multiple fields
    - _Requirements: 12.8_

  - [ ] 24.4 Implement response compression
    - Enable gzip compression for responses >5MB
    - Compress JSON responses
    - _Requirements: 12.9_

  - [ ] 24.5 Create API client library for frontend
    - Generated or manual TypeScript client
    - Type-safe API calls
    - _Requirements: 12.1, 12.2_

  - [ ]* 24.6 Write API endpoint tests
    - Test all CRUD endpoints
    - Test filtering and pagination
    - _Requirements: 12.1_

- [x] 25. Checkpoint - Core features complete
  - [ ] 25.1 Verify all CRUD operations work end-to-end
    - Projects, resources, users, asset types

  - [ ] 25.2 Verify import pipeline works
    - Test Excel file import with sample data

  - [ ] 25.3 Verify RBAC enforcement
    - Test role-based access to different features

  - [ ] 25.4 Verify security measures are in place
    - Test HTTPS requirement, CSRF tokens, input sanitization

  - Ensure all tests pass, ask the user if questions arise.

- [x] 26. Reporting and export functionality - CSV, PDF export
  - [ ] 26.1 Create export service on backend
    - Implement CSV export for project and resource lists
    - Implement PDF export with headers, footers, formatting
    - _Requirements: 17.1, 17.2_

  - [ ] 26.2 Implement data filtering for export
    - Export current filtered dataset
    - Include all visible columns plus timestamp and exporter
    - _Requirements: 17.3, 17.4_

  - [ ] 26.3 Create chart export for PDF
    - Embed ECharts as images in PDF export
    - Include dashboard metrics and visualizations
    - _Requirements: 17.6_

  - [ ] 26.4 Create export buttons in frontend
    - Add export functionality to list pages
    - Add dashboard chart export
    - _Requirements: 17.1_

  - [ ] 26.5 Implement export performance optimization
    - Complete exports for 10,000 records within 30 seconds
    - Stream large exports instead of loading into memory
    - _Requirements: 17.7_

  - [ ]* 26.6 Write unit tests for export functionality
    - Test CSV generation
    - Test PDF export
    - _Requirements: 17.1_

- [x] 27. Session management and idle timeout - Frontend implementation
  - [ ] 27.1 Implement session timeout warnings
    - Show warning modal at 30-minute idle
    - Display countdown to auto-logout
    - _Requirements: 20.4_

  - [ ] 27.2 Implement auto-logout
    - Auto-logout after 35-minute idle
    - Clear token and redirect to login
    - _Requirements: 20.5_

  - [ ] 27.3 Implement keep-alive mechanism
    - Keep-alive request on user activity
    - Reset idle timer on each activity
    - _Requirements: 20.3, 20.4_

  - [ ] 27.4 Implement multiple session support
    - Allow user to be logged in from multiple devices
    - Each session has independent token
    - _Requirements: 20.6_

  - [ ]* 27.5 Write unit tests for session management
    - Test idle timeout detection
    - Test keep-alive mechanism
    - _Requirements: 20.1_

- [x] 28. UI/UX refinement - Responsive design, accessibility, polish
  - [ ] 28.1 Implement responsive design
    - Test on desktop (1024px), tablet, mobile (375px)
    - Ensure all functions accessible on all screen sizes
    - _Requirements: 16.1_

  - [ ] 28.2 Implement accessibility features
    - Add ARIA labels to all interactive elements
    - Ensure proper heading hierarchy
    - Add alt text to images
    - Support keyboard navigation
    - _Requirements: 16.7, 16.8_

  - [ ] 28.3 Add loading indicators and skeletons
    - Display loading skeleton while data fetches
    - Show progress indicators during imports
    - _Requirements: 16.9_

  - [ ] 28.4 Implement tooltips and help
    - Add tooltips to complex UI elements
    - Add help section in main menu
    - _Requirements: 16.6, 16.10_

  - [ ] 28.5 Add consistent status indicators
    - Color-code status: Active/green, Pending/yellow, Completed/blue, On Hold/gray
    - Display status badges consistently
    - _Requirements: 1.7, 16.5_

  - [ ] 28.6 Implement navigation consistency
    - Accessible main menu within 2 clicks
    - Consistent navigation across pages
    - _Requirements: 16.2, 16.3_

  - [ ]* 28.7 Write UI component tests
    - Test responsive layout
    - Test accessibility attributes
    - _Requirements: 16.1_

- [x] 29. Performance optimization - Caching, indexing, optimization
  - [ ] 29.1 Implement database query caching
    - Cache asset type schemas with 24-hour TTL
    - Cache user permissions with 1-hour TTL
    - Invalidate caches on updates
    - _Requirements: 13.6_

  - [ ] 29.2 Implement API response caching
    - Cache dashboard metrics with 30-second TTL
    - Cache project lists with 5-minute TTL
    - Implement cache invalidation on mutations
    - _Requirements: 13.6, 2.6_

  - [ ] 29.3 Verify database indexing is optimal
    - Verify all necessary indexes exist
    - Analyze slow queries (>1 second)
    - _Requirements: 13.5, 19.5_

  - [ ] 29.4 Implement frontend code splitting
    - Split routes into separate chunks
    - Lazy load components
    - _Requirements: 13.1_

  - [ ] 29.5 Implement frontend image optimization
    - Use WebP format with fallbacks
    - Lazy load images
    - _Requirements: 13.1_

  - [ ]* 29.6 Write performance tests
    - Test dashboard load time <2 seconds
    - Test search results <1 second
    - _Requirements: 13.1_

- [x] 30. Final integration and testing - Full system validation
  - [ ] 30.1 Run all property-based tests
    - Execute all 24 correctness properties
    - Verify all properties pass
    - _Requirements: 11.1_

  - [ ] 30.2 Run full integration test suite
    - Test complete workflows end-to-end
    - Test import pipeline with realistic data
    - Test concurrent user scenarios
    - _Requirements: 13.1, 13.4_

  - [ ] 30.3 Verify deployment readiness
    - Check environment configuration
    - Test health check endpoints
    - Verify logging and monitoring
    - _Requirements: 13.1, 19.1_

  - [ ] 30.4 Verify documentation completeness
    - API documentation with Swagger
    - Database schema documentation
    - Deployment guide
    - _Requirements: 12.10_

  - [ ] 30.5 Performance and load testing
    - Verify 100 concurrent users supported
    - Verify performance meets all timing requirements
    - _Requirements: 13.2, 13.4_

  - [ ]* 30.6 Write final integration tests
    - End-to-end test scenarios
    - Database migration tests
    - _Requirements: 13.1_

- [x] 31. Enhanced audit logging - Multiple operation types and compliance
  - [ ] 31.1 Create extended AuditLog schema
    - Add fields: ip_address, user_agent, status, error_message, execution_time_ms
    - Support operation types: LOGIN, LOGOUT, IMPORT, EXPORT, REPORT_DOWNLOAD, ROLE_CHANGE
    - _Requirements: 19.1, 19.2_

  - [ ] 31.2 Implement audit logging for all operations
    - Add middleware to capture login/logout events
    - Add decorators to capture import/export operations
    - Log role changes with old/new values
    - _Requirements: 19.1_

  - [ ] 31.3 Create compliance report generation
    - Generate audit reports by date range, user, operation type
    - Export audit logs with filters
    - _Requirements: 19.3, 19.4_

  - [ ] 31.4 Implement audit log protection
    - Encrypt sensitive audit data at rest
    - Enforce immutability (prevent modification)
    - Admin-only access to audit logs
    - _Requirements: 19.4_

  - [ ]* 31.5 Write unit tests for audit logging
    - Test all operation types recorded
    - Test compliance report generation
    - _Requirements: 19.1_

- [x] 32. Notification system - Backend service
  - [ ] 32.1 Create Notification model and service
    - Create notifications table with type, priority, status
    - Implement notification creation service
    - _Requirements: 21.1, 21.2, 21.3_

  - [ ] 32.2 Implement notification triggers
    - Budget threshold reached (80%, 100%)
    - Warranty expiring (30 days)
    - Import failed/completed
    - Project delayed
    - _Requirements: 21.1, 21.4, 21.5_

  - [ ] 32.3 Create notification delivery service
    - In-app notifications (database)
    - Email notifications (async queue)
    - Retry logic with exponential backoff
    - _Requirements: 21.6, 21.8_

  - [ ] 32.4 Create notification endpoints
    - GET /api/notifications - List unread notifications
    - PUT /api/notifications/{id}/read - Mark as read
    - DELETE /api/notifications/{id} - Dismiss notification
    - GET /api/notifications/preferences - User preferences
    - PUT /api/notifications/preferences - Update preferences
    - _Requirements: 21.7, 21.8_

  - [ ]* 32.5 Write unit tests for notifications
    - Test notification creation and delivery
    - Test retry logic
    - _Requirements: 21.1_

- [x] 33. Notification system - Frontend UI
  - [ ] 33.1 Create notification components
    - Toast notification component (temporary)
    - Notification center component (permanent)
    - Notification badge (unread count)
    - _Requirements: 21.6, 21.7_

  - [ ] 33.2 Implement notification polling
    - Poll /api/notifications every 30 seconds
    - Display new notifications in real-time
    - Mark as read when viewed
    - _Requirements: 21.7_

  - [ ] 33.3 Create notification preference UI
    - Settings page for notification types
    - Toggle delivery channels (in-app, email)
    - _Requirements: 21.8_

  - [ ]* 33.4 Write UI tests for notifications
    - Test toast display
    - Test notification center
    - _Requirements: 21.1_

- [x] 34. JSONB optimization - Custom fields
  - [ ] 34.1 Update database schema to use JSONB
    - Modify resources.custom_field_values to JSONB
    - Modify custom_fields.options to JSONB
    - Modify custom_fields.validation_rules to JSONB
    - _Requirements: 24.1, 24.2_

  - [ ] 34.2 Create GIN indexes on JSONB columns
    - Create GIN index on resources.custom_field_values
    - Create GIN indexes on frequently queried paths
    - _Requirements: 24.3, 24.4_

  - [ ] 34.3 Implement JSONB query builders
    - Create utilities for JSONB @> operator (contains)
    - Create utilities for JSONB -> operator (extract)
    - Create utilities for JSONB ->> operator (extract text)
    - _Requirements: 24.6_

  - [ ] 34.4 Optimize resource filtering
    - Update resource filter endpoints to use JSONB operators
    - Test performance (<1 second for 100k records)
    - _Requirements: 24.4, 24.5_

  - [ ]* 34.5 Write performance tests for JSONB
    - Test JSONB query performance with GIN indexes
    - Benchmark before/after optimization
    - _Requirements: 24.4_

- [x] 35. Reporting engine - Backend service
  - [ ] 35.1 Create report template system
    - Create report_templates table with versioning
    - Implement template CRUD endpoints
    - Support template parameters
    - _Requirements: 23.1, 23.2_

  - [ ] 35.2 Create report generation service
    - Implement report rendering pipeline
    - Support section types: summary, table, chart, recommendation
    - Execute queries and AI agents for each section
    - _Requirements: 23.3, 23.4_

  - [ ] 35.3 Implement report export formats
    - PDF export with charts, headers, footers
    - XLSX export with multiple sheets
    - DOCX export with formatted sections
    - CSV export for data
    - HTML export for web viewing
    - _Requirements: 23.3, 23.4, 23.5_

  - [ ] 35.4 Create report scheduling service
    - Schedule recurring reports (daily, weekly, monthly)
    - Implement report queue/job processing
    - Send email with report attachment
    - _Requirements: 23.8_

  - [ ] 35.5 Create report endpoints
    - GET /api/reports/templates - List templates
    - POST /api/reports/generate - Generate report on-demand
    - POST /api/reports/schedule - Schedule recurring report
    - GET /api/reports/generated - List generated reports
    - GET /api/reports/generated/{id}/download - Download report
    - _Requirements: 23.1, 23.2_

  - [ ]* 35.6 Write unit tests for report generation
    - Test template rendering
    - Test export formats
    - _Requirements: 23.3_

- [x] 36. Reporting engine - Frontend UI
  - [ ] 36.1 Create report template selection UI
    - Display available templates
    - Show template parameters for user input
    - _Requirements: 23.1, 23.2_

  - [ ] 36.2 Create report generation and download UI
    - Generate report on-demand
    - Show generation progress
    - Provide download link when ready
    - _Requirements: 23.2, 23.3_

  - [ ] 36.3 Create report scheduling UI
    - Schedule recurring reports
    - Specify recipients and format
    - _Requirements: 23.8_

  - [ ] 36.4 Create report management UI
    - List previously generated reports
    - Download/delete reports
    - View report metadata
    - _Requirements: 23.7_

  - [ ]* 36.5 Write UI tests for report components
    - Test template selection
    - Test report download
    - _Requirements: 23.1_

- [x] 37. AI/NLQ service layer - Setup and infrastructure
  - [ ] 37.1 Set up LLM service integration
    - Configure LLM provider (OpenAI/Anthropic/self-hosted)
    - Create LLM client with error handling
    - Implement retry logic and fallback
    - _Requirements: 22.1, 22.2_

  - [ ] 37.2 Implement SQL agent
    - Parse natural language queries
    - Generate SELECT-only SQL queries
    - Validate queries (no INSERT/UPDATE/DELETE)
    - Execute and return results
    - _Requirements: 22.1, 22.2_

  - [ ] 37.3 Implement schema context provider
    - Dynamically build schema description for LLM
    - Include table names, column names, relationships
    - Update schema context on entity changes
    - _Requirements: 22.7_

  - [ ] 37.4 Create query safety validator
    - Validate only SELECT queries allowed
    - Sanitize query results (remove sensitive data)
    - Implement query timeouts
    - _Requirements: 22.2, 22.3_

  - [ ]* 37.5 Write unit tests for SQL agent
    - Test query generation accuracy
    - Test SQL validation
    - _Requirements: 22.1_

- [x] 38. AI/RAG pipeline - Embeddings and retrieval
  - [ ] 38.1 Implement embedding service
    - Create embeddings for resources, queries, patterns
    - Use OpenAI embedding API or self-hosted
    - Cache embeddings in PostgreSQL
    - _Requirements: 22.5, 22.8_

  - [ ] 38.2 Create RAG search service
    - Search for similar historical queries
    - Find related resources by embedding similarity
    - Return top-K matches with scores
    - _Requirements: 22.5, 22.6_

  - [ ] 38.3 Implement embedding cache and refresh
    - Store embeddings in embedding_cache table
    - Expire and refresh embeddings periodically
    - Implement efficient vector search
    - _Requirements: 22.8_

  - [ ] 38.4 Create report agent
    - Generate insights from query results
    - Generate recommendations for optimization
    - Generate forecasts from historical data
    - _Requirements: 22.9, 22.10_

  - [ ]* 38.5 Write unit tests for RAG pipeline
    - Test embedding generation
    - Test RAG search
    - _Requirements: 22.5_

- [x] 39. AI/NLQ frontend - Natural language query interface
  - [ ] 39.1 Create NLQ query interface
    - Text input for natural language queries
    - Query suggestions from saved templates
    - _Requirements: 22.1_

  - [ ] 39.2 Implement query execution UI
    - Submit query to /api/ai/query endpoint
    - Display results in table/chart format
    - Show execution time and query used
    - _Requirements: 22.2, 22.3_

  - [ ] 39.3 Create insights panel
    - Display AI-generated insights below results
    - Show recommendations for optimization
    - Show forecast predictions
    - _Requirements: 22.9, 22.10_

  - [ ] 39.4 Implement query history and templates
    - Save successful queries as templates
    - Show query history
    - Allow reuse of saved queries
    - _Requirements: 22.14, 22.15_

  - [ ]* 39.5 Write UI tests for NLQ interface
    - Test query submission
    - Test result display
    - _Requirements: 22.1_

- [x] 40. Checkpoint 3 - Enterprise features complete
  - [ ] 40.1 Verify notification system works end-to-end
    - Test budget threshold notification
    - Test warranty expiring notification
    - Test import failure notification

  - [ ] 40.2 Verify reporting engine
    - Generate report in each format (PDF, XLSX, DOCX)
    - Verify scheduled reports work

  - [ ] 40.3 Verify JSONB performance
    - Test filtering by custom fields is <1 second
    - Verify GIN indexes are being used

  - [ ] 40.4 Verify AI/NLQ system
    - Test natural language query translation
    - Test RAG retrieval
    - Test report generation with AI insights

  - [ ] 40.5 Verify enhanced audit logging
    - Verify all operation types logged
    - Verify compliance report generation

  - Ensure all tests pass, ask the user if questions arise.

- [ ] 41. Final checkpoint - System complete with enterprise features
  - [ ] 41.1 Verify all 24 requirements implemented
    - Check off each requirement against implementation

  - [ ] 41.2 Verify all tests pass
    - Unit tests, property tests, integration tests

  - [ ] 41.3 Verify performance metrics
    - Dashboard <2 seconds
    - Search <1 second
    - JSONB queries <1 second for 100k records
    - Concurrent users: 100+

  - [ ] 41.4 Verify compliance requirements
    - All operations logged
    - 24-month audit trail maintained
    - Sensitive data protected

  - [ ] 41.5 Verify AI/reporting features
    - Natural language queries work
    - Reports generate in all formats
    - Notifications deliver reliably

  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test tasks and can be skipped for faster MVP
- Each implementation task references specific requirements for traceability
- Property-based tests validate universal correctness properties defined in the design
- Unit tests validate specific functionality and edge cases
- Checkpoints ensure incremental validation throughout implementation
- Database schema must be created before any backend operations
- Frontend and backend can be developed in parallel after project setup
- Excel import is a complex feature; integration test thoroughly
- Security measures should be implemented incrementally, not as an afterthought


## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1.1", "2.1"]
    },
    {
      "id": 1,
      "tasks": ["3.1", "3.2", "3.3", "3.4"]
    },
    {
      "id": 2,
      "tasks": ["4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "5.1", "5.2", "5.3", "5.4"]
    },
    {
      "id": 3,
      "tasks": ["3.5", "4.7", "5.5"]
    },
    {
      "id": 4,
      "tasks": ["6.1", "6.2", "6.3", "9.1", "9.2", "9.3", "9.4"]
    },
    {
      "id": 5,
      "tasks": ["6.4", "9.5"]
    },
    {
      "id": 6,
      "tasks": ["7.1", "7.2", "7.3", "7.4", "11.1", "11.2", "11.3", "11.4"]
    },
    {
      "id": 7,
      "tasks": ["7.5", "11.5"]
    },
    {
      "id": 8,
      "tasks": ["8.1", "8.2", "8.3", "8.4", "10.1", "10.2", "10.3", "12.1", "12.2", "12.3", "12.4"]
    },
    {
      "id": 9,
      "tasks": ["8.5", "10.4", "12.5"]
    },
    {
      "id": 10,
      "tasks": ["13.1", "13.2", "13.3", "13.4"]
    },
    {
      "id": 11,
      "tasks": ["13.5"]
    },
    {
      "id": 12,
      "tasks": ["14.1", "14.2", "14.3", "14.4", "14.5"]
    },
    {
      "id": 13,
      "tasks": ["14.6"]
    },
    {
      "id": 14,
      "tasks": ["15.1", "15.2", "15.3", "15.4", "15.5", "15.6", "15.7"]
    },
    {
      "id": 15,
      "tasks": ["15.8"]
    },
    {
      "id": 16,
      "tasks": ["17.1", "17.2", "17.3", "17.4", "17.5", "17.6"]
    },
    {
      "id": 17,
      "tasks": ["17.7"]
    },
    {
      "id": 18,
      "tasks": ["18.1", "18.2", "18.3", "18.4", "18.5"]
    },
    {
      "id": 19,
      "tasks": ["18.6"]
    },
    {
      "id": 20,
      "tasks": ["19.1", "19.2", "19.3", "19.4"]
    },
    {
      "id": 21,
      "tasks": ["19.5"]
    },
    {
      "id": 22,
      "tasks": ["20.1", "20.2", "20.3", "20.4"]
    },
    {
      "id": 23,
      "tasks": ["20.5"]
    },
    {
      "id": 24,
      "tasks": ["21.1", "21.2", "21.3", "21.4", "22.1", "22.2", "22.3", "22.4"]
    },
    {
      "id": 25,
      "tasks": ["21.5", "22.5"]
    },
    {
      "id": 26,
      "tasks": ["23.1", "23.2", "23.3", "23.4", "23.5"]
    },
    {
      "id": 27,
      "tasks": ["23.6"]
    },
    {
      "id": 28,
      "tasks": ["24.1", "24.2", "24.3", "24.4", "24.5"]
    },
    {
      "id": 29,
      "tasks": ["24.6"]
    },
    {
      "id": 30,
      "tasks": ["26.1", "26.2", "26.3", "26.4", "26.5"]
    },
    {
      "id": 31,
      "tasks": ["26.6"]
    },
    {
      "id": 32,
      "tasks": ["27.1", "27.2", "27.3", "27.4"]
    },
    {
      "id": 33,
      "tasks": ["27.5"]
    },
    {
      "id": 34,
      "tasks": ["28.1", "28.2", "28.3", "28.4", "28.5", "28.6"]
    },
    {
      "id": 35,
      "tasks": ["28.7"]
    },
    {
      "id": 36,
      "tasks": ["29.1", "29.2", "29.3", "29.4", "29.5"]
    },
    {
      "id": 37,
      "tasks": ["29.6"]
    },
    {
      "id": 38,
      "tasks": ["30.1", "30.2", "30.3", "30.4", "30.5"]
    },
    {
      "id": 39,
      "tasks": ["30.6"]
    }
  ]
}
```
