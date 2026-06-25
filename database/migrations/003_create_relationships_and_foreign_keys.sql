-- Task 3.2: Create relationships and foreign keys
-- This migration adds the allocations and audit_logs tables for budget tracking
-- and change history. Note: Foreign key constraints are already created in migration 001_create_core_tables.sql

-- ============================================================================
-- NOTE: Foreign Key Constraints Status
-- ============================================================================
-- The following foreign keys are already defined in migration 001:
-- ✓ projects.owner_id → users.id (RESTRICT)
-- ✓ resources.project_id → projects.id (RESTRICT) 
-- ✓ resources.asset_type_id → asset_types.id (RESTRICT)
-- ✓ resources.created_by → users.id (RESTRICT)
-- ✓ custom_fields.asset_type_id → asset_types.id (CASCADE)
--
-- IMPORTANT: As per requirements, resources should CASCADE on deletion from projects
-- This will be addressed if needed in a schema update migration

-- ============================================================================
-- 1. CREATE ALLOCATIONS TABLE (for budget tracking)
-- ============================================================================

CREATE TABLE allocations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_id UUID NOT NULL,
  project_id UUID NOT NULL,
  cost_at_allocation DECIMAL(15, 2) NOT NULL,
  allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deallocated_at TIMESTAMP NULL,
  created_by UUID NOT NULL,
  CONSTRAINT fk_allocations_resource_id FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE,
  CONSTRAINT fk_allocations_project_id FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  CONSTRAINT fk_allocations_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
);

-- Create indexes on allocations for query performance
CREATE INDEX idx_allocations_resource_id ON allocations(resource_id);
CREATE INDEX idx_allocations_project_id ON allocations(project_id);
CREATE INDEX idx_allocations_allocated_at ON allocations(allocated_at);
CREATE INDEX idx_allocations_deallocated_at ON allocations(deallocated_at);

-- ============================================================================
-- 2. CREATE AUDIT_LOGS TABLE (for change history and compliance)
-- ============================================================================

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  entity_type VARCHAR(100) NOT NULL,
  entity_id UUID NOT NULL,
  operation VARCHAR(50) NOT NULL CHECK (operation IN ('CREATE', 'UPDATE', 'DELETE', 'IMPORT', 'EXPORT', 'LOGIN', 'LOGOUT', 'ROLE_CHANGE', 'REPORT_DOWNLOAD', 'CONFIG_CHANGE')),
  old_values JSONB,
  new_values JSONB,
  ip_address VARCHAR(45),
  user_agent VARCHAR(500),
  status VARCHAR(20) DEFAULT 'success' CHECK (status IN ('success', 'failure')),
  error_message TEXT,
  execution_time_ms INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_audit_logs_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes on audit_logs for query performance and compliance
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_operation ON audit_logs(operation);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_status ON audit_logs(status);

-- ============================================================================
-- 3. CREATE INDEXES ON FOREIGN KEY COLUMNS FOR PERFORMANCE
-- ============================================================================

-- Note: Most indexes on foreign keys are already created in migration 001
-- Adding only additional composite indexes for query performance

-- ============================================================================
-- 4. CREATE COMPOSITE INDEXES FOR COMMON QUERIES
-- ============================================================================

-- Composite index for common resource filtering
CREATE INDEX idx_resources_project_status ON resources(project_id, status);

-- Composite index for allocation queries
CREATE INDEX idx_allocations_project_allocated ON allocations(project_id, allocated_at);

-- Composite index for audit log searches
CREATE INDEX idx_audit_logs_entity_operation ON audit_logs(entity_type, operation, created_at);

-- ============================================================================
-- Verification Queries (optional - run separately)
-- ============================================================================
-- Run these queries to verify referential integrity:
--
-- SELECT * FROM information_schema.table_constraints
-- WHERE constraint_type = 'FOREIGN KEY' AND table_name IN ('resources', 'projects', 'custom_fields', 'allocations', 'audit_logs');
--
-- SELECT * FROM pg_indexes
-- WHERE tablename IN ('resources', 'projects', 'custom_fields', 'allocations', 'audit_logs');
