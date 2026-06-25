"""Unit tests for JWT token utilities"""
import pytest
from datetime import timedelta
from uuid import uuid4

from app.utils.jwt_utils import (
    create_access_token,
    create_refresh_token,
    verify_token,
    extract_user_id_from_token
)


class TestCreateAccessToken:
    """Test JWT access token creation"""
    
    def test_create_valid_token(self):
        """Test creating a valid access token"""
        user_id = str(uuid4())
        token_data = {
            "sub": user_id,
            "username": "testuser",
            "role": "Manager"
        }
        
        token = create_access_token(token_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts separated by dots
    
    def test_create_token_with_custom_expiration(self):
        """Test creating token with custom expiration time"""
        user_id = str(uuid4())
        token_data = {
            "sub": user_id,
            "username": "testuser"
        }
        custom_delta = timedelta(hours=2)
        
        token = create_access_token(token_data, custom_delta)
        
        assert token is not None
        payload = verify_token(token)
        assert payload["sub"] == user_id
        assert payload["username"] == "testuser"
    
    def test_token_contains_subject_and_data(self):
        """Test that token contains payload data"""
        user_id = str(uuid4())
        token_data = {
            "sub": user_id,
            "username": "john_doe",
            "role": "Admin"
        }
        
        token = create_access_token(token_data)
        payload = verify_token(token)
        
        assert payload["sub"] == user_id
        assert payload["username"] == "john_doe"
        assert payload["role"] == "Admin"


class TestVerifyToken:
    """Test JWT token verification"""
    
    def test_verify_valid_token(self):
        """Test verifying a valid token"""
        user_id = str(uuid4())
        token_data = {
            "sub": user_id,
            "username": "testuser",
            "role": "Manager"
        }
        token = create_access_token(token_data)
        
        payload = verify_token(token)
        
        assert payload["sub"] == user_id
        assert payload["username"] == "testuser"
        assert payload["role"] == "Manager"
    
    def test_verify_expired_token(self):
        """Test that expired token raises ValueError"""
        user_id = str(uuid4())
        token_data = {
            "sub": user_id,
            "username": "testuser"
        }
        # Create already-expired token
        expires_delta = timedelta(hours=-1)
        token = create_access_token(token_data, expires_delta)
        
        with pytest.raises(ValueError) as exc_info:
            verify_token(token)
        
        assert "expired" in str(exc_info.value).lower()
    
    def test_verify_invalid_token(self):
        """Test that invalid token raises ValueError"""
        invalid_token = "invalid.token.data"
        
        with pytest.raises(ValueError):
            verify_token(invalid_token)
    
    def test_verify_malformed_token(self):
        """Test that malformed token raises ValueError"""
        malformed_token = "not-a-real-token"
        
        with pytest.raises(ValueError):
            verify_token(malformed_token)
    
    def test_verify_token_with_tampered_payload(self):
        """Test that tampered token is detected"""
        user_id = str(uuid4())
        token_data = {
            "sub": user_id,
            "username": "testuser"
        }
        token = create_access_token(token_data)
        
        # Tamper with the token by changing signature
        tampered_token = token[:-5] + "xxxxx"
        
        with pytest.raises(ValueError):
            verify_token(tampered_token)


class TestExtractUserIdFromToken:
    """Test user ID extraction from tokens"""
    
    def test_extract_user_id_from_valid_token(self):
        """Test extracting user ID from valid token"""
        user_id = str(uuid4())
        token_data = {
            "sub": user_id,
            "username": "testuser"
        }
        token = create_access_token(token_data)
        
        extracted_id = extract_user_id_from_token(token)
        
        assert extracted_id == user_id
    
    def test_extract_user_id_from_expired_token(self):
        """Test that extracting from expired token raises ValueError"""
        user_id = str(uuid4())
        token_data = {
            "sub": user_id,
            "username": "testuser"
        }
        expires_delta = timedelta(hours=-1)
        token = create_access_token(token_data, expires_delta)
        
        with pytest.raises(ValueError) as exc_info:
            extract_user_id_from_token(token)
        
        assert "expired" in str(exc_info.value).lower()
    
    def test_extract_user_id_from_token_missing_sub(self):
        """Test extracting from token without 'sub' claim"""
        token_data = {
            "username": "testuser"
            # Missing 'sub' claim
        }
        token = create_access_token(token_data)
        
        with pytest.raises(ValueError) as exc_info:
            extract_user_id_from_token(token)
        
        assert "not found" in str(exc_info.value).lower()


class TestCreateRefreshToken:
    """Test JWT refresh token creation"""
    
    def test_create_refresh_token(self):
        """Test creating a refresh token"""
        user_id = str(uuid4())
        token_data = {
            "sub": user_id,
            "username": "testuser"
        }
        
        token = create_refresh_token(token_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert token.count('.') == 2
    
    def test_refresh_token_has_longer_expiration(self):
        """Test that refresh token has longer expiration than access token"""
        user_id = str(uuid4())
        token_data = {
            "sub": user_id,
            "username": "testuser"
        }
        
        access_token = create_access_token(token_data, timedelta(hours=1))
        refresh_token = create_refresh_token(token_data)
        
        access_payload = verify_token(access_token)
        refresh_payload = verify_token(refresh_token)
        
        # Refresh token should expire later than access token
        assert refresh_payload["exp"] > access_payload["exp"]


# Property-based tests using hypothesis
@pytest.mark.pytest_asyncio
class TestTokenProperties:
    """Property-based tests for token validation"""
    
    def test_token_is_always_valid_when_freshly_created(self):
        """Test that tokens are always valid immediately after creation"""
        for _ in range(10):
            user_id = str(uuid4())
            token_data = {"sub": user_id}
            token = create_access_token(token_data)
            
            # Should not raise
            payload = verify_token(token)
            assert payload["sub"] == user_id
    
    def test_token_payload_round_trip(self):
        """Test that payload survives round-trip encoding/decoding"""
        test_payloads = [
            {"sub": str(uuid4()), "username": "user1", "role": "Admin"},
            {"sub": str(uuid4()), "username": "user2", "role": "Manager"},
            {"sub": str(uuid4()), "data": "some_value", "count": 42},
        ]
        
        for original_data in test_payloads:
            token = create_access_token(original_data)
            decoded_payload = verify_token(token)
            
            # All original keys should be present
            for key, value in original_data.items():
                assert decoded_payload[key] == value
