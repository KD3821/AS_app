from pydantic import BaseModel, EmailStr
from datetime import datetime


class BaseUser(BaseModel):
    email: EmailStr


class UserCreate(BaseUser):
    is_admin: bool
    password: str


class User(BaseUser):
    id: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access: str
    token_type: str | None = 'Bearer'


class AccessToken(BaseModel):
    access: str
    expire_date: datetime
    scope: str
    token_type: str = 'Bearer'


class RefreshToken(BaseModel):
    refresh: str
    expire_date: datetime
