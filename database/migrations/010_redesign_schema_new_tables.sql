-- Database Schema Redesign Migration
-- Creates new table structure for template-driven asset management system

-- ============================================================================
-- 1. ROLES TABLE - Predefined user roles
-- ============================================================================
CREATE TABLE roles (
  id SERIAL PRIMARY KEY,
  role_name VARCHAR(50) UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert predefined roles
INSERT INTO roles (role_name, description) VALUES
  ('Super Admin', 'Full system access and configuration'),
  ('Admin', 'Administrative access with some restrictions'),
  ('Project Manager', 'Project management and oversight'),
  ('Engineer', 'Technical user with asset management'),
  ('Viewer', 'Read-only access to projects and assets'),
  ('Auditor', 'Audit and compliance focused access');

-- ============================================================================
-- 2. TEMPLATES TABLE - Workbook format definitions
-- ============================================================================
CREATE TABLE templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_name VARCHAR(255) UNIQUE NOT NULL,
  description TEXT,
  version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
  client_type VARCHAR(100) NOT NULL,
  is_default BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  template_config JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default templates
INSERT INTO templates (template_name, description, version, client_type, is_default, template_config) VALUES
  ('Navy Standard', 'Standard template for Navy projects', '1.0.0', 'Navy Standard', true, '{"sheets": ["SEAW", "Servers", "Storage", "Firewall", "L3 Switch", "L2 Switch", "KVM Switch", "PC Workstation", "Desktop"]}'),
  ('BEL Standard', 'Bharat Electronics Limited standard template', '1.0.0', 'BEL Standard', false, '{"sheets": ["Summary", "Server", "Storage", "Network", "Workstation"]}'),
  ('HAL Standard', 'Hindustan Aeronautics Limited standard template', '1.0.0', 'HAL Standard', false, '{"sheets": ["Project Info", "Computing Assets", "Storage Systems", "Network Equipment"]}');

-- ============================================================================
-- 3. RESOURCE TYPES TABLE - Represents workbook tabs
-- ============================================================================
CREATE TABLE resource_types (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) UNIQUE NOT NULL,
  display_name VARCHAR(255) NOT NULL,
  icon VARCHAR(50),
  display_order INTEGER NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default resource types
INSERT INTO resource_types (name, display_name, icon, display_order) VALUES
  ('server', 'Server', 'server', 1),
  ('storage', 'Storage', 'hard-drive', 2),
  ('firewall', 'Firewall', 'shield', 3),
  ('l3_switch', 'L3 Switch', 'network-wired', 4),
  ('l2_switch', 'L2 Switch', 'network-wired', 5),
  ('kvm_switch', 'KVM Switch', 'monitor', 6),
  ('pc_workstation', 'PC Workstation', 'desktop-computer', 7),
  ('desktop', 'Desktop', 'computer', 8);

-- ============================================================================
-- 4. TEMPLATE RESOURCE TYPES TABLE - Links templates to resource types
-- ============================================================================
CREATE TABLE template_resource_types (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id UUID NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
  resource_type_id UUID NOT NULL REFERENCES resource_types(id) ON DELETE CASCADE,
  display_order INTEGER NOT NULL,
  is_required BOOLEAN DEFAULT false,
  UNIQUE(template_id, resource_type_id)
);

-- Link Navy Standard template to resource types
INSERT INTO template_resource_types (template_id, resource_type_id, display_order, is_required)
SELECT 
  t.id,
  rt.id,
  rt.display_order,
  true
FROM templates t, resource_types rt
WHERE t.template_name = 'Navy Standard';

-- ============================================================================
-- 5. SHEET MAPPING TABLE - Maps Excel sheet names to resource types
-- ============================================================================
CREATE TABLE sheet_mapping (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id UUID NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
  sheet_name VARCHAR(255) NOT NULL,
  resource_type_id UUID NOT NULL REFERENCES resource_types(id) ON DELETE CASCADE,
  display_order INTEGER NOT NULL,
  is_summary_sheet BOOLEAN DEFAULT false,
  UNIQUE(template_id, sheet_name)
);

-- Insert sheet mappings for Navy Standard
WITH navy_template AS (SELECT id FROM templates WHERE template_name = 'Navy Standard')
INSERT INTO sheet_mapping (template_id, sheet_name, resource_type_id, display_order, is_summary_sheet)
SELECT 
  nt.id,
  CASE rt.name
    WHEN 'server' THEN 'Servers'
    WHEN 'storage' THEN 'Storage'
    WHEN 'firewall' THEN 'Firewall'
    WHEN 'l3_switch' THEN 'L3 Switch'
    WHEN 'l2_switch' THEN 'L2 Switch'
    WHEN 'kvm_switch' THEN 'KVM Switch'
    WHEN 'pc_workstation' THEN 'PC Workstation'
    WHEN 'desktop' THEN 'Desktop'
  END,
  rt.id,
  rt.display_order,
  false
FROM navy_template nt, resource_types rt;

-- Add SEAW summary sheet mapping
INSERT INTO sheet_mapping (template_id, sheet_name, resource_type_id, display_order, is_summary_sheet)
SELECT id, 'SEAW', (SELECT id FROM resource_types LIMIT 1), 0, true
FROM templates WHERE template_name = 'Navy Standard';

-- ============================================================================
-- 6. RESOURCE FIELDS TABLE - Dynamic field definitions
-- ============================================================================
CREATE TABLE resource_fields (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_type_id UUID NOT NULL REFERENCES resource_types(id) ON DELETE CASCADE,
  field_name VARCHAR(100) NOT NULL,
  display_name VARCHAR(255) NOT NULL,
  data_type VARCHAR(50) NOT NULL CHECK (data_type IN ('text', 'number', 'date', 'dropdown', 'boolean', 'decimal', 'email', 'url')),
  unit VARCHAR(20),
  is_required BOOLEAN DEFAULT false,
  is_unique BOOLEAN DEFAULT false,
  default_value TEXT,
  validation_regex TEXT,
  options JSONB,
  display_order INTEGER NOT NULL,
  is_visible BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(resource_type_id, field_name)
);

-- Add common server fields
WITH server_type AS (SELECT id FROM resource_types WHERE name = 'server')
INSERT INTO resource_fields (resource_type_id, field_name, display_name, data_type, display_order, is_required) 
SELECT st.id, field_name, display_name, data_type, display_order, is_required
FROM server_type st, (VALUES
  ('processor', 'Processor', 'text', 1, true),
  ('cpu_cores', 'CPU Cores', 'number', 2, false),
  ('ram_gb', 'RAM (GB)', 'number', 3, true),
  ('storage_gb', 'Storage (GB)', 'number', 4, true),
  ('operating_system', 'Operating System', 'text', 5, false),
  ('ip_address', 'IP Address', 'text', 6, false)
) AS fields(field_name, display_name, data_type, display_order, is_required);

-- ============================================================================
-- Create indexes for performance
-- ============================================================================
CREATE INDEX idx_templates_client_type ON templates(client_type);
CREATE INDEX idx_templates_is_active ON templates(is_active);
CREATE INDEX idx_resource_types_display_order ON resource_types(display_order);
CREATE INDEX idx_template_resource_types_template ON template_resource_types(template_id);
CREATE INDEX idx_sheet_mapping_template ON sheet_mapping(template_id);
CREATE INDEX idx_resource_fields_resource_type ON resource_fields(resource_type_id);
CREATE INDEX idx_resource_fields_display_order ON resource_fields(resource_type_id, display_order);