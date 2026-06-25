"""Authentication and authorization utilities"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import hashlib
import logging
from jose import JWTError, jwt
from app.core.config import settings

logger = logging.getLogger(__name__)

# Try to use bcrypt, fall back to simple hashing if bcrypt fails
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    USE_BCRYPT = True
except Exception as e:
    logger.warning(f"BCrypt unavailable, using SHA256 fallback: {e}")
    USE_BCRYPT = False
    pwd_context = None


class AuthUtils:
    """Utilities for authentication operations"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt or SHA256 fallback"""
        if USE_BCRYPT and pwd_context:
            try:
                return pwd_context.hash(password)
            except Exception as e:
                logger.warning(f"BCrypt failed, using SHA256: {e}")
                return hashlib.sha256(password.encode()).hexdigest()
        else:
            return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain text password against a bcrypt hash or SHA256"""
        if USE_BCRYPT and pwd_context:
            try:
                return pwd_context.verify(plain_password, hashed_password)
            except Exception as e:
                logger.warning(f"BCrypt verify failed, trying SHA256: {e}")
                # Try SHA256 fallback
                return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
        else:
            return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, datetime]:
        """
        Create a JWT access token.
        
        Args:
            data: Dictionary of claims to encode
            expires_delta: Optional timedelta for token expiration
        
        Returns:
            Tuple of (token, expiration_datetime)
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.access_token_expire_hours)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
        return encoded_jwt, expire

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            return payload
        except JWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None

    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a JWT token using SHA256 for secure storage.
        
        Args:
            token: JWT token to hash
        
        Returns:
            SHA256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def extract_token_from_header(auth_header: Optional[str]) -> Optional[str]:
        """
        Extract the token from an Authorization header.
        Expected format: "Bearer <token>"
        
        Args:
            auth_header: Authorization header value
        
        Returns:
            Token string if valid format, None otherwise
        """
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
