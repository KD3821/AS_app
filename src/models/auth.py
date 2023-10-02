from pydantic import BaseModel, EmailStr


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
    access_token: str
    token_type: str = 'bearer'

