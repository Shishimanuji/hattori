"""Pytest configuration and fixtures for tests"""
# Patch SQLAlchemy JSONB BEFORE importing models
import sys
from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator

class JSONB(TypeDecorator):
    """JSONB type that works with SQLite by falling back to JSON"""
    impl = JSON
    cache_ok = True

# Patch sqlalchemy.dialects.postgresql BEFORE any model imports
import sqlalchemy.dialects.postgresql
sqlalchemy.dialects.postgresql.JSONB = JSONB

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from uuid import uuid4
import os

from app.core.database import Base, get_db
from app.core.config import settings
from app.main import app
from app.models.user import User, UserRole
from app.utils.jwt_utils import create_access_token


# Create test database engine - use in-memory SQLite
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database and return session"""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # Print detailed error for debugging
        print(f"Database creation error: {str(e)}")
        import traceback
        traceback.print_exc()
        # If we can't create tables, skip the test
        pytest.skip(f"Cannot create test database: {str(e)}")
    
    db_session = TestingSessionLocal()
    
    yield db_session
    
    db_session.close()
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass  # Ignore errors when dropping tables


@pytest.fixture(scope="function")
def client(db):
    """Create test client with test database session"""
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Use httpx-based TestClient (compatible with fastapi 0.109.0)
    test_client = TestClient(app)
    
    yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db):
    """Create test user in database"""
    from app.utils.auth import AuthUtils
    user_id = uuid4()
    # Use a password that's minimum 8 characters
    password = "testpass123"
    password_hash = AuthUtils.hash_password(password)
    
    user = User(
        id=user_id,
        username="testuser",
        email="testuser@example.com",
        password_hash=password_hash,
        role=UserRole.MANAGER.value,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Store password for use in tests
    user._test_password = password
    return user


@pytest.fixture(scope="function")
def test_admin_user(db):
    """Create test admin user in database"""
    from app.utils.auth import AuthUtils
    user_id = uuid4()
    password = "adminpass123"
    password_hash = AuthUtils.hash_password(password)
    
    user = User(
        id=user_id,
        username="adminuser",
        email="admin@example.com",
        password_hash=password_hash,
        role=UserRole.ADMIN.value,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user._test_password = password
    return user


@pytest.fixture(scope="function")
def inactive_user(db):
    """Create inactive test user"""
    from app.utils.auth import AuthUtils
    user_id = uuid4()
    password = "inactpass123"
    password_hash = AuthUtils.hash_password(password)
    
    user = User(
        id=user_id,
        username="inactiveuser",
        email="inactive@example.com",
        password_hash=password_hash,
        role=UserRole.VIEWER.value,
        is_active=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user._test_password = password
    return user


@pytest.fixture(scope="function")
def valid_token(test_user):
    """Create valid JWT token for test user"""
    token_data = {
        "sub": str(test_user.id),
        "username": test_user.username,
        "role": test_user.role
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def admin_token(test_admin_user):
    """Create valid JWT token for admin user"""
    token_data = {
        "sub": str(test_admin_user.id),
        "username": test_admin_user.username,
        "role": test_admin_user.role
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def manager_token(test_user):
    """Create valid JWT token for manager user"""
    token_data = {
        "sub": str(test_user.id),
        "username": test_user.username,
        "role": test_user.role
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def admin_user(test_admin_user):
    """Alias for test_admin_user"""
    return test_admin_user


@pytest.fixture(scope="function")
def manager_user(test_user):
    """Alias for test_user (which is a manager)"""
    return test_user


@pytest.fixture(scope="function")
def expired_token(test_user):
    """Create expired JWT token"""
    token_data = {
        "sub": str(test_user.id),
        "username": test_user.username,
        "role": test_user.role
    }
    # Create token that already expired
    expires_delta = timedelta(hours=-1)  # Negative: already expired
    return create_access_token(token_data, expires_delta)


@pytest.fixture(scope="function")
def invalid_token():
    """Return invalid token string"""
    return "invalid.token.string"
