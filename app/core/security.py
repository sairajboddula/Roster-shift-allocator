"""Password hashing and JWT utilities."""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(data: dict[str, Any], expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire_mins = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expire_mins)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return None
