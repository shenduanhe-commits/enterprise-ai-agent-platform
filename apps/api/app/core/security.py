from datetime import datetime, timedelta, timezone

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


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    # exp 必须是「过期的那一刻」，不能是一段时长。
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.JWT_EXPIRES_IN)
    )
    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": expire,
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
