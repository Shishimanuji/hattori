# Project Resource Management System (PRMS) - Backend

FastAPI backend for the Project Resource Management System with PostgreSQL integration.

## Project Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration and settings
│   │   └── database.py        # Database connection and session management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py            # User model
│   │   ├── project.py         # Project model
│   │   ├── asset_type.py      # Asset type and custom field models
│   │   ├── resource.py        # Resource and allocation models
│   │   ├── audit_log.py       # Audit log model
│   │   └── session.py         # Session model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py            # User Pydantic schemas
│   │   └── project.py         # Project Pydantic schemas
│   ├── routes/
│   │   └── __init__.py        # API route handlers (to be implemented)
│   ├── services/
│   │   └── __init__.py        # Business logic services (to be implemented)
│   ├── utils/
│   │   └── __init__.py        # Helper utilities (to be implemented)
│   ├── __init__.py
│   └── main.py                # FastAPI application entry point
├── tests/
│   └── (test files to be added)
├── .env.example               # Environment variables template
├── pyproject.toml             # Poetry dependencies and configuration
└── README.md                  # This file
```

## Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- Poetry (for dependency management)

## Installation

### 1. Install Dependencies

```bash
# Navigate to backend directory
cd backend

# Install dependencies using Poetry
poetry install

# Or using pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your local configuration
# Update DATABASE_URL with your PostgreSQL connection string
# Update SECRET_KEY with a secure value
```

### 3. Set Up PostgreSQL Database

```sql
-- Create database
CREATE DATABASE prms_db;

-- Create user (optional, if not using superuser)
CREATE USER prms_user WITH PASSWORD 'prms_password';
GRANT ALL PRIVILEGES ON DATABASE prms_db TO prms_user;
```

## Running the Application

### Development Server

```bash
# Using Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Using Python
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Health Check

```bash
curl http://localhost:8000/health
```

## Database Models

### Core Tables

- **users**: User accounts with authentication and roles
- **projects**: Projects for organizing resources
- **resources**: Assets allocated to projects
- **asset_types**: Categories of resources with schema definitions
- **custom_fields**: Dynamic fields for asset types
- **allocations**: Budget tracking and allocation history
- **audit_logs**: Change history for compliance
- **sessions**: User authentication tokens

## Key Features

### Authentication & Authorization
- JWT token-based authentication (24-hour expiration)
- Role-based access control (RBAC) with 4 roles: Admin, Manager, Analyst, Viewer
- Session management with idle timeout

### Database Integration
- PostgreSQL with SQLAlchemy ORM
- Soft deletes for data preservation
- Audit logging for compliance
- Dynamic schema support via JSONB custom fields

### Data Persistence
- All changes recorded with timestamps
- Referential integrity via foreign keys
- Performance indexes on frequently queried columns

## Configuration

### Database Connection

Set `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

### Security

- Update `SECRET_KEY` in `.env` with a secure random value
- Never commit `.env` file to version control
- Use environment variables for sensitive configuration

### CORS

Configure allowed origins in `.env` for frontend communication:
```
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

### Database Migrations

Alembic is included for managing database schema migrations. Migrations will be added as models evolve.

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

## API Endpoints (To Be Implemented)

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Resources
- `GET /api/resources` - List resources
- `POST /api/resources` - Create resource
- `GET /api/resources/{id}` - Get resource details
- `PUT /api/resources/{id}` - Update resource
- `DELETE /api/resources/{id}` - Delete resource

### Users (Admin)
- `GET /api/users` - List users
- `POST /api/users` - Create user
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

### Asset Types (Admin)
- `GET /api/asset-types` - List asset types
- `POST /api/asset-types` - Create asset type
- `PUT /api/asset-types/{id}` - Update asset type

## Troubleshooting

### Database Connection Error

Check that:
- PostgreSQL is running
- `DATABASE_URL` in `.env` is correct
- Network connectivity to database host
- Username and password are correct

### Module Import Errors

Ensure you're running from the correct directory and dependencies are installed:
```bash
poetry install
```

### Port Already in Use

If port 8000 is in use, specify a different port:
```bash
uvicorn app.main:app --port 8001
```

## Dependencies

See `pyproject.toml` for complete list. Key dependencies:

- **fastapi**: Web framework
- **sqlalchemy**: ORM for database operations
- **psycopg2-binary**: PostgreSQL adapter
- **pydantic**: Data validation
- **python-jose**: JWT token handling
- **bcrypt**: Password hashing
- **alembic**: Database migrations

## Requirements Alignment

This backend setup implements:

- **Requirement 11.1 (Data Persistence)**: PostgreSQL integration with SQLAlchemy
- **Requirement 13.1 (RBAC)**: Role-based models and authentication structure
- **Requirement 14.1 (Security)**: Password hashing with bcrypt, JWT tokens
- **Requirement 18.1 (Database Schema)**: Core tables with proper relationships

## Next Steps

1. Implement authentication routes and services
2. Implement project CRUD endpoints
3. Implement resource management endpoints
4. Implement asset type and custom field management
5. Add dashboard metrics aggregation
6. Implement Excel import pipeline
7. Add audit logging integration
8. Implement RBAC enforcement
9. Add comprehensive tests

## License

Proprietary - Project Resource Management System
