from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional, Dict
from jose import JWTError, jwt
import uuid
from .config import settings

# Use bcrypt directly to avoid passlib/bcrypt version conflicts
import bcrypt

class PasswordContext:
    """Simple password context to replace passlib."""
    
    @staticmethod
    def hash(password: str) -> str:
        """Hash a password."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
# Password context for hashing
pwd_context = PasswordContext()

# Token settings
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
_SECRET_KEY = settings.SECRET_KEY
_ALGORITHM = settings.ALGORITHM
_ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
_REFRESH_TOKEN_EXPIRE_DAYS = getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7)


def _create_token(
    subject: Union[str, Any],
    token_type: str,
    expires_delta: timedelta,
) -> str:
    """Internal helper for JWT creation."""
    now = datetime.now(tz=timezone.utc)
    expire = now + expires_delta
    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    expires = expires_delta or timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, TOKEN_TYPE_ACCESS, expires)


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT refresh token."""
    expires = expires_delta or timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(subject, TOKEN_TYPE_REFRESH, expires)


def verify_token(token: str, token_type: str = TOKEN_TYPE_ACCESS) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(
            token,
            _SECRET_KEY,
            algorithms=[_ALGORITHM],
        )
    except JWTError:
        return None

    if payload.get("type") != token_type:
        return None

    return payload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if not plain_password or not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    if not password:
        raise ValueError("Password cannot be empty")
    return pwd_context.hash(password)

def is_token_expired(token: str) -> bool:
    """Check if token is expired."""
    try:
        payload = jwt.decode(
            token,
            _SECRET_KEY,
            algorithms=[_ALGORITHM],
            options={"verify_exp": False},
        )
        exp = payload.get("exp")
        if exp is None:
            return True
        return datetime.now(tz=timezone.utc).timestamp() > float(exp)
    except JWTError:
        return True


def get_token_remaining_time(token: str) -> Optional[int]:
    """Get remaining time in seconds for token."""
    try:
        payload = jwt.decode(
            token,
            _SECRET_KEY,
            algorithms=[_ALGORITHM],
            options={"verify_exp": False},
        )
        exp = payload.get("exp")
        if exp is None:
            return None
        remaining = float(exp) - datetime.now(tz=timezone.utc).timestamp()
        return max(0, int(remaining))
    except JWTError:
        return None