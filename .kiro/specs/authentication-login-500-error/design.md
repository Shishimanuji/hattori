# Authentication Login 500 Error Bugfix Design

## Overview

The authentication system is failing with 500 Internal Server Error when admin users attempt to log in using specific credentials. The bug appears to involve a hash algorithm mismatch between the seed data (which uses SHA256) and the authentication logic (which attempts bcrypt first), as well as potential database connectivity issues between PostgreSQL configuration and SQLite files. This design formalizes the bug condition and outlines the validation approach to ensure a targeted, minimal fix that doesn't introduce regressions.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when admin credentials cause authentication to fail with 500 error
- **Property (P)**: The desired behavior - successful authentication with proper JWT token generation
- **Preservation**: Existing behavior for valid non-admin users and invalid credentials must remain unchanged
- **login_and_create_session**: The function in `auth_service.py` that handles authentication and session creation
- **verify_password**: The function in `auth.py` that verifies password hashes
- **seed_db**: The script that creates users with SHA256 hashing
- **AuthUtils**: The utility class that attempts bcrypt first, then SHA256 fallback

## Bug Details

### Bug Condition

The bug manifests when a user attempts to log in with admin credentials that were seeded using SHA256 hashing, but the authentication system encounters issues during password verification or database connectivity. The `AuthService.login_and_create_session` function either fails due to bcrypt verification exceptions, database connection errors, or hash mismatch issues.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type LoginRequest
  OUTPUT: boolean
  
  RETURN input.username IN ['admin', 'adminuser']
         AND input.password IN ['admin123', 'PrmsAdmin@2026!']
         AND (hash_verification_fails(input.password, stored_hash)
              OR database_connection_error()
              OR authentication_flow_exception())
END FUNCTION
```

### Examples

1. **Concrete Example 1**:
   - Input: username="admin", password="admin123"
   - Expected: Successful login with 200 OK and JWT token
   - Actual: 500 Internal Server Error "Internal server error during login"
   - Root Cause: SHA256 hash in database vs bcrypt verification attempt

2. **Concrete Example 2**:
   - Input: username="adminuser", password="PrmsAdmin@2026!"
   - Expected: Successful login with 200 OK and JWT token
   - Actual: 500 Internal Server Error "Internal server error during login"
   - Root Cause: Database connectivity issue or hash verification failure

3. **Edge Case Example**:
   - Input: username="nonexistent", password="anypassword"
   - Expected: 401 Unauthorized (preserved behavior)
   - Actual: 401 Unauthorized (correct)

4. **Edge Case Example**:
   - Input: username="valid_non_admin", password="valid_password"
   - Expected: 200 OK (preserved behavior)
   - Actual: 200 OK (correct)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Invalid credentials must continue to return 401 Unauthorized error
- Valid non-admin users must continue to authenticate successfully
- Database connectivity for properly configured setups must remain functional
- Password verification for existing user accounts must continue to work with their current hash algorithm

**Scope:**
All inputs that do NOT involve the admin credentials with potential hash/database issues should be completely unaffected by this fix. This includes:
- Invalid username/password combinations
- Valid credentials for non-admin users
- Properly configured database connections
- Existing password hash verification methods

## Hypothesized Root Cause

Based on the bug description and code analysis, the most likely issues are:

1. **Hash Algorithm Mismatch**: The seed_db.py script uses SHA256 hashing for passwords, but AuthUtils.verify_password() attempts bcrypt verification first. When bcrypt fails, it falls back to SHA256, but this fallback logic may not handle all edge cases properly.

2. **Database Connectivity Issues**: The system may have mixed database configurations:
   - .env file configures PostgreSQL (postgresql://postgres:postgres@localhost:5433/automate)
   - There may be SQLite files (prms.db, test.db) causing conflicts
   - Database migration/connection issues when switching between databases

3. **Seed Data vs Runtime Hashing Inconsistency**:
   - seed_db.py: Uses simple SHA256: `hashlib.sha256(password.encode()).hexdigest()`
   - AuthUtils.hash_password(): Tries bcrypt first, falls back to SHA256
   - This inconsistency could cause verification failures

4. **Exception Handling in Authentication Flow**:
   - The login endpoint catches generic exceptions and returns 500
   - Specific exceptions (hash verification errors, database errors) may not be properly handled
   - Error messages may not provide enough diagnostic information

## Correctness Properties

Property 1: Bug Condition - Admin Authentication Success

_For any_ login input where the bug condition holds (admin credentials with username in ['admin', 'adminuser'] and password in ['admin123', 'PrmsAdmin@2026!']), the fixed authentication system SHALL successfully authenticate the user and return a valid JWT token with 200 OK status.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Non-Admin Authentication Behavior

_For any_ login input where the bug condition does NOT hold (non-admin users, invalid credentials, properly configured database connections), the fixed system SHALL produce exactly the same behavior as the original system, preserving all existing authentication functionality for non-admin scenarios.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `app/utils/auth.py`

**Function**: `verify_password()`

**Specific Changes**:
1. **Improve Hash Verification Fallback**: Ensure the bcrypt-to-SHA256 fallback works correctly for all seed data passwords
2. **Add Diagnostic Logging**: Log which hash verification method is being used for debugging
3. **Handle Edge Cases**: Ensure all exceptions in password verification are properly caught and logged

**File**: `app/routes/auth.py`

**Function**: `login()` endpoint

**Specific Changes**:
1. **Better Exception Handling**: Catch specific exceptions and provide more detailed error messages
2. **Database Connection Validation**: Add checks for database connectivity before authentication attempts
3. **Diagnostic Information**: Log specific error details for debugging

**File**: Configuration files

**Specific Changes**:
1. **Database Consistency**: Ensure consistent database configuration (PostgreSQL only)
2. **Seed Data Updates**: Update seed_db.py to use consistent hashing method if needed
3. **Environment Validation**: Add startup checks for database connectivity

**Potential Implementation Details**:
1. Update AuthUtils.verify_password() to handle SHA256 hashes more robustly
2. Add database health check before authentication attempts
3. Ensure seed_db.py and runtime authentication use compatible hash methods
4. Add comprehensive logging for authentication failures

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that attempt to log in with admin credentials and assert successful authentication. Run these tests on the UNFIXED code to observe failures and understand the root cause.

**Test Cases**:
1. **Admin Login Test**: Attempt login with "admin/admin123" (will fail on unfixed code)
2. **AdminUser Login Test**: Attempt login with "adminuser/PrmsAdmin@2026!" (will fail on unfixed code)
3. **Hash Verification Test**: Directly test AuthUtils.verify_password() with seeded passwords (will fail on unfixed code)
4. **Database Connection Test**: Test database connectivity before authentication (may fail on unfixed code)

**Expected Counterexamples**:
- 500 Internal Server Error instead of successful authentication
- Hash verification failures (bcrypt vs SHA256 mismatch)
- Database connection errors
- Exception stack traces in logs

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := login_fixed(input)
  ASSERT result.status = 200 AND result.has_valid_jwt_token
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT login_original(input) = login_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for non-admin users and invalid credentials, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Invalid Credential Preservation**: Verify invalid credentials continue to return 401
2. **Non-Admin User Preservation**: Verify existing non-admin users can still authenticate
3. **Database Connectivity Preservation**: Verify database operations continue to work
4. **Error Message Preservation**: Verify error messages remain consistent

### Unit Tests

- Test AuthUtils.verify_password() with SHA256 hashes
- Test login endpoint with admin credentials
- Test database connectivity checks
- Test exception handling in authentication flow

### Property-Based Tests

- Generate random user credentials and verify authentication behavior is preserved
- Test password verification across different hash algorithms
- Generate random database states and verify authentication consistency
- Test error handling across various failure scenarios

### Integration Tests

- Test complete authentication flow with admin credentials
- Test database connectivity and migration scenarios
- Test seed data compatibility with authentication system
- Test error recovery and logging