"""JWT token utilities for authentication"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional timedelta for custom expiration time
                      If not provided, uses settings.access_token_expire_hours
    
    Returns:
        Encoded JWT token string
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
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional timedelta for custom expiration time
                      If not provided, uses settings.refresh_token_expire_days
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
    
    Returns:
        Decoded token payload (dictionary)
    
    Raises:
        ValueError: If token is invalid, expired, or malformed
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as e:
        if "expired" in str(e).lower():
            raise ValueError("Token has expired") from e
        else:
            raise ValueError("Invalid token") from e


def extract_user_id_from_token(token: str) -> str:
    """
    Extract the user ID from a JWT token's 'sub' claim.
    
    Args:
        token: JWT token string
    
    Returns:
        User ID string
    
    Raises:
        ValueError: If token is invalid, expired, or missing 'sub' claim
    """
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("User ID not found in token")
    
    return user_id


def extract_claim(token: str, claim_name: str) -> Optional[Any]:
    """
    Extract a specific claim from a JWT token.
    
    Args:
        token: JWT token string
        claim_name: Name of the claim to extract
    
    Returns:
        Claim value if present, None otherwise
    
    Raises:
        ValueError: If token is invalid or expired
    """
    payload = verify_token(token)
    return payload.get(claim_name)
