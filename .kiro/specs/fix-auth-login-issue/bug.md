# Bug: Authentication Login Failure (500 Internal Server Error)

## Bug Description
Login endpoint `/api/auth/login` returns 500 Internal Server Error when attempting to login with valid credentials `adminuser/PrmsAdmin@2026!`.

## Symptoms
- POST `/api/auth/login` returns `{"detail":"Internal server error during login"}` 
- No detailed error logs visible in console
- Authentication works when tested directly but fails in FastAPI route

## Root Cause Analysis
Based on investigation:

1. **Database Schema Issue**: User model has `role_id` (Integer foreign key to `roles` table), but `seed_db.py` incorrectly tries to set string `role` attribute
2. **Password Hashing**: Database stores SHA256 hashes, AuthUtils tries bcrypt first (fails with "hash could not be identified"), falls back to SHA256
3. **Role Relationship**: Potential issue with loading `user.role` relationship in auth route

## Bug Condition Exploration Tasks

### Task 1: Write bug condition exploration property test
**Property Test**: Authentication should succeed with valid credentials from seed_db.py
- **Validates**: Login endpoint returns 200 OK with JWT token for seeded admin user
- **Failing Condition**: Currently returns 500 Internal Server Error

### Task 2: Investigate seed_db.py role assignment
- Check if `role` field exists in User model (it doesn't - should be `role_id`)
- Verify roles table has corresponding Admin and Manager roles
- Fix seed script to use proper `role_id` foreign key

### Task 3: Fix password hashing inconsistency
- Either: Update AuthUtils to use SHA256 only (since database has SHA256)
- Or: Re-seed database with bcrypt hashes
- Ensure consistent hashing algorithm

### Task 4: Fix auth.py role retrieval
- Ensure `session_record.user` relationship is properly loaded
- Fix role retrieval logic in lines 87-96 of auth.py
- Handle case where role relationship might not be loaded

### Task 5: Add proper error logging
- Ensure errors are logged at ERROR level
- Capture full exception traceback
- Make logs visible in development

## Verification Tasks

### Task 6: Test login with fixed implementation
- Verify `/api/auth/login` returns 200 OK with adminuser credentials
- Verify JWT token is valid and contains correct claims
- Verify role information is correctly included in response

### Task 7: Test login with all seeded users
- Test PRMS/India@123 (Manager)
- Test adminuser/PrmsAdmin@2026! (Admin)
- Test admin/admin123 (Admin - if exists)

### Task 8: Run existing auth tests
- Run `test_auth_end_to_end.py` tests
- Ensure all authentication tests pass
- Fix any broken tests

## Success Criteria
1. Login endpoint returns 200 OK with valid credentials
2. JWT token is generated and can be used for authenticated requests
3. User role information is correctly included in login response
4. All existing authentication tests pass
5. Proper error messages for invalid credentials (401) vs server errors (500)