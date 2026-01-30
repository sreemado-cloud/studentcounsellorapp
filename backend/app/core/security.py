from datetime import datetime, timedelta
from typing import Optional
import secrets
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.database import get_database, get_default_database
from app.core.validators import validate_object_id
from app.core.token_revocation import session_exists

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, str, datetime]:
    """
    Create JWT with jti for revocation.
    Returns (encoded_jwt, jti, expire).
    """
    to_encode = data.copy()
    jti = secrets.token_hex(16)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": jti})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, jti, expire


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validates JWT token and returns the current user.
    This is the core of multi-tenancy - all subsequent queries use this user's ID.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        uid = validate_object_id(user_id, "sub")
    except Exception:
        raise credentials_exception

    if jti and not await session_exists(jti):
        raise credentials_exception

    # Always use shared DB for auth user lookup (avoids tenant DB mixups for institution etc.)
    default_db = get_default_database()
    user = await default_db.users.find_one({"_id": uid})

    if user is None:
        raise credentials_exception

    user["id"] = str(user["_id"])
    return user


async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Ensures the user account is active"""
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
