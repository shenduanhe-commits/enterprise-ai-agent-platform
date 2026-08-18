from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.core.exceptions import UnauthorizedException
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.schemas.user import UserLogin
from app.services.user_service import UserService


def _user(**overrides):
    data = {
        "id": 1,
        "email": "a@eaap.com",
        "created_at": datetime.now(UTC),
        "password_hash": hash_password("secret"),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class FakeUserRepository:
    def __init__(self, user=None):
        self.user = user

    async def get_by_email(self, db, email):
        if self.user and self.user.email == email:
            return self.user
        return None

    async def get_by_id(self, db, user_id):
        if self.user and self.user.id == user_id:
            return self.user
        return None


@pytest.mark.asyncio
async def test_login_rejects_bad_password_with_401():
    service = UserService(FakeUserRepository(_user()))

    with pytest.raises(UnauthorizedException, match="邮箱或密码错误"):
        await service.login(None, UserLogin(email="a@eaap.com", password="wrong"))


@pytest.mark.asyncio
async def test_login_returns_access_and_refresh():
    service = UserService(FakeUserRepository(_user()))

    tokens = await service.login(None, UserLogin(email="a@eaap.com", password="secret"))

    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.token_type == "bearer"
    assert tokens.user.email == "a@eaap.com"


@pytest.mark.asyncio
async def test_refresh_rejects_access_token():
    service = UserService(FakeUserRepository(_user()))
    access = create_access_token(1)

    with pytest.raises(UnauthorizedException, match="Token 无效"):
        await service.refresh_tokens(None, access)


@pytest.mark.asyncio
async def test_get_user_by_token_rejects_refresh_token():
    service = UserService(FakeUserRepository(_user()))
    refresh = create_refresh_token(1)

    with pytest.raises(UnauthorizedException, match="Token 无效"):
        await service.get_user_by_token(None, refresh)


@pytest.mark.asyncio
async def test_refresh_issues_new_pair():
    service = UserService(FakeUserRepository(_user()))
    refresh = create_refresh_token(1)

    tokens = await service.refresh_tokens(None, refresh)

    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.user.id == 1
