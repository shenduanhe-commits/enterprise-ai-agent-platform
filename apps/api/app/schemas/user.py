from datetime import datetime

from pydantic import BaseModel, EmailStr


# 创建用户请求
class UserCreate(BaseModel):
    email: EmailStr
    password: str


# 用户响应
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
