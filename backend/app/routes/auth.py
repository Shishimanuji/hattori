"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from app.core.database import get_db
from app.schemas.auth import LoginResponse, LogoutResponse, TokenData, LoginRequest, CurrentUserResponse
from app.models.user import User
from app.models.session import Session as SessionModel
from app.services.auth_service import AuthService
from app.services.session_service import SessionService
from app.utils.auth import AuthUtils
from app.services.password_reset_service import PasswordResetService
from app.services.audit_service import log_logout, log_login
from app.utils.dependencies import get_current_user
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Request/Response schemas for password reset
class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    username_or_email: str = Field(
        ...,
        description="Username or email address of account",
        example="john.doe"
    )


class PasswordResetResponse(BaseModel):
    """Password reset response schema"""
    success: bool
    message: str


class PasswordResetCompleteRequest(BaseModel):
    """Password reset completion request schema"""
    token: str = Field(..., description="Reset token from email")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="New password (minimum 8 characters)"
    )


class PasswordChangeRequest(BaseModel):
    """Password change request schema for authenticated users"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="New password (minimum 8 characters)"
    )


class PasswordChangeResponse(BaseModel):
    """Password change response schema"""
    success: bool
    message: str


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Login endpoint - authenticate user and create session.
    
    **Requirements:**
    - Validate credentials against stored password hashes (Requirement 3.1)
    - Create JWT token with 24-hour expiration (Requirement 3.2, 20.1)
    - Create session record with timeout tracking (Requirement 20.1, 20.4)
    - Log successful login with audit trail (Requirement 19.2)
    
    **Request Body:**
    - username: User's username
    - password: User's password (minimum 8 characters)
    
    **Returns:**
    - 200 OK: LoginResponse with access token and user info
    - 401 Unauthorized: If credentials are invalid or user is inactive
    - 422 Unprocessable Entity: If validation fails
    
    **Response:**
    ```json
    {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "token_type": "bearer",
      "expires_in": 86400,
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "john.doe",
      "role": "Manager"
    }
    ```
    
    **Example:**
    ```
    POST /api/auth/login
    Content-Type: application/json
    
    {
      "username": "john.doe",
      "password": "SecurePassword123!"
    }
    ```
    """
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Authenticate user and create session with JWT token
        token, session_record = AuthService.login_and_create_session(
            db=db,
            username=login_data.username,
            password=login_data.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        user = session_record.user
        
        # Log successful login
        log_login(
            db=db,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # Update user's last_login timestamp
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.info(f"User {user.username} (ID: {user.id}) logged in successfully")
        
        # Calculate token expiration in seconds
        from app.core.config import settings
        expires_in = settings.access_token_expire_hours * 3600
        
        # Get user role safely - handle both string and object
        user_role = "Viewer"  # Default role
        try:
            if hasattr(user, 'role') and user.role:
                user_role = user.role.role_name if hasattr(user.role, 'role_name') else str(user.role)
        except Exception as e:
            logger.warning(f"Could not retrieve user role: {str(e)}")
        
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
            user=CurrentUserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user_role,
                is_active=user.is_active,
                created_at=user.created_at,
            ),
        )
        
    except ValueError as e:
        logger.warning(f"Login failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during login")


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Logout endpoint - invalidates user's session and clears tokens.
    
    Requires authentication (valid Bearer token).
    
    Returns:
        200 OK: { "message": "Successfully logged out" }
        401 Unauthorized: If no token or invalid token
        404 Not Found: If session not found (already logged out)
    """
    try:
        # Extract IP address from request
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Get the token from Authorization header
        auth_header = request.headers.get("authorization")
        token = AuthUtils.extract_token_from_header(auth_header)
        
        if not token:
            logger.warning(f"Logout attempt without token by user {current_user.id}")
            raise HTTPException(status_code=401, detail="No authentication token provided")
        
        # Verify token is valid
        token_data = AuthUtils.verify_token(token)
        if not token_data:
            logger.warning(f"Logout attempt with invalid token by user {current_user.id}")
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # Hash the token to match what's stored in sessions table
        token_hash = AuthUtils.hash_token(token)
        
        # Find and invalidate the session
        session_record = db.query(SessionModel).filter(
            SessionModel.token_hash == token_hash,
            SessionModel.user_id == current_user.id
        ).first()
        
        if session_record:
            # Invalidate the session
            session_record.invalidate()
            db.commit()
            
            # Log the logout operation
            log_logout(
                db=db,
                user_id=current_user.id,
                session_id=session_record.id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            logger.info(f"User {current_user.username} (ID: {current_user.id}) logged out successfully")
        else:
            # Session not found - idempotent behavior (return 200 anyway)
            logger.info(
                f"Logout for user {current_user.username} - session already invalidated or not found"
            )
            # Still log the logout attempt
            log_logout(
                db=db,
                user_id=current_user.id,
                session_id=UUID(int=0),  # Placeholder for non-existent session
                ip_address=ip_address,
                user_agent=user_agent,
            )
        
        return LogoutResponse(message="Successfully logged out")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during logout for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during logout")


@router.post("/password-reset/request", response_model=PasswordResetResponse)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Request a password reset for an account.
    
    **Requirements:**
    - Generate a temporary password (Requirement 4.7)
    - Create a one-time reset token (Requirement 4.7)
    - Always returns success message without revealing if user exists (security)
    - In production, temporary password and token would be sent via email
    
    **Request Body:**
    - username_or_email: Username or email address to reset password for
    
    **Returns:**
    - 200 OK: Always returns success message for security
    
    **Response (in development/testing):**
    - includes 'token' and 'temporary_password' fields (would not be in production)
    
    **Example:**
    ```
    POST /api/auth/password-reset/request
    Content-Type: application/json
    
    {
      "username_or_email": "john@example.com"
    }
    ```
    
    **Note:** For security, this endpoint always returns success even if the user
    doesn't exist, preventing user enumeration attacks.
    """
    try:
        result = PasswordResetService.request_password_reset(
            db=db,
            username_or_email=reset_request.username_or_email
        )
        
        logger.info(
            f"Password reset requested for: {reset_request.username_or_email}"
        )
        
        return PasswordResetResponse(
            success=result.get("success", True),
            message=result.get("message", "Password reset requested")
        )
        
    except Exception as e:
        logger.error(f"Error requesting password reset: {str(e)}")
        # Still return success for security
        return PasswordResetResponse(
            success=True,
            message="If a matching account exists, a password reset link has been sent to the registered email"
        )


@router.post("/password-reset/complete", response_model=PasswordResetResponse)
async def complete_password_reset(
    reset_data: PasswordResetCompleteRequest,
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Complete password reset with new permanent password.
    
    **Requirements:**
    - Require user to set new password on first login after reset (Requirement 4.7)
    - Validate reset token and ensure it hasn't expired
    - Update user's password and clear force_password_change flag
    - One-time use token (cannot be reused)
    
    **Request Body:**
    - token: Password reset token from email
    - new_password: New permanent password (minimum 8 characters)
    
    **Returns:**
    - 200 OK: PasswordResetResponse with success message
    - 400 Bad Request: If validation fails
    - 422 Unprocessable Entity: If password doesn't meet requirements
    
    **Example:**
    ```
    POST /api/auth/password-reset/complete
    Content-Type: application/json
    
    {
      "token": "abc123def456...",
      "new_password": "NewSecurePass123!"
    }
    ```
    """
    try:
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        result = PasswordResetService.complete_password_reset(
            db=db,
            token=reset_data.token,
            new_password=reset_data.new_password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        logger.info("Password reset completed successfully")
        
        return PasswordResetResponse(
            success=result.get("success", True),
            message=result.get("message", "Password reset complete")
        )
        
    except ValueError as e:
        logger.warning(f"Password reset validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing password reset: {str(e)}")
        raise HTTPException(status_code=500, detail="Error completing password reset")


@router.post("/password/change", response_model=PasswordChangeResponse)
async def change_password(
    change_request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Change password for authenticated user.
    
    **Requirements:**
    - User must be authenticated (valid Bearer token)
    - Current password must be verified
    - New password must meet minimum requirements (8+ characters)
    - Password change is audited
    
    **Request Body:**
    - old_password: Current password for verification
    - new_password: New password (minimum 8 characters)
    
    **Returns:**
    - 200 OK: PasswordChangeResponse with success message
    - 400 Bad Request: If old password is incorrect
    - 401 Unauthorized: If not authenticated
    - 422 Unprocessable Entity: If new password doesn't meet requirements
    
    **Example:**
    ```
    POST /api/auth/password/change
    Content-Type: application/json
    Authorization: Bearer <token>
    
    {
      "old_password": "CurrentPassword123!",
      "new_password": "NewPassword456!"
    }
    ```
    """
    try:
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        result = PasswordResetService.change_password(
            db=db,
            user_id=current_user.id,
            old_password=change_request.old_password,
            new_password=change_request.new_password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        logger.info(f"Password changed for user {current_user.username}")
        
        return PasswordChangeResponse(
            success=result.get("success", True),
            message=result.get("message", "Password changed successfully")
        )
        
    except ValueError as e:
        logger.warning(f"Password change failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(status_code=500, detail="Error changing password")
