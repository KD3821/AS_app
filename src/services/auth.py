from pydantic import ValidationError
from jose import jwt, JWTError
from passlib.hash import bcrypt
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_session
from models.auth import User, AccessToken, RefreshToken, UserCreate
from settings import accounting_settings
import tables


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    return AuthService.validate_token(token)


class AuthService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        return bcrypt.verify(password, hashed_password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        return bcrypt.hash(password)

    @classmethod
    def validate_token(cls, token: str) -> User:
        credential_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid credentials',
            headers={'WWW-Authenticate': 'Bearer'}
        )

        try:
            payload = jwt.decode(
                token,
                accounting_settings.jwt_secret,
                algorithms=[accounting_settings.jwt_algorithm]
            )
        except JWTError:
            raise credential_exception

        if payload.get('exp') < datetime.timestamp(datetime.utcnow()):  # added
            raise credential_exception

        user_data = payload.get('user')

        try:
            user = User.model_validate(user_data)
        except ValidationError:
            raise credential_exception

        return user

    @classmethod
    def create_token(cls, user: tables.User, token_type: str = 'access', delta: int = accounting_settings.jwt_expiration):
        user_data = User.model_validate(user)

        now = datetime.utcnow()

        if token_type == 'refresh':  # hardcode expire_date for refresh token (5 min)
            delta = 300

        payload = {
            'iat': now,
            'nbf': now,
            'exp': now + (delta * timedelta(seconds=1)),
            'sub': str(user_data.id),
            'user': user_data.model_dump()
        }

        token = jwt.encode(
            payload,
            accounting_settings.jwt_secret,
            algorithm=accounting_settings.jwt_algorithm
        )

        if token_type == 'refresh':
            return RefreshToken(refresh=token, expire_date=payload.get('exp'))
        return AccessToken(access=token, expire_date=payload.get('exp'))

    def register_user(self, user_data: UserCreate) -> AccessToken:
        if user_data.is_admin:
            admin_user = (
                self.session
                .query(tables.User)
                .filter(tables.User.is_admin is True)
                .first()
            )

            if admin_user:
                raise HTTPException(
                    detail='AdminUser already exists.',
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        user = (
            self.session
            .query(tables.User)
            .filter(tables.User.email == user_data.email)
            .first()
        )

        if user:
            raise HTTPException(
                detail='User with such Email is already registered. Do you want to reset password?',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user = tables.User(
            email=user_data.email,
            is_admin=user_data.is_admin,
            hashed_password=self.hash_password(user_data.password)
        )

        self.session.add(user)
        self.session.commit()

        return self.create_token(user)

    def authenticate_user(self, email: str, password: str) -> AccessToken:
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

        return self.create_token(user)
