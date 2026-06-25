"""Password reset service"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import secrets
import string
import logging

from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.utils.auth import AuthUtils
from app.services.audit_service import log_audit
from app.models.audit_log import AuditOperation, AuditLogStatus

logger = logging.getLogger(__name__)


class PasswordResetService:
    """Service for password reset operations"""

    # Password reset token expiration time in hours
    TOKEN_EXPIRATION_HOURS = 1
    
    # Temporary password length and character set
    TEMP_PASSWORD_LENGTH = 12

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Generate a random token for password reset.
        
        Args:
            length: Token length in bytes (hex-encoded, so string length will be 2x)
        
        Returns:
            Hex-encoded random token
        """
        return secrets.token_hex(length)

    @staticmethod
    def generate_temporary_password() -> str:
        """
        Generate a temporary password with mixed character types.
        Includes: uppercase, lowercase, digits, and special characters
        
        Returns:
            Generated temporary password
        """
        # Character sets
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = "!@#$%^&*"
        
        # Ensure at least one character from each set
        password_chars = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(special),
        ]
        
        # Fill remaining characters randomly from all sets
        all_chars = uppercase + lowercase + digits + special
        password_chars.extend(
            secrets.choice(all_chars)
            for _ in range(PasswordResetService.TEMP_PASSWORD_LENGTH - len(password_chars))
        )
        
        # Shuffle to avoid predictable pattern
        import random
        random.shuffle(password_chars)
        
        return "".join(password_chars)

    @staticmethod
    def request_password_reset(
        db: Session,
        username_or_email: str,
        user_id: uuid.UUID = None
    ) -> dict:
        """
        Request password reset for a user.
        
        Finds user by username or email, generates reset token and temporary password,
        creates PasswordResetToken record, and logs audit event.
        
        IMPORTANT: Always returns success message without revealing user existence.
        
        Args:
            db: Database session
            username_or_email: Username or email of user requesting reset
            user_id: Optional user ID (used internally when user is already authenticated)
        
        Returns:
            dict with success message and token (for testing/email - prod would send via email)
        """
        try:
            # Find user
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
            else:
                user = db.query(User).filter(
                    (User.username == username_or_email) | (User.email == username_or_email)
                ).first()
            
            # Always return success even if user not found (security: don't reveal existence)
            if not user:
                logger.warning(f"Password reset requested for non-existent user: {username_or_email}")
                return {
                    "success": True,
                    "message": "If a matching account exists, a password reset link has been sent to the registered email"
                }
            
            if not user.is_active:
                logger.warning(f"Password reset requested for inactive user: {user.username}")
                return {
                    "success": True,
                    "message": "If a matching account exists, a password reset link has been sent to the registered email"
                }
            
            # Generate token and temporary password
            token = PasswordResetService.generate_token()
            temp_password = PasswordResetService.generate_temporary_password()
            temp_password_hash = AuthUtils.hash_password(temp_password)
            
            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(hours=PasswordResetService.TOKEN_EXPIRATION_HOURS)
            
            # Create password reset token record
            reset_token = PasswordResetToken(
                id=uuid.uuid4(),
                user_id=user.id,
                token=token,
                temporary_password_hash=temp_password_hash,
                expires_at=expires_at,
                is_valid=True,
            )
            
            db.add(reset_token)
            db.commit()
            db.refresh(reset_token)
            
            # Log audit event
            log_audit(
                db=db,
                user_id=None,  # System-initiated action
                entity_type="PasswordReset",
                entity_id=user.id,
                operation=AuditOperation.CREATE,
                new_values={
                    "user_id": str(user.id),
                    "username": user.username,
                    "token_id": str(reset_token.id),
                    "expires_at": expires_at.isoformat(),
                },
                status=AuditLogStatus.SUCCESS,
            )
            
            logger.info(f"Password reset token generated for user {user.username}")
            
            # Return token and temp password (in production, these would be sent via email)
            return {
                "success": True,
                "message": "If a matching account exists, a password reset link has been sent to the registered email",
                "token": token,  # Remove in production (would be sent via email)
                "temporary_password": temp_password,  # Remove in production (would be sent via email)
            }
            
        except Exception as e:
            logger.error(f"Error requesting password reset: {str(e)}")
            # Still return success message for security
            return {
                "success": True,
                "message": "If a matching account exists, a password reset link has been sent to the registered email"
            }

    @staticmethod
    def validate_reset_token(db: Session, token: str) -> PasswordResetToken:
        """
        Validate a password reset token.
        
        Checks:
        - Token exists
        - Token is valid (is_valid=True)
        - Token hasn't expired
        - Token hasn't been used
        
        Args:
            db: Database session
            token: Reset token string
        
        Returns:
            PasswordResetToken object
        
        Raises:
            ValueError: If token is invalid, expired, or already used
        """
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).first()
        
        if not reset_token:
            logger.warning(f"Password reset validation failed: token not found")
            raise ValueError("Invalid or expired reset token")
        
        if not reset_token.is_valid:
            logger.warning(f"Password reset validation failed: token marked invalid")
            raise ValueError("Invalid or expired reset token")
        
        if reset_token.is_expired:
            logger.warning(f"Password reset validation failed: token expired for user {reset_token.user_id}")
            raise ValueError("Reset token has expired. Please request a new password reset.")
        
        if reset_token.is_used:
            logger.warning(f"Password reset validation failed: token already used for user {reset_token.user_id}")
            raise ValueError("This reset token has already been used. Please request a new password reset.")
        
        return reset_token

    @staticmethod
    def use_reset_token(db: Session, reset_token: PasswordResetToken, user_id: uuid.UUID) -> PasswordResetToken:
        """
        Mark a reset token as used.
        
        Args:
            db: Database session
            reset_token: PasswordResetToken object
            user_id: User ID (for audit logging)
        
        Returns:
            Updated PasswordResetToken object
        
        Raises:
            ValueError: If token validation fails
        """
        # Ensure token belongs to the user
        if reset_token.user_id != user_id:
            logger.warning(f"Token use mismatch: token for {reset_token.user_id}, user {user_id}")
            raise ValueError("Token validation failed")
        
        # Mark token as used
        reset_token.used_at = datetime.utcnow()
        db.commit()
        db.refresh(reset_token)
        
        # Log audit event
        log_audit(
            db=db,
            user_id=user_id,
            entity_type="PasswordReset",
            entity_id=reset_token.id,
            operation=AuditOperation.UPDATE,
            old_values={"used_at": None},
            new_values={"used_at": reset_token.used_at.isoformat()},
            status=AuditLogStatus.SUCCESS,
        )
        
        logger.info(f"Password reset token marked as used for user {user_id}")
        return reset_token

    @staticmethod
    def complete_password_reset(
        db: Session,
        token: str,
        new_password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        """
        Complete password reset with new permanent password.
        
        Validates token, updates user password, and marks token as used.
        
        Args:
            db: Database session
            token: Reset token
            new_password: New permanent password
            ip_address: Optional client IP
            user_agent: Optional user agent
        
        Returns:
            Success message
        
        Raises:
            ValueError: If validation fails
        """
        # Validate token
        reset_token = PasswordResetService.validate_reset_token(db, token)
        user = reset_token.user
        
        # Update password
        user.password_hash = AuthUtils.hash_password(new_password)
        user.force_password_change = False
        db.commit()
        db.refresh(user)
        
        # Mark token as used
        PasswordResetService.use_reset_token(db, reset_token, user.id)
        
        # Log audit event
        log_audit(
            db=db,
            user_id=user.id,
            entity_type="User",
            entity_id=user.id,
            operation=AuditOperation.UPDATE,
            new_values={"password_changed": True},
            ip_address=ip_address,
            user_agent=user_agent,
            status=AuditLogStatus.SUCCESS,
        )
        
        logger.info(f"Password reset completed for user {user.username}")
        
        return {
            "success": True,
            "message": "Password has been reset successfully. You can now log in with your new password."
        }

    @staticmethod
    def authenticate_with_temporary_password(
        db: Session,
        token: str,
        temporary_password: str
    ) -> dict:
        """
        Authenticate user with temporary password and reset token.
        
        Validates token and temporary password, returns user and token if valid.
        
        Args:
            db: Database session
            token: Reset token
            temporary_password: Temporary password from reset
        
        Returns:
            dict with user and authentication info
        
        Raises:
            ValueError: If validation fails
        """
        # Validate token
        reset_token = PasswordResetService.validate_reset_token(db, token)
        user = reset_token.user
        
        # Verify temporary password
        if not AuthUtils.verify_password(temporary_password, reset_token.temporary_password_hash):
            logger.warning(f"Temporary password verification failed for user {user.id}")
            raise ValueError("Invalid temporary password")
        
        # Set flag to force password change on next login
        user.force_password_change = True
        db.commit()
        db.refresh(user)
        
        logger.info(f"User {user.username} authenticated with temporary password")
        
        return {
            "success": True,
            "user_id": str(user.id),
            "username": user.username,
            "must_change_password": True,
        }

    @staticmethod
    def change_password(
        db: Session,
        user_id: uuid.UUID,
        old_password: str,
        new_password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        """
        Change password when user is authenticated.
        
        Validates old password, updates to new password, clears force_password_change flag.
        
        Args:
            db: Database session
            user_id: Authenticated user ID
            old_password: Current password
            new_password: New password
            ip_address: Optional client IP
            user_agent: Optional user agent
        
        Returns:
            Success message
        
        Raises:
            ValueError: If old password doesn't match
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Verify old password
        if not AuthUtils.verify_password(old_password, user.password_hash):
            logger.warning(f"Password change failed: invalid old password for user {user.id}")
            raise ValueError("Current password is incorrect")
        
        # Update to new password
        user.password_hash = AuthUtils.hash_password(new_password)
        user.force_password_change = False
        db.commit()
        db.refresh(user)
        
        # Log audit event
        log_audit(
            db=db,
            user_id=user.id,
            entity_type="User",
            entity_id=user.id,
            operation=AuditOperation.UPDATE,
            new_values={"password_changed": True},
            ip_address=ip_address,
            user_agent=user_agent,
            status=AuditLogStatus.SUCCESS,
        )
        
        logger.info(f"Password changed for user {user.username}")
        
        return {
            "success": True,
            "message": "Password has been changed successfully."
        }
