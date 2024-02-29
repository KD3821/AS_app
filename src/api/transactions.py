from typing import List, Annotated

from fastapi import APIRouter, Depends

from models.transactions import Transaction, TransactionCreate, TransactionUpdate, Kind
from services.transactions import TransactionsService
from models.auth import User
from services.auth import get_current_user


router = APIRouter(
    prefix='/transactions',
    tags=['Transactions']
)

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get('/{account_number}', response_model=List[Transaction])
def get_transactions(
    user: CurrentUser,
    account_number: str,
    kind: Kind | None = None,
    service: TransactionsService = Depends()
):
    """
    Get list of Account's Transactions (Auth required)
    - **kind**: Filter common by type - ('transfer', 'withdraw', 'deposit') - Optionally.
    """
    return service.get_list(user_email=user.email, account_number=account_number, kind=kind)


@router.post('/', response_model=Transaction)
def create_transfer_transaction(
    user: CurrentUser,
    txn_data: TransactionCreate,
    service: TransactionsService = Depends()
):
    """
    Create a Transaction (Auth required). User can transfer between own accounts - from account at one client (service)
    to own account at another client (Deposit txns work from PaaS only). Deleting account at one of the clients will be
    followed by transferring the money left to User's wallet account. Client can transfer from wallet to Users account
    - **type**: use one of the list: 'transfer' (between user's accounts), 'deposit' (from wallet to account), but
    'withdraw' (from account to wallet) will only perform in background as a result of deleting account by User,
    """
    return service.create(user_email=user.email, txn_data=txn_data)


@router.patch('/{transaction_id}', response_model=Transaction)
def update_transaction(
    user: CurrentUser,
    transaction_id: int,
    notice_data: TransactionUpdate,
    service: TransactionsService = Depends()
):
    """
    Update Transaction's notice field (Auth required)
    """
    return service.update(
        user_email=user.email,
        txn_id=transaction_id,
        notice_data=notice_data
    )
