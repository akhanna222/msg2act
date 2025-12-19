"""
Security utilities for authentication, encryption, and token management
"""
import base64
from datetime import datetime, timedelta
from typing import Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryption for OAuth tokens
cipher_suite = Fernet(settings.ENCRYPTION_KEY.encode())


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def encrypt_token(token: str) -> str:
    """
    Encrypt an OAuth token for secure storage

    Args:
        token: Plain text token

    Returns:
        Base64 encoded encrypted token
    """
    encrypted = cipher_suite.encrypt(token.encode())
    return base64.b64encode(encrypted).decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt an OAuth token

    Args:
        encrypted_token: Base64 encoded encrypted token

    Returns:
        Plain text token
    """
    encrypted_bytes = base64.b64decode(encrypted_token.encode())
    decrypted = cipher_suite.decrypt(encrypted_bytes)
    return decrypted.decode()
