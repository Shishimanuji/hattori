#!/usr/bin/env python
"""Debug the exact login flow to find the error"""
import sys
sys.path.insert(0, '.')

import logging
logging.basicConfig(level=logging.DEBUG)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from app.models.user import User
from app.models.session import Session
from app.utils.auth import AuthUtils
from app.core.config import settings
import uuid

# Create database connection
engine = create_engine('postgresql://postgres:postgres@localhost:5433/automate')
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    print("=== Simulating exact login flow ===")
    
    # Step 1: Authenticate user (like AuthService.authenticate_user)
    username = 'adminuser'
    password = 'PrmsAdmin@2026!'
    
    print(f"Step 1: Looking up user '{username}'")
    user = db.query(User).filter(User.username == username).first()
    print(f"User found: {user}")
    
    if user:
        print(f"Step 2: Verifying password")
        password_ok = AuthUtils.verify_password(password, user.password_hash)
        print(f"Password verification: {password_ok}")
        
        if password_ok:
            print(f"Step 3: Creating JWT token")
            try:
                token, token_expires = AuthUtils.create_access_token(
                    data={"sub": str(user.id)},
                    expires_delta=timedelta(hours=settings.access_token_expire_hours)
                )
                print(f"Token created: {token[:50]}...")
                print(f"Token expires: {token_expires}")
            except Exception as e:
                print(f"Error creating token: {e}")
                raise
            
            print(f"Step 4: Creating session")
            try:
                # Hash the token for secure storage
                token_hash = AuthUtils.hash_token(token)
                
                # Calculate expiration time (absolute timeout: 35 minutes from now)
                now = datetime.utcnow()
                expires_at = now + timedelta(minutes=settings.absolute_timeout_minutes)
                
                # Create session
                session_record = Session(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    token_hash=token_hash,
                    created_at=now,
                    expires_at=expires_at,
                    last_activity=now,
                    is_active=True,
                )
                
                db.add(session_record)
                db.commit()
                db.refresh(session_record)
                
                print(f"Session created: {session_record}")
                
                # Step 5: Try to access user from session (like in auth.py line 73)
                print(f"Step 5: Accessing user from session")
                try:
                    session_user = session_record.user
                    print(f"User from session: {session_user}")
                    print(f"User username: {session_user.username}")
                    print(f"User role: {session_user.role}")
                except Exception as e:
                    print(f"Error accessing user from session: {e}")
                    
                    # Try with explicit query
                    print(f"Trying explicit query...")
                    session_user = db.query(User).filter(User.id == session_record.user_id).first()
                    print(f"User from explicit query: {session_user}")
                
            except Exception as e:
                print(f"Error creating session: {e}")
                raise
                
finally:
    db.close()