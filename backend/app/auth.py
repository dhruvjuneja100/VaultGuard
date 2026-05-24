from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# =============================================
# VAULTGUARD — Authentication Module
# Handles JWT token creation and validation
#
# JWT = JSON Web Token
# Industry standard for API authentication
# Used by every major financial API
# =============================================

# Load environment variables from .env file
load_dotenv()

# ── Configuration ──
# os.getenv() reads from .env file
# Second argument is default if not found
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

# Demo credentials from .env
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "admin")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "vaultguard123")

# ── Password Hashing ──
# Never store plain text passwords!
# bcrypt is industry standard hashing algorithm
# Even if database is hacked, passwords are safe
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ── OAuth2 Scheme ──
# Tells FastAPI where to find the token
# "token" = the endpoint that gives tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# =============================================
# PYDANTIC MODELS
# =============================================

class Token(BaseModel):
    """Response when user logs in successfully"""
    access_token: str
    token_type:   str  # Always "bearer"


class TokenData(BaseModel):
    """Data stored inside JWT token"""
    username: Optional[str] = None


class User(BaseModel):
    """User model"""
    username: str


# =============================================
# HELPER FUNCTIONS
# =============================================

def verify_password(plain_password: str,
                    hashed_password: str) -> bool:
    """
    Check if plain password matches hashed password.
    
    bcrypt is one-way — you can't reverse it.
    We hash the input and compare hashes.
    
    Example:
    plain:  "vaultguard123"
    hashed: "$2b$12$..." (60 char hash)
    → bcrypt hashes plain and compares to stored hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password.
    Used when creating new users.
    
    Same password → different hash each time
    (bcrypt adds random "salt")
    This prevents rainbow table attacks
    """
    return pwd_context.hash(password)


def authenticate_user(username: str,
                      password: str) -> Optional[User]:
    """
    Verify username and password.
    Simple comparison for demo purposes.
    In production: hash passwords and store in database.
    """
    # Check username and password directly
    if username != DEMO_USERNAME:
        return None

    if password != DEMO_PASSWORD:
        return None

    return User(username=username)

def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = None
                        ) -> str:
    """
    Create a JWT token containing user data.
    
    JWT structure:
    Header.Payload.Signature
    
    Header:  algorithm used
    Payload: data we store (username, expiry)
    Signature: cryptographic proof of validity
    
    Only our server can create valid signatures
    (because only we know SECRET_KEY)
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    # Add expiry to token payload
    to_encode.update({"exp": expire})

    # Create signed JWT token
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency — validates JWT token on every request.
    
    FastAPI Depends() runs this before the endpoint.
    If token is invalid → request is rejected.
    If token is valid   → user is passed to endpoint.
    
    This protects endpoints from unauthorized access.
    """

    # Standard HTTP 401 error for auth failures
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode and verify JWT token
        # jwt.decode() automatically checks:
        # → Signature is valid (not tampered)
        # → Token has not expired
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # Extract username from token payload
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username)

    except JWTError:
        # Token is invalid or expired
        raise credentials_exception

    return User(username=token_data.username)