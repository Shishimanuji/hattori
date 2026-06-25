"""Session management service for authentication and timeout tracking"""
from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timedelta
import logging

from app.models.session import Session
from app.core.config import settings

logger = logging.getLogger(__name__)


class SessionNotFoundError(Exception):
    """Raised when a session cannot be found"""
    pass


class SessionExpiredError(Exception):
    """Raised when a session has expired"""
    pass


class SessionTimeoutType:
    """Constants for timeout types"""
    IDLE = "idle"
    ABSOLUTE = "absolute"


class SessionService:
    """Service for managing session lifecycle and timeout validation"""

    @staticmethod
    def validate_session_timeout(
        session: Session,
        idle_timeout_minutes: int = None,
        absolute_timeout_minutes: int = None
    ) -> bool:
        """
        Validate whether a session is still valid based on timeout thresholds.
        
        Checks both idle timeout (30 min default) and absolute timeout (35 min default).
        
        Args:
            session: The Session object to validate
            idle_timeout_minutes: Minutes of inactivity before idle timeout (uses config default if None)
            absolute_timeout_minutes: Minutes total before absolute timeout (uses config default if None)
        
        Returns:
            True if session is valid
        
        Raises:
            SessionExpiredError: If session has expired with timeout type in message
        """
        if idle_timeout_minutes is None:
            idle_timeout_minutes = settings.idle_timeout_minutes
        if absolute_timeout_minutes is None:
            absolute_timeout_minutes = settings.absolute_timeout_minutes

        if not session.is_active:
            logger.warning(f"Session {session.id} is not active (invalidated)")
            raise SessionExpiredError("Session expired")

        if session.invalidated_at is not None:
            logger.warning(f"Session {session.id} was invalidated at {session.invalidated_at}")
            raise SessionExpiredError("Session expired")

        # Check absolute timeout first
        if session.is_absolute_expired(absolute_timeout_minutes):
            logger.info(f"Session {session.id} exceeded absolute timeout ({absolute_timeout_minutes} minutes)")
            raise SessionExpiredError("Session expired")

        # Check idle timeout
        if session.is_idle_expired(idle_timeout_minutes):
            logger.info(f"Session {session.id} exceeded idle timeout ({idle_timeout_minutes} minutes)")
            raise SessionExpiredError("Session expired due to inactivity")

        return True

    @staticmethod
    def reset_idle_timer(
        session: Session,
        db: DBSession
    ) -> None:
        """
        Reset the idle timer for a session by updating last_activity to now.
        This should be called on each authenticated request to prevent idle timeout.
        
        Args:
            session: The Session object to update
            db: SQLAlchemy database session
        """
        session.reset_idle_timer()
        db.commit()
        logger.debug(f"Reset idle timer for session {session.id}")

    @staticmethod
    def invalidate_session(
        session: Session,
        db: DBSession
    ) -> None:
        """
        Immediately invalidate a session (e.g., on logout).
        
        Args:
            session: The Session object to invalidate
            db: SQLAlchemy database session
        """
        session.invalidate()
        db.commit()
        logger.info(f"Session {session.id} invalidated")

    @staticmethod
    def get_session_by_token_hash(
        db: DBSession,
        token_hash: str
    ) -> Session:
        """
        Retrieve a session by token hash.
        
        Args:
            db: SQLAlchemy database session
            token_hash: SHA256 hash of the JWT token
        
        Returns:
            Session object
        
        Raises:
            SessionNotFoundError: If session not found
        """
        session = db.query(Session).filter(
            Session.token_hash == token_hash,
            Session.is_active == True
        ).first()

        if not session:
            logger.warning(f"Session with token hash not found or inactive")
            raise SessionNotFoundError("Session not found or has been invalidated")

        return session

    @staticmethod
    def get_session_by_user_and_token(
        db: DBSession,
        user_id,
        token_hash: str
    ) -> Session:
        """
        Retrieve a session by user ID and token hash.
        
        Args:
            db: SQLAlchemy database session
            user_id: UUID of the user
            token_hash: SHA256 hash of the JWT token
        
        Returns:
            Session object
        
        Raises:
            SessionNotFoundError: If session not found
        """
        session = db.query(Session).filter(
            Session.user_id == user_id,
            Session.token_hash == token_hash,
            Session.is_active == True
        ).first()

        if not session:
            logger.warning(f"Session for user {user_id} with given token not found or inactive")
            raise SessionNotFoundError("Session not found or has been invalidated")

        return session

    @staticmethod
    def cleanup_expired_sessions(db: DBSession) -> int:
        """
        Clean up expired sessions (mark inactive those past absolute timeout).
        This can be called periodically or on demand.
        
        Args:
            db: SQLAlchemy database session
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        expired_threshold = now - timedelta(minutes=settings.absolute_timeout_minutes)

        # Update sessions that have expired
        result = db.query(Session).filter(
            Session.is_active == True,
            Session.created_at < expired_threshold
        ).update(
            {
                Session.is_active: False,
                Session.invalidated_at: now
            },
            synchronize_session=False
        )

        db.commit()
        logger.info(f"Cleaned up {result} expired sessions")
        return result

    @staticmethod
    def get_user_active_sessions(
        db: DBSession,
        user_id
    ) -> list:
        """
        Get all active sessions for a user (e.g., across multiple devices).
        
        Args:
            db: SQLAlchemy database session
            user_id: UUID of the user
        
        Returns:
            List of active Session objects
        """
        sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.is_active == True
        ).all()

        return sessions
