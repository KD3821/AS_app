from fastapi import APIRouter, Depends

from services.oauth2 import OAuthService
from services.auth import AuthService
from models.oauth2 import (
    OAuthClientCreate,
    OAuthClient,
    OAuthProvideRequest,
    OAuthProvideResponse,
    OAuthRevokeRequest,
    IntrospectRequest,
    IntrospectResponse,
)


router = APIRouter(
    prefix='/clients',
    tags=['OAuth Clients']
)


@router.post('/register', response_model=OAuthClient)
def register(
    client_data: OAuthClientCreate,
    service: OAuthService = Depends()
):
    """
    Register Client of OAuth Service.
    """
    return service.register_client(client_data)


@router.post('/keys', response_model=OAuthClient)
def keys(
    auth_data: OAuthClientCreate,
    service: OAuthService = Depends()
):
    """
    Request Client's service credentials
    """
    return service.remind_creds(name=auth_data.name, password=auth_data.password)


@router.post('/token/', response_model=OAuthProvideResponse)
def provide(
    oauth_data: OAuthProvideRequest,
    service: OAuthService = Depends(),
    user_service: AuthService = Depends()
):
    """
    Validate credentials or refresh token & Provide Access and Refresh tokens
    """
    data = {
        'client_id': oauth_data.client_id,
        'secret_key': oauth_data.client_secret,
        'grant_type': oauth_data.grant_type,
        'email': oauth_data.username,
        'password': oauth_data.password,
        'refresh_token': oauth_data.refresh_token,
    }
    return service.provide_oauth(data, user_service)


@router.post('/revoke_token/')
def revoke(
    token_data: OAuthRevokeRequest,
    service: OAuthService = Depends()
):
    """
    Revoke User's Access and Refresh tokens
    """
    return service.revoke_token(token_data)


@router.post('/introspect/')
def introspect(
    introspect_data: IntrospectRequest,
    service: OAuthService = Depends(),
    user_service: AuthService = Depends()
):
    return service.check_token(introspect_data, user_service)


"""
{
    "access_token": "KraHxV8vO4oI0nsfIR1Lzbe3TP8XBB",
    "expires_in": 36000,
    "token_type": "Bearer",
    "scope": "read write groups",
    "refresh_token": "f1UsFpkiTzNV8Cw98QwoIcXHFcEuw2"
}
"""