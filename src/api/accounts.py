from typing import List, Annotated

from fastapi import APIRouter, Depends, Response, status

from models.accounts import Account, AccountCreate, Country, AccountUpdate, AccountPublic
from services.accounts import AccountsService
from models.auth import User
from services.auth import get_current_user


router = APIRouter(
    prefix='/accounts',
    tags=['Business Accounts']
)

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get('/', response_model=List[AccountPublic])
def get_accounts(
    user: CurrentUser,
    country: Country | None = None,
    service: AccountsService = Depends()
):
    """
    Get list of all Accounts registered in 'Accounting Service' (Auth required).

    - **country**: Filter Accounts by country - ('RU', 'US', 'GB', 'TR', 'GE', 'ES', 'FR', 'CN') - Optionally.
    """
    return service.get_list(country=country)


@router.get('/info', response_model=Account)
def get_account(
    user: CurrentUser,
    service: AccountsService = Depends()
):
    """
    Get info about User's account (Auth required)
    """
    return service.get(user_id=user.id)


@router.post('/', response_model=Account)
def create_account(
    user: CurrentUser,
    account_data: AccountCreate,
    service: AccountsService = Depends()
):
    """
    Register Business Account (Auth required)
    """
    return service.create(user_id=user.id, account_data=account_data)


@router.patch('/info', response_model=Account)
def update_account(
    user: CurrentUser,
    account_data: AccountUpdate | None,
    service: AccountsService = Depends()
):
    """
    Update info about Business Account (Auth required)
    """
    return service.update(user_id=user.id, account_data=account_data)


@router.delete('/info')
def delete_account(
    user: CurrentUser,
    service: AccountsService = Depends()
):
    """
    Delete Business Account (Auth required)
    """
    service.delete(user_id=user.id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
