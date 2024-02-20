from pydantic import BaseModel, EmailStr
from datetime import datetime


class BaseOAuthClient(BaseModel):
    name: str


class OAuthClientCreate(BaseOAuthClient):
    password: str


class OAuthClient(BaseOAuthClient):
    id: int
    client_id: str
    secret_key: str

    class Config:
        from_attributes = True


class OAuthProvideRequest(BaseModel):
    client_id: str
    client_secret: str
    grant_type: str
    username: EmailStr | None = None
    password: str | None = None
    refresh_token: str | None = None


class OAuthRevokeRequest(BaseModel):
    client_id: str
    client_secret: str
    token: str


class OAuthProvideResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    scope: str


class IntrospectResponse(BaseModel):
    client_id: str
    username: EmailStr
    scope: str
    exp: int
    active: bool
