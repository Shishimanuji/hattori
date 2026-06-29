#!/usr/bin/env python
"""Test to find the actual error in auth flow"""
import sys
sys.path.insert(0, '.')

import logging
logging.basicConfig(level=logging.DEBUG)

# Try to import and run the exact auth service
try:
    print("=== Testing imports ===")
    from app.services.auth_service import AuthService
    print("✓ AuthService imported")
    
    from app.core.config import settings
    print(f"✓ Settings imported: database_url={settings.database_url[:30]}...")
    
    # Test the actual method
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    print("\n=== Testing AuthService.authenticate_user ===")
    try:
        user = AuthService.authenticate_user(db, 'adminuser', 'PrmsAdmin@2026!')
        print(f"✓ authenticate_user succeeded: {user.username}")
    except Exception as e:
        print(f"✗ authenticate_user failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Testing AuthService.login_and_create_session ===")
    try:
        token, session = AuthService.login_and_create_session(db, 'adminuser', 'PrmsAdmin@2026!')
        print(f"✓ login_and_create_session succeeded")
        print(f"  Token: {token[:50]}...")
        print(f"  Session: {session}")
    except Exception as e:
        print(f"✗ login_and_create_session failed: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()
    
except Exception as e:
    print(f"Import or setup error: {e}")
    import traceback
    traceback.print_exc()