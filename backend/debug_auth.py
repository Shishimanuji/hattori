#!/usr/bin/env python
"""Debug script for authentication issues"""
import sys
sys.path.insert(0, '.')

from app.utils.auth import AuthUtils
import hashlib

# Test password verification
password = 'PrmsAdmin@2026!'
sha256_hash = 'ffab4c64d5008500cb0634822f7ff244b91fc65d340e990062f95b66ec409c56'

print('Testing password verification...')
print(f'Password: {password}')
print(f'SHA256 hash: {sha256_hash}')
print(f'Hash from hashlib.sha256: {hashlib.sha256(password.encode()).hexdigest()}')

# Test AuthUtils
print('\nAuthUtils.verify_password test:')
result = AuthUtils.verify_password(password, sha256_hash)
print(f'Result: {result}')

# Test AuthUtils.hash_password
print('\nAuthUtils.hash_password test:')
hash_result = AuthUtils.hash_password(password)
print(f'Hash result: {hash_result}')
print(f'Is bcrypt? {"$2b$" in hash_result}')
print(f'Matches SHA256? {hash_result == sha256_hash}')

# Test if bcrypt is available
print('\nChecking bcrypt availability:')
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    print('BCrypt is available')
    
    # Try to verify SHA256 hash with bcrypt
    print('\nTrying to verify SHA256 hash with bcrypt:')
    try:
        bcrypt_result = pwd_context.verify(password, sha256_hash)
        print(f'BCrypt verification result: {bcrypt_result}')
    except Exception as e:
        print(f'BCrypt verification error: {e}')
except Exception as e:
    print(f'BCrypt is not available: {e}')