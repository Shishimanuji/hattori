"""Authentication service for login, logout, and session management"""
from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timedelta
import logging
import uuid

from app.models.session import Session
from app.models.user import User
from app.utils.auth import AuthUtils
from app.services.session_service import SessionService
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    def authenticate_user(
        db: DBSession,
        username: str,
        password: str
    ) -> User:
        """
        Authenticate a user by username and password.
        
        Args:
            db: SQLAlchemy database session
            username: Username
            password: Plain text password
        
        Returns:
            User object if authentication successful
        
        Raises:
            ValueError: If credentials are invalid
        """
        user = db.query(User).filter(User.username == username).first()
        
        if not user or not AuthUtils.verify_password(password, user.password_hash):
            logger.warning(f"Authentication failed for username: {username}")
            raise ValueError("Invalid username or password")
        
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {username}")
            raise ValueError("User account is inactive")
        
        logger.info(f"User {username} authenticated successfully")
        return user

    @staticmethod
    def create_session(
        db: DBSession,
        user_id: uuid.UUID,
        token: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Session:
        """
        Create a new session for a user after successful login.
        
        Sets up:
        - JWT token hash (for secure storage)
        - Session creation time
        - Absolute timeout: created_at + 35 minutes
        - Idle timeout: last_activity updated on each request (30 min inactivity)
        
        Args:
            db: SQLAlchemy database session
            user_id: UUID of authenticated user
            token: JWT token
            ip_address: Optional IP address of the client
            user_agent: Optional User-Agent header value
        
        Returns:
            New Session object
        """
        # Hash the token for secure storage
        token_hash = AuthUtils.hash_token(token)
        
        # Calculate expiration time (absolute timeout: 35 minutes from now)
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=settings.absolute_timeout_minutes)
        
        # Create session
        session = Session(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            created_at=now,
            expires_at=expires_at,
            last_activity=now,
            is_active=True,
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Session created for user {user_id} with expiration at {expires_at}")
        return session

    @staticmethod
    def logout_user(
        db: DBSession,
        user_id: uuid.UUID,
        token_hash: str
    ) -> bool:
        """
        Log out a user by invalidating their session.
        
        Args:
            db: SQLAlchemy database session
            user_id: UUID of the user
            token_hash: Hash of the JWT token
        
        Returns:
            True if logout successful
        """
        try:
            session = SessionService.get_session_by_user_and_token(
                db=db,
                user_id=user_id,
                token_hash=token_hash
            )
            SessionService.invalidate_session(session, db)
            logger.info(f"User {user_id} logged out successfully")
            return True
        except Exception as e:
            logger.warning(f"Logout failed for user {user_id}: {str(e)}")
            return False

    @staticmethod
    def login_and_create_session(
        db: DBSession,
        username: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> tuple:
        """
        Complete login flow: authenticate user and create session.
        
        Args:
            db: SQLAlchemy database session
            username: Username
            password: Plain text password
            ip_address: Optional client IP address
            user_agent: Optional User-Agent header
        
        Returns:
            Tuple of (jwt_token, session)
        
        Raises:
            ValueError: If authentication fails
        """
        # Authenticate user
        user = AuthService.authenticate_user(db, username, password)
        
        # Create JWT token
        token, token_expires = AuthUtils.create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(hours=settings.access_token_expire_hours)
        )
        
        # Create session in database
        session = AuthService.create_session(
            db=db,
            user_id=user.id,
            token=token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Refresh session to ensure user relationship is loaded
        db.refresh(session)
        
        return token, session
