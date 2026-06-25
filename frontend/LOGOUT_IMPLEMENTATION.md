# Logout Functionality Implementation - Task 5.4

## Overview
This document describes the implementation of logout functionality for the PRMS frontend, including the navbar component, logout button, and the complete logout flow.

## Components Implemented

### 1. Navbar Component (`src/components/Layout/Navbar.tsx`)
**Purpose**: Display authenticated user information and provide logout functionality.

**Features**:
- Only rendered when user is authenticated (`state.isAuthenticated === true`)
- Displays username and user icon in top-right corner
- Shows dropdown menu with user options:
  - View Profile (placeholder for future implementation)
  - Logout button
- Confirmation dialog before logout: "Are you sure you want to logout?"
- Loading state during logout
- Error message display if logout fails
- Responsive design for mobile/tablet/desktop

**Key Behavior**:
1. User clicks on username/user icon to open dropdown menu
2. User clicks "Logout" button
3. Confirmation dialog appears
4. On confirmation, `logout()` from `useAuth` hook is called
5. Component redirects to `/login` after successful logout
6. Even if API call fails, local state is cleared and user is redirected

### 2. MainLayout Component (`src/components/Layout/MainLayout.tsx`)
**Purpose**: Wrapper component that includes Navbar and content area.

**Usage**:
```tsx
<ProtectedRoute>
  <MainLayout>
    <Dashboard />
  </MainLayout>
</ProtectedRoute>
```

**Features**:
- Sticky navbar at top
- Flexible main content area
- Responsive scrolling and styling

### 3. Updated AuthContext (`src/store/authContext.tsx`)
**Changes**:
- Enhanced `logout()` method to:
  - Always clear local state even if API call fails
  - Remove tokens from localStorage
  - Set `isLoading` to false after completion
  - Clear any error state

**Logout Method**:
```typescript
const logout = useCallback(async () => {
  setIsLoading(true)
  setError(null)
  try {
    // Attempt to call the logout API endpoint
    await authService.logout()
  } catch (err) {
    // Log the error but continue with local cleanup
    console.error('Logout API error:', err)
  } finally {
    // Always clear local state and token
    setTokenState(null)
    setUserState(null)
    setError(null)
    setIsLoading(false)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
  }
}, [])
```

### 4. Updated Auth Service (`src/services/auth.ts`)
**Changes**:
- Enhanced `logout()` to gracefully handle API failures
- Ensures localStorage is always cleared

**Implementation**:
```typescript
logout: async (): Promise<void> => {
  try {
    // Call the logout API endpoint
    await apiClient.post('/auth/logout')
  } catch (error) {
    // Log the error but don't throw
    console.error('Logout API error:', error)
  } finally {
    // Always clear localStorage
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
  }
}
```

## Logout Flow Diagram

```
User clicks Logout
      ↓
Confirmation Dialog: "Are you sure?"
      ↓
    [Cancel]  →  Menu closes
      ↓
    [Confirm]
      ↓
Show loading state
      ↓
Call logout() from useAuth hook
      ↓
Inside logout():
  - Try: Call POST /api/auth/logout
  - Catch: Log error, continue anyway
  - Finally: Always clear localStorage and context state
      ↓
Clear auth_token from localStorage
Clear user from localStorage
      ↓
Set isAuthenticated to false
Set token to null
Set user to null
      ↓
Navbar component redirects to /login
      ↓
User sees login page
```

## Error Handling

### API Error Scenario
- If the `/api/auth/logout` endpoint returns an error:
  - Error is logged to console
  - Local state is still cleared
  - User is still redirected to login
  - Optional: Toast notification shows "Logout completed locally, but there was an issue with the server."

### Success Scenario
- `/api/auth/logout` succeeds
- Local state is cleared
- User is redirected to `/login`

## Acceptance Criteria - Verification

✅ **Logout button visible in navbar when authenticated**
- Navbar.tsx only renders when `state.isAuthenticated === true`
- Logout button is in the user dropdown menu

✅ **Logout button hidden when not authenticated**
- Navbar returns `null` when not authenticated
- API interceptor redirects to /login on 401

✅ **Clicking logout calls logout() from context**
- `handleLogout()` calls `logout()` from useAuth hook
- Confirmed in unit tests

✅ **POST /api/auth/logout called successfully**
- authService.logout() makes POST request
- Request includes Authorization header via interceptor

✅ **Token cleared from localStorage**
- AuthContext's logout clears localStorage.removeItem('auth_token')
- AuthService also clears it in finally block

✅ **Auth context cleared**
- AuthContext sets token, user, and isAuthenticated to null/false
- App re-renders with unauthenticated state

✅ **Redirects to /login**
- Navbar component uses useNavigate() to redirect after logout
- ProtectedRoute component already redirects unauthenticated users to /login

✅ **Works correctly on mobile/responsive layouts**
- CSS has mobile breakpoints (@media queries)
- Username hidden on small screens
- Menu arrow hidden on small screens
- Responsive dropdown positioning

## Integration with App

In `src/App.tsx`, protected routes should wrap content with MainLayout:

```tsx
<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <MainLayout>
        <Dashboard />
      </MainLayout>
    </ProtectedRoute>
  }
/>
```

This ensures:
1. Route is protected (redirects to /login if not authenticated)
2. Navbar with logout is displayed
3. Content area shows the page

## Testing

### Unit Tests
- `Navbar.test.tsx`: Tests navbar rendering, logout button click, menu open/close
- `authContext.test.tsx`: Tests logout clears state, handles errors gracefully

### Manual Testing Checklist
1. ✓ Login successfully
2. ✓ Navbar appears with username
3. ✓ Click on username to open menu
4. ✓ Click logout button
5. ✓ Confirmation dialog appears
6. ✓ Confirm logout
7. ✓ Redirected to login page
8. ✓ localStorage cleared (check DevTools)
9. ✓ Refresh page - still on login (confirming session cleared)

## Security Considerations

1. **Token Invalidation**: Backend endpoint `/api/auth/logout` should:
   - Mark session as invalid in database
   - Refuse any requests with that token going forward
   - Clear session cookie if used

2. **HTTPS Only**: All auth operations use HTTPS in production

3. **XSS Protection**: No sensitive data in DOM, React escaping applied

4. **CSRF Protection**: POST request includes CSRF token via headers

## Files Modified/Created

### New Files
- `src/components/Layout/Navbar.tsx` - Navbar component with logout
- `src/components/Layout/Navbar.css` - Navbar styling
- `src/components/Layout/MainLayout.tsx` - Layout wrapper
- `src/components/Layout/MainLayout.css` - Layout styling
- `src/components/Layout/Navbar.test.tsx` - Unit tests for Navbar
- `src/store/authContext.test.tsx` - Unit tests for auth context

### Modified Files
- `src/store/authContext.tsx` - Enhanced logout method
- `src/services/auth.ts` - Enhanced logout method
- `src/App.tsx` - Added MainLayout import and commented example routes

## Dependencies

- React Router DOM (already installed)
- React Context API (built-in)
- Axios (already installed for API calls)
- No new dependencies required

## Future Enhancements

1. Toast notifications on logout success/error
2. Profile page component
3. Settings page component
4. User preferences for theme, language
5. Remember me functionality
6. Two-factor authentication
7. Session timeout warnings
