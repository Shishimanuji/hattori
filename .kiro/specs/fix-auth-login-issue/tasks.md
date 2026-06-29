# Implementation Tasks: Fix Authentication Login Issue

## Overview
Fix the 500 Internal Server Error when logging in with adminuser/PrmsAdmin@2026! credentials.

## Tasks

- [ ] 1. Write bug condition exploration property test
  - Create test that reproduces the login failure
  - Test with adminuser/PrmsAdmin@2026! credentials
  - Expectation: Should return 500 (bug condition)
  - **Property**: Authentication endpoint handles valid seeded credentials
  - **Validates**: Bug exists and can be reproduced

- [ ] 2. Investigate and fix seed_db.py role assignment
  - Check User model schema: has `role_id` not `role`
  - Check roles table for Admin (id=2) and Manager (id=3) roles
  - Fix seed_db.py to use proper `role_id` instead of string `role`
  - Test: Run seed_db.py and verify users have correct role_id

- [ ] 3. Fix password hashing inconsistency
  - Option A: Update AuthUtils to use SHA256 only (simpler)
  - Option B: Re-seed with bcrypt hashes (more secure)
  - Ensure verify_password works with existing SHA256 hashes
  - Test: AuthUtils.verify_password returns True for seeded passwords

- [ ] 4. Fix auth.py role retrieval and error handling
  - Ensure session.user relationship is properly loaded (add `lazy='joined'` or explicit load)
  - Fix role retrieval logic in lines 87-96
  - Add better error logging with traceback
  - Test: Login endpoint doesn't throw 500 errors

- [ ] 5. Add proper error logging to auth route
  - Log full exception traceback on error
  - Ensure ERROR level logs are visible
  - Add debug logging for authentication flow
  - Test: Errors appear in logs with stack traces

- [ ] 6. Test login with fixed implementation
  - Test adminuser/PrmsAdmin@2026! returns 200 OK
  - Verify JWT token structure and claims
  - Verify role field in response matches database role
  - Test: Login successful with token returned

- [ ] 7. Test login with all seeded users
  - Test PRMS/India@123 (Manager role)
  - Test adminuser/PrmsAdmin@2026! (Admin role)
  - Test admin/admin123 if exists
  - Test: All seeded users can login

- [ ] 8. Run and fix existing auth tests
  - Run `python -m pytest backend/tests/test_auth_end_to_end.py -v`
  - Fix any test failures related to authentication
  - Ensure checkpoint 16.2 tests pass
  - Test: All auth tests pass

## Success Verification
- ✅ Login endpoint returns 200 OK for valid credentials
- ✅ JWT tokens are valid and contain correct user info
- ✅ Role information correctly included in response
- ✅ No 500 errors for valid login attempts
- ✅ Proper 401 errors for invalid credentials
- ✅ All existing tests pass