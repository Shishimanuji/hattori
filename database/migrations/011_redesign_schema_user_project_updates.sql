-- Database Schema Redesign Migration Part 2
-- Updates existing tables and creates new core tables

-- ============================================================================
-- 1. UPDATE USERS TABLE - Add new fields for enhanced user profile
-- ============================================================================
ALTER TABLE users 
ADD COLUMN employee_id VARCHAR(50) UNIQUE,
ADD COLUMN full_name VARCHAR(255),
ADD COLUMN phone VARCHAR(20),
ADD COLUMN department VARCHAR(100),
ADD COLUMN designation VARCHAR(100),
ADD COLUMN role_id INTEGER REFERENCES roles(id),
ADD COLUMN status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'Suspended'));

-- Migrate existing role data to role_id
UPDATE users SET role_id = (
  CASE role
    WHEN 'Admin' THEN (SELECT id FROM roles WHERE role_name = 'Admin')
    WHEN 'Manager' THEN (SELECT id FROM roles WHERE role_name = 'Project Manager')
    WHEN 'Analyst' THEN (SELECT id FROM roles WHERE role_name = 'Engineer')
    WHEN 'Viewer' THEN (SELECT id FROM roles WHERE role_name = 'Viewer')
    ELSE (SELECT id FROM roles WHERE role_name = 'Viewer')
  END
);

-- Set full_name from username initially
UPDATE users SET full_name = username WHERE full_name IS NULL;
UPDATE users SET status = CASE WHEN is_active THEN 'Active' ELSE 'Inactive' END;

-- Make role_id required after migration
ALTER TABLE users ALTER COLUMN role_id SET NOT NULL;

-- ============================================================================
-- 2. UPDATE PROJECTS TABLE - Add new fields for enhanced project tracking
-- ============================================================================
ALTER TABLE projects
ADD COLUMN project_code VARCHAR(50) UNIQUE,
ADD COLUMN client VARCHAR(255),
ADD COLUMN vendor VARCHAR(255),
ADD COLUMN location VARCHAR(255),
ADD COLUMN template_id UUID REFERENCES templates(id),
ADD COLUMN created_by UUID REFERENCES users(id);

-- Generate project codes using a temporary sequence
WITH project_rows AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as row_num
  FROM projects
  WHERE project_code IS NULL
)
UPDATE projects SET 
  project_code = 'PRJ-' || LPAD(project_rows.row_num::text, 4, '0'),
  created_by = owner_id,
  template_id = (SELECT id FROM templates WHERE template_name = 'Navy Standard' LIMIT 1)
FROM project_rows
WHERE projects.id = project_rows.id;

-- Make project_code required
ALTER TABLE projects ALTER COLUMN project_code SET NOT NULL;

-- ============================================================================
-- 3. PROJECT SUMMARY TABLE - Separate SEAW sheet data
-- ============================================================================
CREATE TABLE project_summary (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  prepared_by VARCHAR(255),
  approved_by VARCHAR(255),
  project_duration INTEGER, -- in days
  remarks TEXT,
  total_budget DECIMAL(15,2),
  completion_percentage DECIMAL(5,2) DEFAULT 0.00 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
  version VARCHAR(20) DEFAULT '1.0',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(project_id)
);

-- Migrate existing project data to project_summary
INSERT INTO project_summary (project_id, total_budget, completion_percentage)
SELECT id, budget, 0.00 FROM projects
ON CONFLICT (project_id) DO NOTHING;

-- ============================================================================
-- 4. ASSETS TABLE - Unified asset table replacing resources
-- ============================================================================
CREATE TABLE assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  resource_type_id UUID NOT NULL REFERENCES resource_types(id),
  asset_code VARCHAR(100),
  asset_name VARCHAR(255) NOT NULL,
  manufacturer VARCHAR(255),
  model VARCHAR(255),
  serial_number VARCHAR(255),
  service_tag VARCHAR(255),
  vendor VARCHAR(255),
  location VARCHAR(255),
  room_no VARCHAR(50),
  custodian_id UUID REFERENCES users(id),
  purchase_date DATE,
  installation_date DATE,
  warranty_start DATE,
  warranty_end DATE,
  cost DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  status VARCHAR(50) DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'Disposed', 'Under Repair', 'Reserved')),
  audit_status VARCHAR(50) DEFAULT 'Pending' CHECK (audit_status IN ('Pending', 'Completed', 'Overdue', 'Not Required')),
  last_audit_date DATE,
  remarks TEXT,
  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP
);

-- ============================================================================
-- 5. ASSET FIELD VALUES TABLE - EAV pattern for dynamic fields
-- ============================================================================
CREATE TABLE asset_field_values (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  resource_field_id UUID NOT NULL REFERENCES resource_fields(id) ON DELETE CASCADE,
  text_value TEXT,
  number_value DECIMAL(15,4),
  date_value DATE,
  boolean_value BOOLEAN,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(asset_id, resource_field_id)
);

-- ============================================================================
-- 6. DOCUMENTS TABLE - File attachments
-- ============================================================================
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
  document_type VARCHAR(100) NOT NULL CHECK (document_type IN ('Invoice', 'Warranty', 'Configuration', 'Drawing', 'Manual', 'Certificate', 'Other')),
  file_name VARCHAR(255) NOT NULL,
  file_path TEXT NOT NULL,
  file_size BIGINT,
  mime_type VARCHAR(100),
  uploaded_by UUID NOT NULL REFERENCES users(id),
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  description TEXT
);

-- ============================================================================
-- 7. ALERTS TABLE - Dashboard alerts
-- ============================================================================
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
  alert_type VARCHAR(100) NOT NULL CHECK (alert_type IN ('Warranty Expiry', 'Audit Due', 'Maintenance Due', 'Compliance', 'Budget', 'Other')),
  severity VARCHAR(20) NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
  title VARCHAR(255) NOT NULL,
  message TEXT NOT NULL,
  status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Acknowledged', 'Resolved', 'Dismissed')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  resolved_at TIMESTAMP,
  resolved_by UUID REFERENCES users(id),
  due_date DATE
);

-- ============================================================================
-- 8. UPDATE IMPORT HISTORY TABLE - Enhanced import tracking
-- ============================================================================
ALTER TABLE import_jobs RENAME TO import_history;

ALTER TABLE import_history
ADD COLUMN template_id UUID REFERENCES templates(id),
ADD COLUMN filename VARCHAR(255),
ADD COLUMN uploaded_by UUID REFERENCES users(id),
ADD COLUMN total_records INTEGER DEFAULT 0,
ADD COLUMN successful_records INTEGER DEFAULT 0,
ADD COLUMN failed_records INTEGER DEFAULT 0,
ADD COLUMN uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Update existing import history
UPDATE import_history SET 
  uploaded_by = created_by,
  total_records = rows_total,
  successful_records = rows_successful,
  failed_records = rows_failed,
  uploaded_at = created_at
WHERE uploaded_by IS NULL;

-- ============================================================================
-- 9. REPORT TEMPLATES TABLE - Reusable report configurations
-- ============================================================================
CREATE TABLE report_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_name VARCHAR(255) NOT NULL,
  description TEXT,
  filters_json JSONB NOT NULL DEFAULT '{}',
  columns_config JSONB NOT NULL DEFAULT '{}',
  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_public BOOLEAN DEFAULT false
);

-- ============================================================================
-- Create indexes for performance
-- ============================================================================
CREATE INDEX idx_users_employee_id ON users(employee_id);
CREATE INDEX idx_users_role_id ON users(role_id);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_department ON users(department);

CREATE INDEX idx_projects_project_code ON projects(project_code);
CREATE INDEX idx_projects_template_id ON projects(template_id);
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_client ON projects(client);

CREATE INDEX idx_project_summary_project_id ON project_summary(project_id);

CREATE INDEX idx_assets_project_id ON assets(project_id);
CREATE INDEX idx_assets_resource_type_id ON assets(resource_type_id);
CREATE INDEX idx_assets_asset_code ON assets(asset_code);
CREATE INDEX idx_assets_serial_number ON assets(serial_number);
CREATE INDEX idx_assets_status ON assets(status);
CREATE INDEX idx_assets_audit_status ON assets(audit_status);
CREATE INDEX idx_assets_custodian_id ON assets(custodian_id);
CREATE INDEX idx_assets_warranty_end ON assets(warranty_end);
CREATE INDEX idx_assets_created_by ON assets(created_by);

CREATE INDEX idx_asset_field_values_asset_id ON asset_field_values(asset_id);
CREATE INDEX idx_asset_field_values_field_id ON asset_field_values(resource_field_id);

CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_documents_asset_id ON documents(asset_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by);

CREATE INDEX idx_alerts_project_id ON alerts(project_id);
CREATE INDEX idx_alerts_asset_id ON alerts(asset_id);
CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_due_date ON alerts(due_date);

CREATE INDEX idx_import_history_project_id ON import_history(project_id);
CREATE INDEX idx_import_history_template_id ON import_history(template_id);
CREATE INDEX idx_import_history_uploaded_by ON import_history(uploaded_by);

CREATE INDEX idx_report_templates_created_by ON report_templates(created_by);
CREATE INDEX idx_report_templates_is_public ON report_templates(is_public);