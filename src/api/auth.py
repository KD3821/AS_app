from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from models.auth import UserCreate, AccessToken, User
from services.auth import AuthService, get_current_user

router = APIRouter(
    prefix='/auth',
    tags=['Sign In - Sign Up']
)

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post('/register', response_model=AccessToken)
def register(
    user_data: UserCreate,
    service: AuthService = Depends()
):
    """
    Register User of Accounting Service. Setting admin:"true" makes money on admin's account available for loans! (JOKE)
    | Admin funcs not implemented - to be continued...
    """
    return service.register_user(user_data)


@router.post('/login', response_model=AccessToken)
def login(
    auth_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends()
):
    """
    Please use EMAIL as username to login via OAuthForm
    """
    email = auth_data.username

    return service.authenticate_user(email, auth_data.password)


@router.get('/info', response_model=User)
def retrieve_user(user: CurrentUser):
    """
    Get info about own account (Auth required)
    """
    return user
