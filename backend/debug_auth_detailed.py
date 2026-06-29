#!/usr/bin/env python
"""Detailed debug script for authentication issues"""
import sys
sys.path.insert(0, '.')

import logging
logging.basicConfig(level=logging.DEBUG)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.utils.auth import AuthUtils

# Create database connection
engine = create_engine('postgresql://postgres:postgres@localhost:5433/automate')
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Test 1: Find user in database
    print("=== Test 1: Find user in database ===")
    username = 'adminuser'
    user = session.query(User).filter(User.username == username).first()
    print(f"User found: {user}")
    if user:
        print(f"User details: id={user.id}, username={user.username}, email={user.email}")
        print(f"Password hash: {user.password_hash}")
        print(f"Role: {user.role}")
        print(f"Role ID: {user.role_id}")
        print(f"Is active: {user.is_active}")
        
        # Test 2: Check password verification
        print("\n=== Test 2: Password verification ===")
        password = 'PrmsAdmin@2026!'
        print(f"Testing password: {password}")
        
        # Direct hash comparison
        import hashlib
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        print(f"SHA256 of password: {sha256_hash}")
        print(f"Hash matches? {user.password_hash == sha256_hash}")
        
        # AuthUtils verification
        print("\nUsing AuthUtils.verify_password:")
        result = AuthUtils.verify_password(password, user.password_hash)
        print(f"Result: {result}")
        
        # Test 3: Check if there's an issue with role relationship
        print("\n=== Test 3: Role relationship ===")
        try:
            role_obj = user.role
            print(f"Role object: {role_obj}")
            if role_obj:
                print(f"Role name: {role_obj.role_name}")
        except Exception as e:
            print(f"Error accessing role: {e}")
            
        # Test 4: Check if role_id exists in roles table
        print("\n=== Test 4: Check roles table ===")
        from app.models.role import Role
        role = session.query(Role).filter(Role.id == user.role_id).first()
        print(f"Role from roles table: {role}")
        if role:
            print(f"Role name: {role.role_name}")
        
finally:
    session.close()