#!/usr/bin/env python
"""Seed database with test users for PostgreSQL"""
import sys
sys.path.insert(0, '/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User, UserRole
from uuid import uuid4
from datetime import datetime
import hashlib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment or use PostgreSQL connection
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/automate')

# Connect to PostgreSQL
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Check if users already exist
    existing = session.query(User).filter_by(username='PRMS').first()
    if existing:
        print('✅ Users already exist in database')
        print(f'   Found user: {existing.username} (Role: {existing.role})')
    else:
        # Simple hash for testing (not for production!)
        def hash_password(password: str) -> str:
            # Use a simple SHA256 hash for testing
            return hashlib.sha256(password.encode()).hexdigest()
        
        # Create test manager user
        user1 = User(
            id=uuid4(),
            username='PRMS',
            email='testuser@example.com',
            password_hash=hash_password('India@123'),
            role=UserRole.MANAGER.value,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Create test admin user
        user2 = User(
            id=uuid4(),
            username='adminuser',
            email='admin@example.com',
            password_hash=hash_password('PrmsAdmin@2026!'),
            role=UserRole.ADMIN.value,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(user1)
        session.add(user2)
        session.commit()
        print('✅ Test users created successfully in PostgreSQL!')
        print('   PRMS / India@123 (Manager)')
        print('   adminuser / PrmsAdmin@2026! (Admin)')

finally:
    session.close()
