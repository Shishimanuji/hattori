"""Session database model"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid

from app.core.database import Base


class Session(Base):
    """Session model for managing user authentication tokens with timeout tracking"""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)
    invalidated_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_expires_at", "expires_at"),
        Index("idx_sessions_token_hash", "token_hash"),
        Index("idx_sessions_last_activity", "last_activity"),
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

    @property
    def is_expired(self) -> bool:
        """Check if session token has expired"""
        return datetime.utcnow() > self.expires_at

    def is_idle_expired(self, idle_timeout_minutes: int = 30) -> bool:
        """
        Check if session has been idle for too long (idle timeout).
        
        Args:
            idle_timeout_minutes: Number of minutes of inactivity before session expires (default: 30)
        
        Returns:
            True if session has been inactive longer than idle_timeout_minutes
        """
        idle_threshold = self.last_activity + timedelta(minutes=idle_timeout_minutes)
        return datetime.utcnow() > idle_threshold

    def is_absolute_expired(self, absolute_timeout_minutes: int = 35) -> bool:
        """
        Check if session has exceeded absolute lifetime (absolute timeout).
        Hard limit on session lifetime regardless of activity.
        
        Args:
            absolute_timeout_minutes: Number of minutes before session expires regardless of activity (default: 35)
        
        Returns:
            True if session lifetime has exceeded absolute_timeout_minutes
        """
        absolute_threshold = self.created_at + timedelta(minutes=absolute_timeout_minutes)
        return datetime.utcnow() > absolute_threshold

    def is_valid(self, idle_timeout_minutes: int = 30, absolute_timeout_minutes: int = 35) -> bool:
        """
        Check if session is valid (not expired by any timeout type and not invalidated).
        
        Args:
            idle_timeout_minutes: Idle timeout in minutes
            absolute_timeout_minutes: Absolute timeout in minutes
        
        Returns:
            True if session is active and within all timeout thresholds
        """
        if not self.is_active:
            return False
        if self.invalidated_at is not None:
            return False
        if self.is_idle_expired(idle_timeout_minutes):
            return False
        if self.is_absolute_expired(absolute_timeout_minutes):
            return False
        return True

    def reset_idle_timer(self) -> None:
        """
        Reset the idle timer by updating last_activity to current time.
        Called on each authenticated request to prevent idle timeout.
        """
        self.last_activity = datetime.utcnow()

    def invalidate(self) -> None:
        """
        Invalidate the session immediately (e.g., on logout).
        """
        self.is_active = False
        self.invalidated_at = datetime.utcnow()
