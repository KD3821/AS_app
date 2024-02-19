import random
import string
from datetime import datetime
from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from fastapi import Depends, status
from fastapi.exceptions import HTTPException

import tables
from settings import accounting_settings
from database import get_session
from models.auth import User
from .auth import AuthService
from models.oauth2 import (
    OAuthClientCreate,
    OAuthClient,
    OAuthProvideResponse,
    OAuthRevokeRequest,
    IntrospectRequest,
    IntrospectResponse,
)


class OAuthService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        return bcrypt.verify(password, hashed_password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        return bcrypt.hash(password)

    def remind_creds(self, name: str, password: str) -> OAuthClient:
        authentication_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid client credentials',
            headers={'WWW-Authenticate': 'Bearer'}
        )

        client = (
            self.session
            .query(tables.OAuthClient)
            .filter(tables.OAuthClient.name == name)
            .first()
        )

        if not client:
            raise authentication_exception

        if not self.verify_password(password, client.hashed_password):
            raise authentication_exception

        return client

    def authenticate_client(self, client_id: str, secret_key: str) -> OAuthClient:
        authentication_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid client credentials',
            headers={'WWW-Authenticate': 'Bearer'}
        )

        client = (
            self.session
            .query(tables.OAuthClient)
            .filter(tables.OAuthClient.client_id == client_id)
            .first()
        )

        if not client:
            raise authentication_exception

        if client.secret_key != secret_key:
            raise authentication_exception

        return client

    def authenticate_user(self, email: str, password: str) -> User:
        authentication_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid email or password',
            headers={'WWW-Authenticate': 'Bearer'}
        )

        user = (
            self.session
            .query(tables.User)
            .filter(tables.User.email == email)
            .first()
        )

        if not user:
            raise authentication_exception

        if not self.verify_password(password, user.hashed_password):
            raise authentication_exception

        return user

    def revoke_token(self, token_data: OAuthRevokeRequest) -> dict:
        client = self.authenticate_client(
            client_id=token_data.client_id,
            secret_key=token_data.client_secret
        )
        token_exists = (
            self.session
            .query(tables.OAuthToken)
            .filter(tables.OAuthToken.token == token_data.token)
            .filter(tables.OAuthToken.client_name == client.name)
            .first()
        )
        if token_exists:
            now = datetime.utcnow()
            token_exists.expire_date = now
            token_exists.revoke_date = now
            token_exists.revoked = True

            self.session.commit()
            return {"message": "token revoked"}

        return {"error": "invalid_grant"}

    def provide_oauth(self, data: dict, user_service: AuthService) -> OAuthProvideResponse | dict:
        user = None
        client = self.authenticate_client(
            client_id=data.get('client_id'),
            secret_key=data.get('secret_key')
        )

        grant_type = data.get('grant_type')

        if grant_type == 'password':
            user = self.authenticate_user(
                email=data.get('email'),
                password=data.get('password')
            )

        elif grant_type == 'refresh_token':
            user = user_service.validate_token(data.get('refresh_token'))

        if user:
            access_token = user_service.create_token(user)
            refresh_token = user_service.create_token(user, 'refresh')

            response_data = {
                'access_token': access_token.access,
                'refresh_token': refresh_token.refresh,
                'expires_in': accounting_settings.jwt_expiration,
                'token_type': 'Bearer',
                'scope': 'read write groups',
            }
            access_t = tables.OAuthToken(
                user_id=user.id,
                client_name=client.name,
                token=access_token.access,
                expire_date=access_token.expire_date
            )
            refresh_t = tables.OAuthToken(
                user_id=user.id,
                client_name=client.name,
                refresh=True,
                token=refresh_token.refresh,
                expire_date=refresh_token.expire_date
            )

            self.session.add_all([access_t, refresh_t])
            self.session.commit()

            return OAuthProvideResponse(**response_data)
        return {"error": "invalid_grant"}

    def register_client(self, client_data: OAuthClientCreate) -> OAuthClient:
        client_exists = (
            self.session
            .query(tables.OAuthClient)
            .filter(tables.OAuthClient.name == client_data.name)
            .first()
        )

        if client_exists:
            raise HTTPException(
                detail='OAuthClient with such name already exists.',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        new_client_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))

        client_id_exists = True
        while client_id_exists:
            client_id_exists = False
            client_same_id = (
                self.session
                .query(tables.OAuthClient)
                .filter(tables.OAuthClient.client_id == new_client_id)
                .first()
            )
            if client_same_id:
                client_id_exists = True

        tmp_secret_key = self.hash_password(client_data.password + new_client_id + client_data.name)
        new_secret_key = tmp_secret_key[-10:] + new_client_id[::2]

        client = tables.OAuthClient(
            name=client_data.name,
            hashed_password=self.hash_password(client_data.password),
            client_id=new_client_id,
            secret_key=new_secret_key
        )

        self.session.add(client)
        self.session.commit()

        return client

    def check_token(self, introspect_data: IntrospectRequest, user_service: AuthService) -> IntrospectResponse | dict:
        client = self.authenticate_client(
            client_id=introspect_data.client_id,
            secret_key=introspect_data.client_secret
        )
        token_exists = (
            self.session
            .query(tables.OAuthToken)
            .filter(tables.OAuthToken.token == introspect_data.token)
            .filter(tables.OAuthToken.client_name == client.name)
            .first()
        )
        if token_exists:
            user = user_service.validate_token(token_exists.token)
            data = {
                'id': user.id,
                'email': user.email,
                'exp': token_exists.expire_date
            }
            return IntrospectResponse(**data)

        return {"error": "invalid_grant"}
