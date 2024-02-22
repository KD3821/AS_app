import random
import string
import pytz
from pydantic import ValidationError
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from fastapi import Depends, status, Response
from fastapi.exceptions import HTTPException

import tables
from settings import accounting_settings
from database import get_session
from models.auth import User, AccessToken, RefreshToken
from models.oauth2 import (
    OAuthClientCreate,
    OAuthClient,
    OAuthProvideResponse,
    OAuthRevokeRequest,
    IntrospectResponse,
    OAuthRefreshRequest,
    OAuthRefreshResponse,
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

    @classmethod
    def validate_user_token(cls, token: str) -> User:
        token_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
            headers={'WWW-Authenticate': 'Bearer'}
        )

        try:
            payload = jwt.decode(
                token,
                accounting_settings.jwt_secret,
                algorithms=[accounting_settings.jwt_algorithm]
            )
        except JWTError:
            raise token_exception

        # if payload.get('exp') < datetime.timestamp(datetime.utcnow()):  # added
        #     raise token_exception

        user_data = payload.get('user')

        try:
            user = User.model_validate(user_data)
        except ValidationError:
            raise token_exception

        return user

    @classmethod
    def create_token(cls, user: tables.User, client_id: str, token_type: str = 'access'):
        user_data = User.model_validate(user)

        now = datetime.utcnow()

        delta = 300 if token_type == 'refresh' else accounting_settings.jwt_expiration  # hardcode refresh 'exp' (5 min)

        payload = {
            'exp': now + timedelta(seconds=delta),
            'client_id': client_id,
            'user': user_data.model_dump()
        }

        if token_type == 'access':
            payload.update({'scope': 'read write introspection'})

        token = jwt.encode(
            payload,
            accounting_settings.jwt_secret,
            algorithm=accounting_settings.jwt_algorithm
        )

        if token_type == 'refresh':
            return RefreshToken(refresh=token, expire_date=payload.get('exp'))

        return AccessToken(access=token, expire_date=payload.get('exp'), scope=payload.get('scope'))

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

    def authenticate_client(self, client_id: str, secret_key: str) -> tables.OAuthClient:
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

    def refresh_token(self, token_data: OAuthRefreshRequest) -> OAuthRefreshResponse | dict:
        client = self.authenticate_client(
            client_id=token_data.client_id,
            secret_key=token_data.client_secret
        )

        token = token_data.token

        user = self.validate_user_token(token)

        refresh_token = (
            self.session
            .query(tables.OAuthToken)
            .filter(tables.OAuthToken.refresh == True)
            .filter(tables.OAuthToken.revoked == False)
            .filter(tables.OAuthToken.token == token_data.token)
            .filter(tables.OAuthToken.client_name == client.name)
            .first()
        )

        if refresh_token:
            access_token = self.create_token(user, client.client_id)
            response_data = {
                'access_token': access_token.access,
                'expires_in': accounting_settings.jwt_expiration,
                'token_type': 'Bearer',
                'scope': access_token.scope,
            }
            access_t = tables.OAuthToken(
                user_id=user.id,
                user_email=user.email,
                client_name=client.name,
                token=access_token.access,
                expire_date=access_token.expire_date,
                scope=access_token.scope
            )
            self.session.add(access_t)
            self.session.commit()
            return OAuthRefreshResponse(**response_data)

        return {"error": "invalid_grant"}

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
            unexpired_tokens = (
                self.session
                .query(tables.OAuthToken)
                .filter(tables.OAuthToken.client_name == client.name)
                .filter(tables.OAuthToken.expire_date >= now)
            )
            for token in unexpired_tokens:
                token.revoke_date = now
                token.revoked = True

            self.session.commit()
            return {"message": "token revoked"}

        return {"error": "invalid_grant"}

    def provide_oauth(self, data: dict) -> OAuthProvideResponse | dict:
        client = self.authenticate_client(
            client_id=data.get('client_id'),
            secret_key=data.get('secret_key')
        )

        user = self.authenticate_user(
            email=data.get('email'),
            password=data.get('password')
        )

        if user:
            access_token = self.create_token(user, client.client_id)
            refresh_token = self.create_token(user, client.client_id, 'refresh')

            response_data = {
                'access_token': access_token.access,
                'refresh_token': refresh_token.refresh,
                'expires_in': accounting_settings.jwt_expiration,
                'token_type': 'Bearer',
                'scope': access_token.scope,
            }
            access_t = tables.OAuthToken(
                user_id=user.id,
                user_email=user.email,
                client_name=client.name,
                token=access_token.access,
                expire_date=access_token.expire_date,
                scope=access_token.scope
            )
            refresh_t = tables.OAuthToken(
                user_id=user.id,
                user_email=user.email,
                client_name=client.name,
                token=refresh_token.refresh,
                expire_date=refresh_token.expire_date,
                refresh=True
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
            secret_key=new_secret_key  # later implement 'show once' logic and hash key before saving to DB
        )

        self.session.add(client)
        self.session.commit()

        return client

    def check_token(self, data: dict) -> IntrospectResponse | dict:
        client = self.authenticate_client(
            client_id=data.get('client_id'),
            secret_key=data.get('secret_key')
        )

        token = data.get('token')

        try:
            payload = jwt.decode(
                token,
                accounting_settings.jwt_secret,
                algorithms=[accounting_settings.jwt_algorithm]
            )
        except JWTError:
            print('jwt_error')  # need to revoke token
            return {"active": False, "revoke": True}

        user_dict = payload.get('user')

        token_exists = (
            self.session
            .query(tables.OAuthToken)
            .filter(tables.OAuthToken.user_email == user_dict.get('email'))
            .filter(tables.OAuthToken.client_name == client.name)
            .filter(tables.OAuthToken.expire_date > datetime.utcnow())
            .filter(tables.OAuthToken.token == token)
            .filter(tables.OAuthToken.revoked == False)
            .first()
        )

        if token_exists:
            exp = token_exists.expire_date
            service_timezone = pytz.timezone("Europe/Moscow")
            utc_exp = pytz.utc.localize(exp)
            local_exp = utc_exp.astimezone(service_timezone)

            data = {
                'client_id': client.client_id,
                'username': user_dict.get('email'),
                'scope': token_exists.scope,
                'exp': int(round(datetime.timestamp(local_exp))),
                'active': True,
                'refresh': token_exists.refresh
            }
            print(data)
            return IntrospectResponse(**data)

        print('not_active')
        return {"active": False}
