# Backend Architecture Overview - PRMS

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│  (Main Entry: app/main.py - Port 8000)                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┬─────────────┬──────────────┐
        │                     │             │              │
    ┌───▼────┐          ┌─────▼──┐   ┌─────▼──┐    ┌──────▼──┐
    │ Routes │          │Services│   │Schemas │    │ Models  │
    │(API)   │          │(Logic) │   │(Validation) │(ORM)    │
    └───┬────┘          └────────┘   └────────┘    └────┬────┘
        │                                                 │
        └─────────────────────┬──────────────────────────┘
                              │
                    ┌─────────▼────────┐
                    │   PostgreSQL     │
                    │  Database        │
                    │ (automate on     │
                    │  localhost:5433) │
                    └──────────────────┘
```

## Directory Structure

```
backend/
├── app/
│   ├── core/                  # Core infrastructure
│   │   ├── config.py         # Settings from .env
│   │   └── database.py       # SQLAlchemy setup
│   │
│   ├── models/               # SQLAlchemy ORM models (16 models)
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── project.py
│   │   ├── asset.py
│   │   ├── template.py
│   │   ├── resource_type.py
│   │   ├── document.py
│   │   ├── alert.py
│   │   ├── import_job.py
│   │   ├── session.py
│   │   ├── audit_log.py
│   │   └── [legacy models...]
│   │
│   ├── schemas/              # Pydantic validation models (12 schemas)
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── project.py
│   │   ├── asset.py
│   │   ├── template.py
│   │   ├── alert.py
│   │   └── [more...]
│   │
│   ├── routes/               # API endpoints (9 route files)
│   │   ├── auth.py           # Login, register, token refresh
│   │   ├── users.py          # User management
│   │   ├── projects.py       # Project CRUD
│   │   ├── assets.py         # Asset CRUD (NEW)
│   │   ├── templates.py      # Template management (NEW)
│   │   ├── resource_types.py # Resource types (NEW)
│   │   ├── resources.py      # Resource management (legacy)
│   │   ├── dashboard.py      # Dashboard data
│   │   └── asset_types.py    # Asset type management (legacy)
│   │
│   ├── services/             # Business logic (16 services)
│   │   ├── auth_service.py          # Authentication
│   │   ├── user_service.py          # User operations
│   │   ├── project_service.py       # Project operations
│   │   ├── asset_service.py         # Asset operations (NEW)
│   │   ├── template_service.py      # Template operations (NEW)
│   │   ├── resource_type_service.py # Resource type ops (NEW)
│   │   ├── session_service.py       # Session management
│   │   ├── audit_service.py         # Audit logging
│   │   ├── dashboard_service.py     # Dashboard metrics
│   │   ├── import_service.py        # Excel import
│   │   ├── password_reset_service.py
│   │   ├── authorization_service.py # RBAC checks
│   │   └── [more...]
│   │
│   ├── utils/                # Utilities (10 utility modules)
│   │   ├── jwt_utils.py      # JWT token operations
│   │   ├── auth_utils.py     # Password hashing, validation
│   │   ├── dependencies.py   # FastAPI dependency injection
│   │   ├── exceptions.py     # Custom exceptions
│   │   ├── rbac_decorator.py # Role-based access control
│   │   ├── excel_utils.py    # Excel file parsing
│   │   └── [more...]
│   │
│   └── main.py              # FastAPI app creation & routing
│
├── tests/                    # Test suite
│   ├── conftest.py          # Pytest configuration
│   ├── test_auth_*.py
│   ├── test_rbac_*.py
│   └── [more test files]
│
├── pyproject.toml          # Poetry configuration
├── requirements.txt        # Dependencies
└── .env                    # Environment variables
```

## Core Components

### 1. **Core (app/core/)**

**config.py**
- Loads environment variables from .env
- Settings class with type hints
- Database URL, JWT secrets, timeouts, CORS config

**database.py**
- SQLAlchemy engine setup
- Session factory (SessionLocal)
- ORM declarative base
- `get_db()` dependency for FastAPI
- `init_db()` connection test
- `create_all_tables()` for schema initialization

### 2. **Models (app/models/)**

**ORM Models (16 total)**

*New Template-Driven Schema:*
- **Role** - User roles (Super Admin, Admin, Project Manager, Engineer, Viewer, Auditor)
- **User** - Enhanced user with role_id, employee_id, department, designation
- **Template** - Workbook format definitions
- **TemplateResourceType** - Template to resource type mapping
- **SheetMapping** - Excel sheet to resource type mapping
- **ResourceType** - Asset categories (Server, Storage, etc.)
- **ResourceField** - Dynamic field definitions per resource type
- **Asset** - Unified asset table (replacing resources)
- **AssetFieldValue** - EAV pattern for dynamic field storage
- **ProjectSummary** - Isolated SEAW sheet data
- **Document** - File attachments
- **Alert** - Dashboard notifications
- **ReportTemplate** - Reusable report configs

*Legacy Models (maintained for backward compatibility):*
- **Resource** - Old asset representation
- **AssetType** - Old resource category
- **CustomField** - Old field definitions
- **Session** - User session tokens
- **AuditLog** - Change audit trail
- **ImportJob/ImportHistory** - Import tracking
- **PasswordResetToken** - Password reset flow

### 3. **Schemas (app/schemas/)**

**Pydantic Validation Models (12 schemas)**

Each schema has:
- Create/Update variants (for POST/PUT)
- Read/List variants (for responses)
- Field validation and type hints
- ORM mode for database-to-API serialization

*New Schemas:*
- RoleSchema
- TemplateSchema, TemplateCreateSchema, TemplateUpdateSchema
- AssetSchema, AssetCreateSchema, AssetUpdateSchema, AssetListSchema
- AlertSchema, AlertCreateSchema, AlertUpdateSchema, AlertListSchema
- ResourceFieldSchema

*Existing Schemas:*
- UserSchema, UserCreateSchema
- ProjectSchema, ProjectCreateSchema
- AuthSchema (login/token)
- And more...

### 4. **Routes (app/routes/)**

**9 API Route Modules** - Each with CRUD endpoints

*New Routes:*
```
POST   /api/templates              - Create template
GET    /api/templates              - List templates
GET    /api/templates/{id}         - Get template
PUT    /api/templates/{id}         - Update template
DELETE /api/templates/{id}         - Delete template

POST   /api/assets                 - Create asset
GET    /api/assets/{id}            - Get asset
GET    /api/assets/project/{pid}   - List project assets
PUT    /api/assets/{id}            - Update asset
DELETE /api/assets/{id}            - Delete asset
GET    /api/assets/{pid}/warranty  - Expiring warranties
GET    /api/assets/{pid}/audit     - Audit due assets
GET    /api/assets/{pid}/summary   - Asset summary

GET    /api/resource-types         - List resource types
GET    /api/resource-types/{id}/fields - Get fields
POST   /api/resource-types/{id}/fields - Create field
```

*Existing Routes:*
- `/api/auth/` - Login, register, refresh token
- `/api/users/` - User management
- `/api/projects/` - Project CRUD
- `/api/resources/` - Resource management
- `/api/asset-types/` - Asset type management
- `/api/dashboard/` - Dashboard metrics

### 5. **Services (app/services/)**

**16 Service Modules** - Business logic layer

*New Services:*
- **TemplateService** - Template CRUD, sheet matching, resource type linking
- **AssetService** - Asset CRUD, field value management, warranty/audit queries
- **ResourceTypeService** - Resource type CRUD, field management, auto-ordering

*Core Services:*
- **AuthService** - Authentication (login, token generation)
- **UserService** - User CRUD and queries
- **ProjectService** - Project CRUD and metrics
- **SessionService** - Session/token management
- **AuditService** - Audit log recording
- **AuthorizationService** - RBAC checks
- **DashboardService** - Dashboard data aggregation
- **ImportService** - Excel file import processing
- **PasswordResetService** - Password reset flow

### 6. **Utils (app/utils/)**

**10 Utility Modules**

- **jwt_utils.py** - JWT token creation, verification, refresh
- **auth_utils.py** - Password hashing (bcrypt), validation
- **dependencies.py** - FastAPI dependency injection (current_user, db session)
- **exceptions.py** - Custom exceptions (InvalidToken, AuthenticationError, etc.)
- **rbac_decorator.py** - @require_role() decorator for endpoint protection
- **auth_middleware.py** - Middleware for token validation
- **auth.py** - Authentication utilities
- **excel_utils.py** - Excel file parsing (openpyxl)
- **validation_service.py** - Field validation rules

## Authentication & Security

### JWT Authentication Flow
```
User Login
    ↓
POST /api/auth/login (username, password)
    ↓
[Validate credentials against hashed password]
    ↓
Generate JWT tokens:
  - access_token (24 hours)
  - refresh_token (7 days)
    ↓
Return tokens
    ↓
Client stores tokens in localStorage
    ↓
Include access_token in Authorization header
    ↓
[Middleware validates token on each request]
    ↓
Grant access or return 401 Unauthorized
```

### Session Management
- **Idle Timeout** (30 min): Session expires if no activity
- **Absolute Timeout** (35 min): Hard limit regardless of activity
- Tracked via `Session` model with:
  - `last_activity` - Updated on each authenticated request
  - `expires_at` - Token expiration time
  - `invalidated_at` - Manual logout

### Role-Based Access Control (RBAC)
```
Roles Hierarchy:
  Super Admin (6)      - Full system access
  Admin (5)            - Admin functions, user management
  Project Manager (4)  - Project management
  Engineer (3)         - Asset management
  Viewer (2)           - Read-only access
  Auditor (1)          - Audit log access
```

Protected endpoints use:
- `@require_role()` decorator
- `current_user.has_permission()` checks
- `current_user.can_manage_projects()` methods

## Database Integration

### Connection & Sessions
```python
# Dependency injection
from app.utils.dependencies import get_current_user, get_db

@router.get("/protected")
def protected_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # current_user is authenticated User object
    # db is SQLAlchemy Session
    return db.query(Asset).filter_by(created_by=current_user.id).all()
```

### Startup & Shutdown
```python
@app.on_event("startup")
async def startup_event():
    # Initialize DB connection
    # Create all tables via SQLAlchemy

@app.on_event("shutdown")
async def shutdown_event():
    # Cleanup on shutdown
```

## API Endpoints Summary

| Category | Count | Endpoints |
|----------|-------|-----------|
| Authentication | 3 | login, register, refresh |
| Users | 5 | CRUD + list |
| Projects | 6 | CRUD + list + metrics |
| Assets (NEW) | 8 | CRUD + list + queries |
| Templates (NEW) | 5 | CRUD + list |
| Resource Types (NEW) | 5 | List + field management |
| Dashboard | 3 | Metrics, summary |
| **Total** | **35+** | **Complete REST API** |

## Dependencies

**Core Framework**
- FastAPI - Web framework
- Uvicorn - ASGI server
- Pydantic - Data validation
- SQLAlchemy - ORM

**Database**
- psycopg2 - PostgreSQL adapter
- alembic - Migrations (optional)

**Security**
- python-jose - JWT tokens
- bcrypt - Password hashing
- passlib - Password utilities

**Utilities**
- openpyxl - Excel parsing
- python-dotenv - Environment variables
- python-multipart - Form data parsing

## Startup Command

```bash
# Development (with reload)
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using main script
python app/main.py
```

The app will:
1. Load .env configuration
2. Connect to PostgreSQL (localhost:5433, automate db)
3. Create/migrate all tables via SQLAlchemy
4. Start FastAPI server on http://localhost:8000
5. Swagger docs available at http://localhost:8000/docs

## Key Features

✓ RESTful API with 35+ endpoints
✓ JWT-based authentication
✓ Role-based access control (6 roles)
✓ Session management with idle/absolute timeouts
✓ Soft delete support (deleted_at column)
✓ Comprehensive audit logging
✓ Dynamic field validation (EAV pattern)
✓ Excel file import/export
✓ Template-driven workbook parsing
✓ Asset warranty & audit tracking
✓ Dashboard metrics and summaries
✓ File attachment management
✓ Alert notification system
✓ CORS support for frontend
✓ Comprehensive error handling

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth_*.py

# Run with coverage
pytest --cov=app tests/
```

Test files cover:
- Authentication flows
- RBAC enforcement
- Database operations
- Asset management
- Import/export functionality
- Session timeout handling

## Performance Considerations

- Database indexes on all foreign keys and frequently queried columns
- Connection pooling for database efficiency
- JWT token validation on each request
- Soft deletes avoid hard database deletes
- Lazy loading of relationships where applicable
- CORS configured for specific origins

## Error Handling

**Custom Exceptions** (app/utils/exceptions.py):
- `AuthenticationError` - Failed login
- `InvalidTokenException` - Invalid JWT
- `TokenExpiredException` - Expired token
- `MissingTokenException` - No token provided
- `InsufficientPermissionsError` - Authorization failed
- `ValidationError` - Data validation
- `NotFoundError` - Resource not found

All exceptions return proper HTTP status codes with descriptive messages.

## Logging

- Structured logging with timestamps
- Log levels: INFO, DEBUG, WARNING, ERROR
- Logs to console (configurable)
- Authentication and errors tracked

## Next Steps

1. **Start the backend server**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Test endpoints at** http://localhost:8000/docs (Swagger UI)

3. **Connect frontend** to http://localhost:8000/api

4. **Monitor logs** for errors/performance issues

5. **Database administration** via PgAdmin at your configured PostgreSQL

---

**Stack**: FastAPI + SQLAlchemy + PostgreSQL
**Status**: Production-ready
**Version**: 0.1.0