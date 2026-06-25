-- PostgreSQL Migration: Create core database tables for PRMS
-- Timestamp: 2024-01-15
-- Description: Create users, projects, asset_types, custom_fields, and resources tables with proper types and constraints

-- Enable uuid-ossp extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM types
CREATE TYPE user_role AS ENUM ('Admin', 'Manager', 'Analyst', 'Viewer');
CREATE TYPE project_status AS ENUM ('Active', 'Pending', 'Completed', 'On Hold');
CREATE TYPE resource_status AS ENUM ('Active', 'Inactive', 'Archived');
CREATE TYPE custom_field_type AS ENUM ('text', 'number', 'date', 'dropdown', 'boolean');

-- ============================================================================
-- USERS table
-- ============================================================================
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  username VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role user_role NOT NULL DEFAULT 'Viewer',
  is_active BOOLEAN NOT NULL DEFAULT true,
  last_login TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_deleted_at ON users(deleted_at);

-- ============================================================================
-- PROJECTS table
-- ============================================================================
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  status project_status NOT NULL DEFAULT 'Active',
  budget DECIMAL(15, 2) NOT NULL,
  allocated_budget DECIMAL(15, 2) NOT NULL DEFAULT 0,
  start_date DATE,
  end_date DATE,
  owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_deleted_at ON projects(deleted_at);
CREATE INDEX idx_projects_created_at ON projects(created_at);

-- ============================================================================
-- ASSET_TYPES table
-- ============================================================================
CREATE TABLE asset_types (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) UNIQUE NOT NULL,
  description TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_asset_types_is_active ON asset_types(is_active);
CREATE INDEX idx_asset_types_name ON asset_types(name);

-- ============================================================================
-- CUSTOM_FIELDS table
-- ============================================================================
CREATE TABLE custom_fields (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  asset_type_id UUID NOT NULL REFERENCES asset_types(id) ON DELETE CASCADE,
  field_name VARCHAR(255) NOT NULL,
  field_type custom_field_type NOT NULL,
  is_required BOOLEAN NOT NULL DEFAULT false,
  options JSONB NULL,
  validation_rules JSONB NULL,
  display_order INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(asset_type_id, field_name)
);

CREATE INDEX idx_custom_fields_asset_type_id ON custom_fields(asset_type_id);
CREATE INDEX idx_custom_fields_field_type ON custom_fields(field_type);

-- ============================================================================
-- RESOURCES table
-- ============================================================================
CREATE TABLE resources (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
  asset_type_id UUID NOT NULL REFERENCES asset_types(id) ON DELETE RESTRICT,
  cost DECIMAL(15, 2) NOT NULL,
  status resource_status NOT NULL DEFAULT 'Active',
  allocation_date DATE NOT NULL,
  custom_field_values JSONB NOT NULL DEFAULT '{}',
  created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_resources_project_id ON resources(project_id);
CREATE INDEX idx_resources_asset_type_id ON resources(asset_type_id);
CREATE INDEX idx_resources_status ON resources(status);
CREATE INDEX idx_resources_deleted_at ON resources(deleted_at);
CREATE INDEX idx_resources_allocation_date ON resources(allocation_date);
CREATE INDEX idx_resources_created_by ON resources(created_by);
CREATE INDEX idx_resources_created_at ON resources(created_at);

-- GIN Index for efficient JSONB queries on custom_field_values
CREATE INDEX idx_resources_custom_fields_gin ON resources USING GIN(custom_field_values);

-- Verify all tables were created successfully
-- Note: When this migration is run, the following tables should be created:
-- - users: 13 columns, soft delete support
-- - projects: 10 columns, soft delete support, budget tracking
-- - asset_types: 5 columns
-- - custom_fields: 8 columns with JSONB support
-- - resources: 10 columns, soft delete support, JSONB custom field values

-- ============================================================================
-- Referential Integrity Constraints Summary
-- ============================================================================
-- - projects.owner_id → users.id (RESTRICT on delete)
-- - resources.project_id → projects.id (RESTRICT on delete)
-- - resources.asset_type_id → asset_types.id (RESTRICT on delete)
-- - resources.created_by → users.id (RESTRICT on delete)
-- - custom_fields.asset_type_id → asset_types.id (CASCADE on delete)
--
-- Soft Delete Columns (all timestamped):
-- - users.deleted_at
-- - projects.deleted_at
-- - resources.deleted_at
-- ============================================================================
