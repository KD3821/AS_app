import json

from fastapi import APIRouter, Depends, Request

from services.oauth2 import OAuthService
from models.oauth2 import (
    OAuthClientCreate,
    OAuthClient,
    OAuthProvideRequest,
    OAuthProvideResponse,
    OAuthRevokeRequest,
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
    service: OAuthService = Depends()
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
    return service.provide_oauth(data)


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
async def introspect(
    introspect_data: Request,
    service: OAuthService = Depends()
):
    """
    Introspect data
    """
    # print(dir(introspect_data))
    # print(introspect_data.__dict__)
    # print(introspect_data.headers)

    # request_body = await introspect_data.json()
    # token = request_body.get('token')

    token_bytes = await introspect_data.body()
    token_string = token_bytes.decode()
    token = token_string.split('=')[-1]

    return service.check_token(token)


"""
{
    "access_token": "KraHxV8vO4oI0nsfIR1Lzbe3TP8XBB",
    "expires_in": 36000,
    "token_type": "Bearer",
    "scope": "read write groups",
    "refresh_token": "f1UsFpkiTzNV8Cw98QwoIcXHFcEuw2"
}
"""