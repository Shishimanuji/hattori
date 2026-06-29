"""
Tests for session timeout management (Task 4.6)

Validates:
- Requirements 20.4 (Session Timeout)
- Requirements 20.5 (Auto-logout)

Tests idle timeout (30 minutes) and absolute timeout (35 minutes) functionality.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session as DBSession
import uuid

from app.models.session import Session
from app.models.user import User, UserRole
from app.services.session_service import (
    SessionService,
    SessionNotFoundError,
    SessionExpiredError
)
from app.services.auth_service import AuthService
from app.utils.auth import AuthUtils
from app.core.config import settings


@pytest.fixture
def test_user(db: DBSession):
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash=AuthUtils.hash_password("testpass123"),
        role=UserRole.MANAGER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_session(db: DBSession, test_user: User):
    \"\"\"Create a test session\"\"\"
    session = Session(
        id=uuid.uuid4(),
        user_id=test_user.id,
        token_hash=\"test_token_hash_123\",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=35),
        last_activity=datetime.utcnow(),
        is_active=True
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


class TestSessionIdleTimeout:
    \"\"\"Tests for idle timeout (30 minutes)\"\"\"

    def test_idle_timeout_not_expired_when_recently_active(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.4 - Session Timeout**
        
        Session should NOT expire when recently active (within 30 minutes).
        \"\"\"
        # Set last_activity to 10 minutes ago
        test_session.last_activity = datetime.utcnow() - timedelta(minutes=10)
        
        # Idle timeout should not be exceeded
        assert not test_session.is_idle_expired(idle_timeout_minutes=30)

    def test_idle_timeout_expired_after_30_minutes_inactivity(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.4 - Session Timeout**
        
        Session should expire when idle for 30 minutes.
        \"\"\"
        # Set last_activity to 31 minutes ago
        test_session.last_activity = datetime.utcnow() - timedelta(minutes=31)
        
        # Idle timeout should be exceeded
        assert test_session.is_idle_expired(idle_timeout_minutes=30)

    def test_idle_timeout_exactly_30_minutes(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.4 - Session Timeout**
        
        Session at exactly 30 minutes should still be valid.
        \"\"\"
        # Set last_activity to exactly 30 minutes ago
        test_session.last_activity = datetime.utcnow() - timedelta(minutes=30)
        
        # At exactly 30 minutes, should not yet be expired
        # (expires when > 30 minutes, not >= 30 minutes)
        assert not test_session.is_idle_expired(idle_timeout_minutes=30)

    def test_idle_timeout_just_over_30_minutes(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.4 - Session Timeout**
        
        Session just over 30 minutes should be expired.
        \"\"\"
        # Set last_activity to 30 minutes and 1 second ago
        test_session.last_activity = datetime.utcnow() - timedelta(minutes=30, seconds=1)
        
        # Just over 30 minutes should be expired
        assert test_session.is_idle_expired(idle_timeout_minutes=30)


class TestSessionAbsoluteTimeout:
    \"\"\"Tests for absolute timeout (35 minutes total lifetime)\"\"\"

    def test_absolute_timeout_not_expired_at_20_minutes(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.5 - Auto-logout**
        
        Session should NOT expire at 20 minutes total age.
        \"\"\"
        # Set created_at to 20 minutes ago
        test_session.created_at = datetime.utcnow() - timedelta(minutes=20)
        
        # Absolute timeout should not be exceeded
        assert not test_session.is_absolute_expired(absolute_timeout_minutes=35)

    def test_absolute_timeout_expired_after_35_minutes(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.5 - Auto-logout**
        
        Session should expire after 35 minutes total age regardless of activity.
        \"\"\"
        # Set created_at to 36 minutes ago
        test_session.created_at = datetime.utcnow() - timedelta(minutes=36)
        
        # Absolute timeout should be exceeded
        assert test_session.is_absolute_expired(absolute_timeout_minutes=35)

    def test_absolute_timeout_overrides_activity(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.5 - Auto-logout**
        
        Session should expire by absolute timeout even if recently active.
        \"\"\"
        # Set created_at to 36 minutes ago (exceeds absolute timeout)
        test_session.created_at = datetime.utcnow() - timedelta(minutes=36)
        
        # Even if last_activity is very recent, absolute timeout applies
        test_session.last_activity = datetime.utcnow() - timedelta(seconds=1)
        
        # Should be expired by absolute timeout
        assert test_session.is_absolute_expired(absolute_timeout_minutes=35)


class TestSessionValidity:
    \"\"\"Tests for combined session validity checks\"\"\"

    def test_session_valid_when_recently_created_and_active(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.4**
        
        Session should be valid when recently created and active.
        \"\"\"
        test_session.is_active = True
        test_session.invalidated_at = None
        test_session.created_at = datetime.utcnow() - timedelta(minutes=5)
        test_session.last_activity = datetime.utcnow() - timedelta(minutes=2)
        
        assert test_session.is_valid()

    def test_session_invalid_when_idle_expired(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.4**
        
        Session should be invalid when idle timeout exceeded.
        \"\"\"
        test_session.is_active = True
        test_session.invalidated_at = None
        test_session.last_activity = datetime.utcnow() - timedelta(minutes=31)
        test_session.created_at = datetime.utcnow() - timedelta(minutes=20)
        
        assert not test_session.is_valid()

    def test_session_invalid_when_absolute_expired(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.5**
        
        Session should be invalid when absolute timeout exceeded.
        \"\"\"
        test_session.is_active = True
        test_session.invalidated_at = None
        test_session.created_at = datetime.utcnow() - timedelta(minutes=36)
        test_session.last_activity = datetime.utcnow() - timedelta(minutes=1)
        
        assert not test_session.is_valid()

    def test_session_invalid_when_inactive(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.2**
        
        Session should be invalid when marked inactive.
        \"\"\"
        test_session.is_active = False
        test_session.created_at = datetime.utcnow() - timedelta(minutes=5)
        test_session.last_activity = datetime.utcnow() - timedelta(minutes=2)
        
        assert not test_session.is_valid()

    def test_session_invalid_when_invalidated(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.2**
        
        Session should be invalid when explicitly invalidated.
        \"\"\"
        test_session.is_active = True
        test_session.invalidated_at = datetime.utcnow() - timedelta(minutes=1)
        test_session.created_at = datetime.utcnow() - timedelta(minutes=5)
        test_session.last_activity = datetime.utcnow() - timedelta(minutes=2)
        
        assert not test_session.is_valid()


class TestSessionIdleTimerReset:
    \"\"\"Tests for resetting the idle timer\"\"\"

    def test_reset_idle_timer_updates_last_activity(self, db: DBSession, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.4**
        
        Calling reset_idle_timer should update last_activity to current time.
        \"\"\"
        old_time = test_session.last_activity
        
        # Wait a moment and reset
        import time
        time.sleep(0.1)  # 100ms to ensure time difference
        
        test_session.reset_idle_timer()
        
        # last_activity should be updated to approximately now
        assert test_session.last_activity > old_time

    def test_reset_idle_timer_prevents_idle_timeout(self, db: DBSession, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.4**
        
        After resetting idle timer, session should not be idle expired.
        \"\"\"
        test_session.last_activity = datetime.utcnow() - timedelta(minutes=29)
        
        # After reset, last_activity should be current
        test_session.reset_idle_timer()
        
        # Should no longer be idle expired
        assert not test_session.is_idle_expired(idle_timeout_minutes=30)


class TestSessionInvalidation:
    \"\"\"Tests for session invalidation\"\"\"

    def test_invalidate_session_marks_inactive(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.2 - Logout**
        
        Calling invalidate_session should mark session as inactive.
        \"\"\"
        test_session.invalidate()
        
        assert not test_session.is_active
        assert test_session.invalidated_at is not None

    def test_invalidated_session_is_not_valid(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.2 - Logout**
        
        Invalidated session should not be valid.
        \"\"\"
        test_session.invalidate()
        
        assert not test_session.is_valid()


class TestSessionServiceValidation:
    \"\"\"Tests for SessionService timeout validation\"\"\"

    def test_validate_session_timeout_passes_for_valid_session(
        self,
        db: DBSession,
        test_session: Session
    ):
        \"\"\"
        **Validates: Requirement 20.4**
        
        validate_session_timeout should return True for valid session.
        \"\"\"
        result = SessionService.validate_session_timeout(test_session)
        assert result is True

    def test_validate_session_timeout_raises_for_idle_expired(
        self,
        db: DBSession,
        test_session: Session
    ):
        \"\"\"
        **Validates: Requirement 20.4**
        
        validate_session_timeout should raise SessionExpiredError for idle timeout.
        \"\"\"
        test_session.last_activity = datetime.utcnow() - timedelta(minutes=31)
        
        with pytest.raises(SessionExpiredError) as exc_info:
            SessionService.validate_session_timeout(test_session)
        
        assert \"inactivity\" in str(exc_info.value)

    def test_validate_session_timeout_raises_for_absolute_expired(
        self,
        db: DBSession,
        test_session: Session
    ):
        \"\"\"
        **Validates: Requirement 20.5**
        
        validate_session_timeout should raise SessionExpiredError for absolute timeout.
        \"\"\"
        test_session.created_at = datetime.utcnow() - timedelta(minutes=36)
        
        with pytest.raises(SessionExpiredError):
            SessionService.validate_session_timeout(test_session)

    def test_validate_session_timeout_raises_for_inactive(
        self,
        db: DBSession,
        test_session: Session
    ):
        \"\"\"
        **Validates: Requirement 20.2**
        
        validate_session_timeout should raise for inactive session.
        \"\"\"
        test_session.is_active = False
        
        with pytest.raises(SessionExpiredError):
            SessionService.validate_session_timeout(test_session)


class TestSessionServiceDatabaseOperations:
    \"\"\"Tests for SessionService database operations\"\"\"

    def test_get_session_by_token_hash_returns_session(
        self,
        db: DBSession,
        test_session: Session
    ):
        \"\"\"
        **Validates: Requirement 20.1**
        
        Should retrieve session by token hash.
        \"\"\"
        retrieved = SessionService.get_session_by_token_hash(
            db=db,
            token_hash=test_session.token_hash
        )
        
        assert retrieved.id == test_session.id
        assert retrieved.user_id == test_session.user_id

    def test_get_session_by_token_hash_raises_for_missing(self, db: DBSession):
        \"\"\"
        **Validates: Requirement 20.1**
        
        Should raise SessionNotFoundError for non-existent token.
        \"\"\"
        with pytest.raises(SessionNotFoundError):
            SessionService.get_session_by_token_hash(
                db=db,
                token_hash=\"nonexistent_hash\"
            )

    def test_invalidate_session_in_database(self, db: DBSession, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.2 - Logout**
        
        Invalidating session should persist to database.
        \"\"\"
        SessionService.invalidate_session(test_session, db)
        
        # Fetch fresh from database
        reloaded = db.query(Session).filter(Session.id == test_session.id).first()
        
        assert not reloaded.is_active
        assert reloaded.invalidated_at is not None

    def test_reset_idle_timer_in_database(self, db: DBSession, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.4**
        
        Resetting idle timer should persist to database.
        \"\"\"
        old_activity = test_session.last_activity
        
        import time
        time.sleep(0.1)
        
        SessionService.reset_idle_timer(test_session, db)
        
        # Fetch fresh from database
        reloaded = db.query(Session).filter(Session.id == test_session.id).first()
        
        assert reloaded.last_activity > old_activity

    def test_get_user_active_sessions(
        self,
        db: DBSession,
        test_user: User,
        test_session: Session
    ):
        \"\"\"
        **Validates: Requirement 20.1**
        
        Should retrieve all active sessions for a user.
        \"\"\"
        # Create another session for same user
        session2 = Session(
            id=uuid.uuid4(),
            user_id=test_user.id,
            token_hash=\"another_token_hash\",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=35),
            last_activity=datetime.utcnow(),
            is_active=True
        )
        db.add(session2)
        db.commit()
        
        sessions = SessionService.get_user_active_sessions(db, test_user.id)
        
        assert len(sessions) == 2
        assert all(s.is_active for s in sessions)
        assert all(s.user_id == test_user.id for s in sessions)

    def test_cleanup_expired_sessions(self, db: DBSession, test_user: User):
        \"\"\"
        **Validates: Requirement 20.5 - Auto-logout**
        
        Cleanup should mark expired sessions as inactive.
        \"\"\"
        # Create an expired session
        expired_session = Session(
            id=uuid.uuid4(),
            user_id=test_user.id,
            token_hash=\"expired_token_hash\",
            created_at=datetime.utcnow() - timedelta(minutes=40),
            expires_at=datetime.utcnow() - timedelta(minutes=5),
            last_activity=datetime.utcnow() - timedelta(minutes=40),
            is_active=True
        )
        db.add(expired_session)
        db.commit()
        
        # Run cleanup
        count = SessionService.cleanup_expired_sessions(db)
        
        assert count >= 1
        
        # Check it was marked inactive
        reloaded = db.query(Session).filter(Session.id == expired_session.id).first()
        assert not reloaded.is_active


class TestAuthServiceLoginFlow:
    \"\"\"Tests for authentication service login flow\"\"\"

    def test_login_and_create_session_generates_valid_token(
        self,
        db: DBSession,
        test_user: User
    ):
        \"\"\"
        **Validates: Requirement 20.1 - Session Creation**
        
        Login should create valid JWT token and session.
        \"\"\"
        token, session = AuthService.login_and_create_session(
            db=db,
            username=test_user.username,
            password=\"testpass123\"
        )
        
        assert token is not None
        assert len(token) > 0
        assert session.user_id == test_user.id
        assert session.is_active

    def test_session_expiration_set_correctly(
        self,
        db: DBSession,
        test_user: User
    ):
        \"\"\"
        **Validates: Requirement 20.5**
        
        Session expiration should be set to created_at + 35 minutes.
        \"\"\"
        token, session = AuthService.login_and_create_session(
            db=db,
            username=test_user.username,
            password=\"testpass123\"
        )
        
        expected_expiration = session.created_at + timedelta(minutes=settings.absolute_timeout_minutes)
        
        # Allow 1 second difference for execution time
        time_diff = abs((session.expires_at - expected_expiration).total_seconds())
        assert time_diff < 1

    def test_session_created_at_and_last_activity_equal_on_login(
        self,
        db: DBSession,
        test_user: User
    ):
        \"\"\"
        **Validates: Requirement 20.4**
        
        On login, created_at and last_activity should be approximately equal.
        \"\"\"
        token, session = AuthService.login_and_create_session(
            db=db,
            username=test_user.username,
            password=\"testpass123\"
        )
        
        # Should be within 1 second
        time_diff = abs((session.created_at - session.last_activity).total_seconds())
        assert time_diff < 1


class TestTimeoutErrorMessages:
    \"\"\"Tests for appropriate error messages on timeout\"\"\"

    def test_idle_timeout_error_message(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.4**
        
        Idle timeout should return specific error message.
        \"\"\"
        test_session.last_activity = datetime.utcnow() - timedelta(minutes=31)
        
        try:
            SessionService.validate_session_timeout(test_session)
            assert False, \"Should have raised SessionExpiredError\"
        except SessionExpiredError as e:
            assert \"inactivity\" in str(e).lower()

    def test_absolute_timeout_error_message(self, test_session: Session):
        \"\"\"
        **Validates: Requirement 20.5**
        
        Absolute timeout should return generic expired message.
        \"\"\"
        test_session.created_at = datetime.utcnow() - timedelta(minutes=36)
        
        try:
            SessionService.validate_session_timeout(test_session)
            assert False, \"Should have raised SessionExpiredError\"
        except SessionExpiredError as e:
            error_msg = str(e).lower()
            assert \"expired\" in error_msg
