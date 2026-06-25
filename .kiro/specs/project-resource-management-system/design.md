# Design Document: Project Resource Management System (PRMS)

## 1. System Architecture Overview

The PRMS follows a multi-layered architecture ensuring separation of concerns, scalability, and maintainability:

### 1.1 Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│          Presentation Layer (React Frontend)        │
│  - Components, Pages, UI State Management           │
│  - TanStack Query for server state                  │
│  - Tailwind CSS + ShadCN UI Components              │
└────────────────────┬────────────────────────────────┘
                     │ HTTPS/JSON
┌────────────────────▼────────────────────────────────┐
│       API Layer (FastAPI REST Endpoints)            │
│  - Route handlers, request/response validation      │
│  - Authentication/Authorization middleware          │
│  - Error handling and status code mapping           │
└────────────────────┬────────────────────────────────┘
                     │ ORM/SQL
┌────────────────────▼────────────────────────────────┐
│      Business Logic Layer (Services)                │
│  - Project management service                       │
│  - Resource management service                      │
│  - Asset type and schema management                 │
│  - Budget tracking and allocation                   │
│  - Authentication and authorization                 │
│  - Import processing pipeline                       │
│  - Notification service                             │
│  - Audit logging service                            │
│  - Report generation service                        │
│  - AI/NLQ service layer (NEW)                       │
└────────────────────┬────────────────────────────────┘
                     │ SQL Queries
┌────────────────────▼────────────────────────────────┐
│    Data Access Layer (SQLAlchemy ORM)               │
│  - Database models and relationships                │
│  - Query optimization                               │
│  - Transaction management                           │
│  - JSONB query builders                             │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│    AI/ML Services Layer (Optional)                  │
│  - LLM Integration (SQL Agent)                      │
│  - RAG Pipeline (Embeddings, Vector DB)             │
│  - Report Agent (NLG)                               │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│         PostgreSQL Database                         │
│  - Projects, Resources, Asset Types                 │
│  - Custom Fields (JSONB), Audit Logs                │
│  - Notifications, Generated Reports                 │
│  - Report Templates, Embeddings Cache               │
└─────────────────────────────────────────────────────┘
```

### 1.2 Key Design Principles

- **Separation of Concerns**: Each layer has distinct responsibilities
- **Type Safety**: TypeScript frontend, Python type hints, SQLAlchemy models
- **Security First**: RBAC enforced at API layer, input validation at all boundaries
- **Dynamic Schema**: Asset types and custom fields stored in database, no code changes required
- **Performance**: Caching, indexing (including GIN indexes on JSONB), pagination, async processing
- **Audit Trail**: All mutations logged with user context, timestamps, and compliance fields
- **AI-Ready**: Embedding pipeline and LLM service integration points defined
- **Notification-First**: Event-driven notifications for critical business events


## 2. Frontend Component Architecture

### 2.1 Component Structure

```
src/
├── pages/
│   ├── Dashboard.tsx          # Main dashboard with charts
│   ├── ProjectList.tsx        # Project CRUD listing
│   ├── ProjectDetail.tsx      # Individual project view
│   ├── ResourceList.tsx       # Resource CRUD listing
│   ├── ResourceForm.tsx       # Create/Edit resource form
│   ├── ImportPage.tsx         # Excel import interface
│   ├── UserManagement.tsx     # Admin user management
│   ├── AssetTypeManagement.tsx # Admin asset type config
│   └── Login.tsx              # Authentication
├── components/
│   ├── Layout/
│   │   ├── MainLayout.tsx
│   │   ├── Navbar.tsx
│   │   └── Sidebar.tsx
│   ├── Dashboard/
│   │   ├── ProjectOverviewCard.tsx
│   │   ├── ResourceDistributionChart.tsx
│   │   ├── UtilizationTrendChart.tsx
│   │   ├── BudgetVisualization.tsx
│   │   └── MetricsCard.tsx
│   ├── Forms/
│   │   ├── ProjectForm.tsx
│   │   ├── ResourceForm.tsx
│   │   ├── AssetTypeForm.tsx
│   │   └── CustomFieldInput.tsx
│   ├── Tables/
│   │   ├── ProjectTable.tsx
│   │   ├── ResourceTable.tsx
│   │   └── DataTable.tsx (generic)
│   └── Common/
│       ├── Dialog/
│       ├── Loading/
│       ├── ErrorBoundary.tsx
│       └── ConfirmDialog.tsx
├── hooks/
│   ├── useAuth.ts
│   ├── useProjects.ts
│   ├── useResources.ts
│   ├── useAssetTypes.ts
│   ├── usePagination.ts
│   └── useExport.ts
├── services/
│   ├── api.ts                 # Axios client with interceptors
│   ├── auth.ts                # Authentication API calls
│   ├── projects.ts            # Project API calls
│   ├── resources.ts           # Resource API calls
│   └── assetTypes.ts          # Asset type API calls
├── store/
│   ├── authContext.ts         # Auth state
│   ├── queryClient.ts         # TanStack Query setup
│   └── cache.ts               # Cache configuration
├── types/
│   └── index.ts               # TypeScript interfaces
├── utils/
│   ├── validation.ts
│   ├── formatting.ts
│   ├── constants.ts
│   └── errors.ts
└── styles/
    ├── globals.css            # Tailwind base
    └── theme.css              # Dark blue theme
```

### 2.2 State Management Strategy

- **Server State**: TanStack Query (React Query) for API data caching and synchronization
- **Auth State**: React Context for authenticated user info and token
- **UI State**: Component local state (useState) for UI interactions
- **Cache Strategy**: Automatic invalidation on mutations, 5-minute default stale-time

### 2.3 Key Components

**ProjectOverviewCard**: Displays project status, budget utilization, resource count, color-coded status
**ResourceDistributionChart**: ECharts pie chart showing resources by type
**UtilizationTrendChart**: ECharts line chart showing 30-day allocation trends
**CustomFieldInput**: Renders appropriate input based on field type (text, number, date, dropdown, boolean)
**DataTable**: Generic table with pagination, sorting, filtering


## 3. Backend API Design

### 3.1 REST API Endpoints

#### Authentication Endpoints
```
POST   /api/auth/login              # Login with username/password
POST   /api/auth/logout             # Logout and invalidate token
POST   /api/auth/refresh            # Refresh expired token
GET    /api/auth/me                 # Get current user info
```

#### Project Endpoints
```
GET    /api/projects                # List projects with pagination
POST   /api/projects                # Create new project
GET    /api/projects/{id}           # Get project details
PUT    /api/projects/{id}           # Update project
DELETE /api/projects/{id}           # Soft delete project
GET    /api/projects/{id}/resources # List resources in project
```

#### Resource Endpoints
```
GET    /api/resources               # List resources with filtering
POST   /api/resources               # Create new resource
GET    /api/resources/{id}          # Get resource details
PUT    /api/resources/{id}          # Update resource
DELETE /api/resources/{id}          # Soft delete resource
GET    /api/resources/{id}/history  # Get allocation history
```

#### Asset Type Endpoints
```
GET    /api/asset-types             # List asset types
POST   /api/asset-types             # Create asset type
GET    /api/asset-types/{id}        # Get asset type with schema
PUT    /api/asset-types/{id}        # Update asset type
DELETE /api/asset-types/{id}        # Mark asset type as inactive
POST   /api/asset-types/{id}/fields # Add custom field
```

#### User Management Endpoints (Admin)
```
GET    /api/users                   # List users
POST   /api/users                   # Create user
GET    /api/users/{id}              # Get user details
PUT    /api/users/{id}              # Update user
DELETE /api/users/{id}              # Archive user
PUT    /api/users/{id}/role         # Update user role
```

#### Import Endpoints
```
POST   /api/import/preview          # Preview Excel file
POST   /api/import/execute          # Execute import
GET    /api/import/status/{job-id}  # Check import status
```

#### Audit Log Endpoints
```
GET    /api/audit-logs              # List audit logs (Admin)
```

### 3.2 Request/Response Schemas

#### Project Schema
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "status": "Active|Pending|Completed|On Hold",
  "budget": 100000.00,
  "allocated_budget": 50000.00,
  "start_date": "2024-01-15",
  "end_date": "2024-12-31",
  "owner_id": "uuid",
  "resource_count": 15,
  "resources_by_type": {
    "Personnel": 10,
    "Equipment": 5
  },
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-20T14:30:00Z"
}
```

#### Resource Schema
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "asset_type_id": "uuid",
  "name": "string",
  "cost": 5000.00,
  "allocation_date": "2024-01-15",
  "status": "Active|Inactive",
  "custom_fields": {
    "department": "Engineering",
    "skill_level": "Senior",
    "utilization": 85
  },
  "allocation_history": [...],
  "created_by": "uuid",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-20T14:30:00Z"
}
```

#### Asset Type Schema
```json
{
  "id": "uuid",
  "name": "Personnel",
  "standard_fields": [
    { "name": "name", "type": "text", "required": true },
    { "name": "cost", "type": "number", "required": true }
  ],
  "custom_fields": [
    {
      "id": "uuid",
      "name": "department",
      "type": "dropdown",
      "required": false,
      "options": ["Engineering", "Sales", "HR"],
      "validation": {}
    }
  ],
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 3.3 Error Response Format
```json
{
  "error": "string",
  "code": "ERROR_CODE",
  "details": "string (optional)",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

### 3.4 Pagination Parameters
- `limit` (default: 50, max: 100)
- `offset` (default: 0)
- `sort_by` (default: created_at)
- `sort_order` (asc|desc)


## 4. Database Schema Design

### 4.1 Core Tables

#### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL, -- Admin, Manager, Analyst, Viewer
  is_active BOOLEAN DEFAULT true,
  last_login TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL
);
```

#### Projects Table
```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(50) NOT NULL, -- Active, Pending, Completed, On Hold
  budget DECIMAL(15, 2) NOT NULL,
  start_date DATE,
  end_date DATE,
  owner_id UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL
);
```

#### Asset Types Table
```sql
CREATE TABLE asset_types (
  id UUID PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  description TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Custom Fields Table
```sql
CREATE TABLE custom_fields (
  id UUID PRIMARY KEY,
  asset_type_id UUID NOT NULL REFERENCES asset_types(id),
  name VARCHAR(255) NOT NULL,
  field_type VARCHAR(50) NOT NULL, -- text, number, date, dropdown, boolean
  is_required BOOLEAN DEFAULT false,
  options JSONB, -- JSON array for dropdown types
  validation_rules JSONB, -- JSON object with constraints
  display_order INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(asset_type_id, name)
);
```

#### Resources Table
```sql
CREATE TABLE resources (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id),
  asset_type_id UUID NOT NULL REFERENCES asset_types(id),
  name VARCHAR(255) NOT NULL,
  cost DECIMAL(15, 2) NOT NULL,
  allocation_date DATE NOT NULL,
  status VARCHAR(50) DEFAULT 'Active',
  custom_field_values JSONB NOT NULL DEFAULT '{}', -- JSONB for efficient filtering
  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL
);
```

#### Allocations Table
```sql
CREATE TABLE allocations (
  id UUID PRIMARY KEY,
  resource_id UUID NOT NULL REFERENCES resources(id),
  project_id UUID NOT NULL REFERENCES projects(id),
  cost_at_allocation DECIMAL(15, 2) NOT NULL,
  allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deallocated_at TIMESTAMP NULL,
  created_by UUID NOT NULL REFERENCES users(id)
);
```

#### Audit Logs Table
```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  entity_type VARCHAR(100) NOT NULL, -- 'Project', 'Resource', etc.
  entity_id UUID NOT NULL,
  operation VARCHAR(20) NOT NULL, -- CREATE, UPDATE, DELETE
  old_values TEXT, -- JSON object
  new_values TEXT, -- JSON object
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ip_address VARCHAR(45)
);
```

#### Sessions Table
```sql
CREATE TABLE sessions (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  token_hash VARCHAR(255) UNIQUE NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Notifications Table (NEW)
```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  type VARCHAR(50) NOT NULL, -- budget_threshold, warranty_expiring, import_failed, etc.
  title VARCHAR(255) NOT NULL,
  message TEXT,
  is_read BOOLEAN DEFAULT false,
  priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
  action_url VARCHAR(500), -- Optional link to relevant resource
  related_entity_type VARCHAR(100), -- project, resource, import_job
  related_entity_id UUID,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  read_at TIMESTAMP NULL,
  dismissed_at TIMESTAMP NULL
);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
```

#### Report Templates Table (NEW)
```sql
CREATE TABLE report_templates (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  template_type VARCHAR(50) NOT NULL, -- project_summary, budget_analysis, etc.
  version INT DEFAULT 1,
  parameters JSONB, -- Configurable parameters
  output_format VARCHAR(20), -- pdf, xlsx, docx, csv, html
  created_by UUID NOT NULL REFERENCES users(id),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Generated Reports Table (NEW)
```sql
CREATE TABLE generated_reports (
  id UUID PRIMARY KEY,
  template_id UUID NOT NULL REFERENCES report_templates(id),
  title VARCHAR(255) NOT NULL,
  output_format VARCHAR(20) NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  file_size_bytes INT,
  parameters_used JSONB,
  generated_by UUID NOT NULL REFERENCES users(id),
  generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP, -- For temporary reports
  download_count INT DEFAULT 0
);
CREATE INDEX idx_generated_reports_template_id ON generated_reports(template_id);
CREATE INDEX idx_generated_reports_generated_by ON generated_reports(generated_by);
```

#### Enhanced Audit Logs Table (UPDATED)
```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  entity_type VARCHAR(100) NOT NULL, -- Project, Resource, User, Import, Export, etc.
  entity_id UUID NOT NULL,
  operation VARCHAR(20) NOT NULL, -- CREATE, UPDATE, DELETE, LOGIN, LOGOUT, IMPORT, EXPORT, REPORT_DOWNLOAD, ROLE_CHANGE
  old_values JSONB, -- JSON object
  new_values JSONB, -- JSON object
  ip_address VARCHAR(45),
  user_agent VARCHAR(500),
  status VARCHAR(20) DEFAULT 'success', -- success, failure
  error_message TEXT,
  execution_time_ms INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_operation ON audit_logs(operation);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

#### Embeddings Cache Table (NEW - for AI/RAG)
```sql
CREATE TABLE embedding_cache (
  id UUID PRIMARY KEY,
  entity_type VARCHAR(100) NOT NULL, -- resource, project, query_pattern
  entity_id UUID NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR(1536), -- OpenAI embeddings dimension
  model_version VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP -- For periodic refresh
);
CREATE INDEX idx_embedding_cache_entity ON embedding_cache(entity_type, entity_id);
```

### 4.2 Indexes for Performance

```sql
-- Projects indexes
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_deleted_at ON projects(deleted_at);

-- Resources indexes
CREATE INDEX idx_resources_project_id ON resources(project_id);
CREATE INDEX idx_resources_asset_type_id ON resources(asset_type_id);
CREATE INDEX idx_resources_status ON resources(status);
CREATE INDEX idx_resources_deleted_at ON resources(deleted_at);
CREATE INDEX idx_resources_allocation_date ON resources(allocation_date);

-- GIN Indexes for JSONB custom field queries (NEW)
CREATE INDEX idx_resources_custom_fields_gin ON resources USING GIN(custom_field_values);

-- Custom fields indexes
CREATE INDEX idx_custom_fields_asset_type_id ON custom_fields(asset_type_id);

-- Audit logs indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_operation ON audit_logs(operation);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Sessions indexes
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- Notifications indexes (NEW)
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_type ON notifications(type);

-- Report indexes (NEW)
CREATE INDEX idx_generated_reports_template_id ON generated_reports(template_id);
CREATE INDEX idx_generated_reports_generated_by ON generated_reports(generated_by);

-- Embedding cache indexes (NEW)
CREATE INDEX idx_embedding_cache_entity ON embedding_cache(entity_type, entity_id);
```

### 4.3 Referential Integrity

- Resources must reference existing projects and asset types
- Custom fields must reference existing asset types
- Allocations must reference existing resources and projects
- Audit logs maintain referential integrity for user tracking
- Sessions reference users and maintain temporal constraints


## 5. Authentication and Authorization

### 5.1 Authentication Flow

```
1. User submits login form (username/password)
   ↓
2. Server validates credentials against bcrypt hash
   ↓
3. If valid: Generate JWT token (24-hour expiration)
   ↓
4. Return token to frontend (HttpOnly cookie or localStorage)
   ↓
5. Frontend includes token in Authorization header for subsequent requests
   ↓
6. Server validates token signature and expiration on each request
   ↓
7. If expired: Return 401, frontend redirects to login
```

### 5.2 RBAC Model

| Permission | Admin | Manager | Analyst | Viewer |
|-----------|-------|---------|---------|--------|
| View Dashboard | ✓ | ✓ | ✓ | ✓* |
| Create Project | ✓ | ✓ | ✗ | ✗ |
| Edit Project | ✓ | ✓* | ✗ | ✗ |
| Delete Project | ✓ | ✓* | ✗ | ✗ |
| Create Resource | ✓ | ✓ | ✗ | ✗ |
| Edit Resource | ✓ | ✓ | ✗ | ✗ |
| Delete Resource | ✓ | ✓ | ✗ | ✗ |
| Import Resources | ✓ | ✓ | ✗ | ✗ |
| Manage Asset Types | ✓ | ✗ | ✗ | ✗ |
| Manage Users | ✓ | ✗ | ✗ | ✗ |
| View Audit Logs | ✓ | ✗ | ✗ | ✗ |

*Manager can only view/edit their own projects; Viewer only assigned projects

### 5.3 Authorization Enforcement

```python
# Middleware pattern for FastAPI
@app.middleware("http")
async def verify_auth(request: Request, call_next):
    token = extract_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"error": "No token"})
    
    user = verify_token(token)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})
    
    request.state.user = user
    return await call_next(request)

# Decorator for role-based access
def require_role(*roles):
    async def check_role(request: Request):
        if request.state.user.role not in roles:
            raise HTTPException(status_code=403)
    return check_role
```

### 5.4 Session Management

- Token expiration: 24 hours
- Idle timeout warning: 30 minutes
- Idle logout: 35 minutes
- Session invalidated on logout: Immediate
- Token refresh: Available via refresh endpoint


## 6. Data Import Pipeline

### 6.1 Excel Import Process

```
1. User uploads .xlsx or .xls file
   ↓
2. Server reads file headers
   ↓
3. Map Excel columns to asset type fields based on field names
   ↓
4. Validate file structure (required columns present)
   ↓
5. Parse all rows with data type conversion
   ↓
6. Display preview (first 100 rows) with validation status
   ↓
7. If preview accepted:
   - Start background job
   - Process all rows (max 10,000)
   - Apply custom field validation
   - Create resource records
   - Record audit logs
   ↓
8. Return summary report (successful, skipped, errors)
```

### 6.2 Import Validation

- Column name matching (case-insensitive)
- Data type validation per field
- Required field check
- Custom field validation rules applied
- Cost calculation and budget constraint check
- Duplicate detection

### 6.3 Error Handling

- Invalid data types → Skip row, record error
- Missing required field → Skip row, record error
- Budget exceeded → Skip row, offer option to continue
- Import errors are collected and reported without failing entire import

## 7. Budget Tracking and Allocation

### 7.1 Budget Allocation Logic

```
When resource allocated:
  project.allocated_budget += resource.cost
  project.remaining_budget = project.budget - project.allocated_budget
  
When resource deallocated:
  project.allocated_budget -= resource.cost_at_allocation
  project.remaining_budget = project.budget - project.allocated_budget

Utilization percentage:
  (allocated_budget / budget) * 100

Budget warnings:
  80% utilization → Yellow warning (trigger notification)
  100% utilization → Red, block new allocations (trigger urgent notification)
```

### 7.2 Allocation History

Track all allocation changes:
- allocation_date
- deallocation_date (if applicable)
- cost_at_allocation
- created_by user

## 8. Notification System (NEW)

### 8.1 Notification Types and Triggers

```
1. BUDGET_THRESHOLD_80
   - Trigger: project.allocated_budget >= 0.80 * project.budget
   - Recipients: project owner, managers
   - Priority: high

2. BUDGET_THRESHOLD_100
   - Trigger: project.allocated_budget >= project.budget
   - Recipients: project owner, admins
   - Priority: urgent

3. WARRANTY_EXPIRING
   - Trigger: asset.warranty_end_date - today <= 30 days
   - Recipients: resource custodian, asset manager
   - Priority: normal

4. IMPORT_FAILED
   - Trigger: Excel import job completes with errors
   - Recipients: user who initiated import
   - Priority: high

5. IMPORT_COMPLETED
   - Trigger: Excel import job completes successfully
   - Recipients: user who initiated import
   - Priority: normal

6. PROJECT_DELAYED
   - Trigger: project.status changed to delayed/at-risk
   - Recipients: project owner, managers
   - Priority: high

7. REPORT_GENERATED
   - Trigger: Scheduled/on-demand report completed
   - Recipients: report recipient users
   - Priority: normal

8. RESOURCE_ALLOCATION_FAILED
   - Trigger: Resource allocation rejected due to budget
   - Recipients: attempting user
   - Priority: normal
```

### 8.2 Notification Delivery

- **In-App**: Toast notifications + notification center
- **Email**: For critical alerts (urgent priority)
- **Dashboard Badge**: Unread notification count
- **User Preferences**: Configurable per notification type

### 8.3 Notification Lifecycle

```
Created → Sent → Read/Dismissed → Archived
```

## 9. AI/NLQ Service Layer (NEW)

### 9.1 Natural Language Query Processing

```
User Input: "Show me all overbudget projects"
    ↓
LLM Service (SQL Agent):
  - Parse intent: query resources
  - Identify entities: projects, budget
  - Generate SQL: SELECT * FROM projects WHERE allocated_budget > budget
  - Validate: Only SELECT queries allowed
    ↓
Database Query:
  - Execute safe SQL
  - Return results within 3 seconds
    ↓
Response: 
  - Structured JSON
  - Metadata: execution time, row count
```

### 9.2 AI Service Components

```
services/
├── ai/
│   ├── sql_agent.py
│   │   - parse_natural_language(query: str) → SQL
│   │   - validate_query(sql: str) → bool (SELECT only)
│   │   - execute_query(sql: str) → List[dict]
│   │
│   ├── rag_agent.py
│   │   - embed_query(text: str) → Vector
│   │   - search_similar(vector: Vector, top_k: int) → List[QueryPattern]
│   │   - generate_insights() → List[str]
│   │
│   ├── report_agent.py
│   │   - generate_summary(data: List[dict]) → str
│   │   - generate_recommendations(data: List[dict]) → List[str]
│   │   - generate_forecast(historical_data: List[dict]) → Forecast
│   │
│   └── embeddings.py
│       - create_embedding(text: str) → Vector(1536)
│       - cache_embedding(entity_id: str, vector: Vector)
│       - search_embeddings(query_vector: Vector) → List[Match]
```

### 9.3 LLM Integration Points

- **Model**: OpenAI GPT-4 or self-hosted LLM (configurable)
- **Schema Context**: Dynamic schema passed with each query
- **Safety**: Only SELECT queries, no sensitive data in responses
- **Caching**: Embedding vectors cached in PostgreSQL
- **Fallback**: Graceful degradation if LLM unavailable

## 10. Reporting Engine (NEW)

### 10.1 Report Template Structure

```
{
  "id": "uuid",
  "name": "Project Budget Analysis",
  "version": 1,
  "sections": [
    {
      "type": "summary",
      "title": "Executive Summary",
      "content_template": "Project {{project_name}} is at {{utilization}}% budget utilization"
    },
    {
      "type": "table",
      "title": "Resource Breakdown",
      "query": "SELECT * FROM resources WHERE project_id = {{project_id}}"
    },
    {
      "type": "chart",
      "title": "Budget Trends",
      "chart_type": "line",
      "data_query": "SELECT * FROM allocation_history WHERE project_id = {{project_id}}"
    },
    {
      "type": "recommendation",
      "title": "AI Recommendations",
      "ai_agent": "generate_recommendations"
    }
  ],
  "parameters": {
    "project_id": "uuid",
    "date_range": "date_range"
  }
}
```

### 10.2 Report Generation Pipeline

```
1. User selects template + parameters
   ↓
2. Validate parameters against template schema
   ↓
3. Execute queries for each section
   ↓
4. Generate AI insights (if applicable)
   ↓
5. Render to selected format (PDF/XLSX/DOCX)
   ↓
6. Store in generated_reports table
   ↓
7. Send notification with download link
```

### 10.3 Supported Formats

- **PDF**: Charts as images, formatted sections, company header/footer
- **XLSX**: Multiple sheets (summary, details, charts)
- **DOCX**: Formatted sections, embedded charts, narrative summaries
- **CSV**: Flat data export
- **HTML**: Web-viewable version

## 11. Enhanced Audit Logging for Compliance (UPDATED)

### 11.1 Audit Log Operations

Extended from original CRUD to include:

```
- CREATE: Resource/Project/User created
- UPDATE: Entity field changed
- DELETE: Soft delete performed
- LOGIN: User authenticated successfully
- LOGOUT: User session ended
- IMPORT: Excel import operation (success/failure)
- EXPORT: Data export operation
- REPORT_DOWNLOAD: Report accessed/downloaded
- ROLE_CHANGE: User role modified
- CONFIG_CHANGE: System configuration updated
```

### 11.2 Compliance Fields

Each audit log includes:

```
{
  "id": UUID,
  "user_id": UUID,
  "operation": "string", // One of above
  "entity_type": "string",
  "entity_id": "UUID",
  "old_values": JSONB, // For updates
  "new_values": JSONB, // For updates/creates
  "status": "success|failure",
  "error_message": "string", // If failed
  "ip_address": "string",
  "user_agent": "string",
  "execution_time_ms": int,
  "created_at": timestamp
}
```

### 11.3 Government Compliance

- **Retention**: 24 months (configurable per jurisdiction)
- **Encryption**: At-rest encryption for sensitive data
- **Immutability**: Audit logs protected from modification
- **Access Control**: Only Admins can view/export
- **Export**: Compliance reports with date ranges, user activity, change history

### 8.1 Input Validation Strategy

- **Frontend**: Real-time validation, client-side error messages
- **API Layer**: Schema validation (Pydantic models), business logic validation
- **Database Layer**: Constraints and triggers for integrity

### 8.2 Error Response Hierarchy

```
Level 1: Validation errors (400)
  - Missing required fields
  - Invalid data types
  - Constraint violations

Level 2: Authorization errors (401/403)
  - Invalid credentials
  - Insufficient permissions
  - Expired token

Level 3: Not found errors (404)
  - Resource doesn't exist
  - Project not found

Level 4: Conflict errors (409)
  - Unique constraint violation
  - Budget exceeded
  - Project archived

Level 5: Server errors (500)
  - Unexpected exceptions
  - Database connection failures
  - Log with error reference number
```

### 8.3 Custom Field Validation

```python
class ValidationRule:
  field_type: "text" | "number" | "date" | "dropdown" | "boolean"
  is_required: bool
  min_length: Optional[int]
  max_length: Optional[int]
  min_value: Optional[float]
  max_value: Optional[float]
  regex_pattern: Optional[str]
  allowed_values: Optional[List[str]]
```

## 9. Performance Optimization

### 9.1 Caching Strategy

- Asset type schemas: 24-hour cache (invalidate on update)
- User permissions: 1-hour cache (invalidate on role change)
- Project list: 5-minute cache (invalidate on create/update)
- Resource list: 1-minute cache (invalidate on create/update)
- Dashboard metrics: 30-second cache

### 9.2 Database Optimization

- Connection pooling (max 20 connections)
- Query result pagination (default 50, max 100)
- Lazy loading of relationships
- Indexed search columns
- Soft deletes prevent expensive migrations

### 9.3 Frontend Optimization

- Code splitting by route
- Image optimization with WebP
- Lazy loading of components
- Virtual scrolling for large lists
- Request batching in TanStack Query


## 10. Security Considerations

### 10.1 Password Security

- Hash algorithm: bcrypt with salt (rounds: 12)
- Never store plain text passwords
- Minimum 8 characters, recommend 12+
- Password reset generates temporary token (1-hour expiration)
- User must create new password on first login after reset

### 10.2 Data Transmission

- All endpoints require HTTPS/TLS
- Certificate pinning for sensitive operations
- No sensitive data in URLs or query parameters

### 10.3 Input Security

- SQL Injection prevention: Use SQLAlchemy ORM with parameterized queries
- XSS prevention: Sanitize all user input, use DOMPurify on frontend
- CSRF protection: CSRF tokens on state-changing requests
- File upload validation: Only .xlsx/.xls, file size limit 10MB

### 10.4 Access Control

- RBAC enforced at API layer
- Row-level security: Users can only access assigned projects
- Admin audit: All admin actions logged
- API keys optional for programmatic access (Future enhancement)

### 10.5 Sensitive Data Handling

- Passwords: Never logged, hashed in database
- Tokens: HttpOnly cookies preferred over localStorage
- Audit logs: Protected from user modification
- No sensitive data in error messages (generic messages shown to users)

## 11. Logging and Monitoring

### 11.1 Log Levels

- **DEBUG**: Development only, variable states
- **INFO**: User actions, successful operations
- **WARNING**: Performance issues, deprecated features
- **ERROR**: Failures, exceptions with context
- **CRITICAL**: System failures, security breaches

### 11.2 Audit Logging

All create/update/delete operations logged with:
- User ID
- Timestamp
- Entity type and ID
- Old and new values (JSON)
- IP address (if available)

### 11.3 Performance Monitoring

- Log slow queries (>1 second)
- Monitor API response times
- Track memory usage and connection pool
- Alert on error rate spikes
- Dashboard performance metrics

## 12. Testing Strategy

### 12.1 Unit Tests

- Service layer business logic
- Validation rules and constraint checks
- Data transformation functions
- Component rendering with different props

### 12.2 Integration Tests

- API endpoint functionality with database
- Authentication and authorization flows
- Import pipeline with sample Excel files
- Budget calculation accuracy

### 12.3 Property-Based Tests

- Correctness properties (detailed in Correctness Properties section)
- Mutation invariants
- Round-trip transformations
- State consistency checks

## 13. Deployment Considerations

### 13.1 Environment Configuration

```python
# .env example
DATABASE_URL=postgresql://user:pass@host:5432/prms
JWT_SECRET_KEY=<generated-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
FRONTEND_URL=https://prms.example.com
CORS_ORIGINS=https://prms.example.com
LOG_LEVEL=INFO
```

### 13.2 Database Migrations

- Use Alembic for schema version control
- Test migrations on staging before production
- Maintain backward compatibility where possible
- Soft deletes enable safe migrations

### 13.3 Health Checks

- Database connectivity
- API responsiveness
- Cache connectivity (if using Redis)
- Disk space availability


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Dashboard displays only accessible projects for non-admin users

*For any* authenticated user with Analyst or Viewer role, the Dashboard SHALL display only projects explicitly assigned to that user, while Admin and Manager users see all projects.

**Validates: Requirements 1.5**

### Property 2: Resource type counts are accurate

*For any* project on the Dashboard, the count of active resources by type SHALL equal the result of filtering the project's resources by asset type and status.

**Validates: Requirements 1.3**

### Property 3: Dashboard reflects concurrent changes

*For any* change made by another user (resource allocation, project update, etc.), a subsequent Dashboard refresh SHALL reflect that change without requiring page navigation.

**Validates: Requirements 1.8**

### Property 4: Resource utilization trends are accurately calculated

*For any* 30-day period, the Dashboard trend chart values SHALL match the sum of daily resource allocations during that period, grouped by resource type.

**Validates: Requirements 2.2**

### Property 5: Chart updates occur within real-time threshold

*For any* Dashboard metric update (resource allocation, budget change), the corresponding chart SHALL refresh within 1 second without requiring page reload.

**Validates: Requirements 2.6**

### Property 6: Authentication is required for all system access

*For any* request to any protected endpoint, the system SHALL return 401 Unauthorized if no valid authentication credentials are provided.

**Validates: Requirements 3.1**

### Property 7: Session tokens have correct expiration

*For any* successful user login, the system SHALL create a session token that remains valid for exactly 24 hours from creation and becomes invalid after that duration.

**Validates: Requirements 3.2, 20.1**

### Property 8: Unauthorized access is blocked with 403 response

*For any* request attempting to access a resource without required RBAC permissions, the system SHALL return 403 Forbidden regardless of the resource type or user role.

**Validates: Requirements 3.3**

### Property 9: Role-based permissions are consistently enforced

*For any* RBAC-protected operation (create project, edit resource, manage users), the system SHALL enforce permissions according to the role matrix and reject unauthorized attempts with 403.

**Validates: Requirements 3.5, 3.6, 3.7, 3.8**

### Property 10: Expired sessions redirect to login on next action

*For any* request made with an expired session token, the system SHALL redirect the user to the login page and require re-authentication.

**Validates: Requirements 3.9, 20.2**

### Property 11: Resource creation validates all required fields

*For any* resource creation attempt with missing required fields according to the asset type schema, the system SHALL reject the creation and display a validation error without persisting the resource.

**Validates: Requirements 6.1, 8.2**

### Property 12: Created resources receive unique identifiers and metadata

*For any* resource successfully created, the system SHALL assign a UUID that is unique across all resources, record the creator's user ID, and record the creation timestamp.

**Validates: Requirements 6.2**

### Property 13: Budget updates follow resource allocation

*For any* resource allocation to a project, the project's allocated_budget SHALL increase by the resource cost, and remaining_budget SHALL decrease accordingly.

**Validates: Requirements 6.4, 10.1**

### Property 14: Soft deletes preserve data integrity

*For any* deleted resource, the system SHALL set deleted_at timestamp rather than removing the record, and subsequent queries SHALL exclude soft-deleted resources unless explicitly querying deleted items.

**Validates: Requirements 6.5, 11.3**

### Property 15: Dynamic asset type schema discovery works for resource creation

*For any* asset type with defined standard and custom fields, when a Manager creates a resource of that type, the system SHALL dynamically load the schema and present all applicable fields without code deployment.

**Validates: Requirements 7.2**

### Property 16: Custom field validation rules are enforced

*For any* custom field with defined validation rules (required, min/max, regex), the system SHALL apply those rules during resource creation and reject invalid entries with specific error messages.

**Validates: Requirements 8.1, 8.2**

### Property 17: Excel file format validation

*For any* Excel file upload, the system SHALL reject files that are not .xlsx or .xls format and display a format error to the user.

**Validates: Requirements 9.1**

### Property 18: Excel column mapping is consistent

*For any* Excel import with columns named identically to asset type fields (case-insensitive), the system SHALL map those columns to the corresponding asset type fields consistently across all rows.

**Validates: Requirements 9.2**

### Property 19: Budget constraints prevent over-allocation

*For any* project with allocated_budget at 100% of budget, the system SHALL reject all subsequent resource allocation attempts and return a 409 Conflict error.

**Validates: Requirements 10.2**

### Property 20: Data persistence round-trip

*For any* resource created and persisted to PostgreSQL, a subsequent query for that resource by ID SHALL return the identical data (all field values, user context, timestamp) without data loss or modification.

**Validates: Requirements 11.1**

### Property 21: Updates record complete change metadata

*For any* resource update operation, the system SHALL record the old and new values in the audit log along with the user ID and timestamp, creating an immutable change history.

**Validates: Requirements 11.2**

### Property 22: API authorization is consistent with RBAC

*For any* REST API request with a given user role, the system SHALL enforce the same RBAC permissions as the web interface and return 401/403 errors for unauthorized requests.

**Validates: Requirements 12.3, 12.4**

### Property 23: Passwords are hashed, never stored plain text

*For any* user account in the system, the password_hash column in the users table SHALL contain a bcrypt hash, never a plain text password, and login validation SHALL compare against the hash.

**Validates: Requirements 14.1**

### Property 24: Password validation uses secure hashing

*For any* login attempt, the system SHALL validate the provided password by comparing its bcrypt hash against the stored hash, ensuring no plain text comparison occurs.

**Validates: Requirements 14.2**
