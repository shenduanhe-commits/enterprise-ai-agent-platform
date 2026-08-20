from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def _encode(user_id: int, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(UTC) + expires_delta
    return jwt.encode(
        {
            "sub": str(user_id),
            "typ": token_type,
            "exp": expire,
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    # exp 必须是「过期的那一刻」，不能是一段时长。
    delta = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.JWT_EXPIRES_IN)
    )
    return _encode(user_id, "access", delta)


def create_refresh_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    delta = (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.JWT_REFRESH_EXPIRES_IN)
    )
    return _encode(user_id, "refresh", delta)


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
