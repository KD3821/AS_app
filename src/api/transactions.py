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


@router.get('/', response_model=List[Transaction])
def get_transactions(
    user: CurrentUser,
    kind: Kind | None = None,
    service: TransactionsService = Depends()
):
    """
    Get list of Business Account's Transactions (Auth required)
    - **kind**: Filter common by type - ('transfer', 'withdraw', 'deposit') - Optionally.
    """
    return service.get_list(user_id=user.id, kind=kind)


@router.post('/', response_model=Transaction)
def create_transaction(
    user: CurrentUser,
    txn_data: TransactionCreate,
    service: TransactionsService = Depends()
):
    """
    Create a Transaction (Auth required) - Please use Business Partner's account_number to make money transfer.
    - **type**: please use one of the list: 'transfer', 'withdraw', 'deposit'
    - **receiver_account**: only required for creating 'transfer' type of Transactions. Other types assume transactions
                            between Business Account and 'CASH BOX'.
    """
    return service.create(user_id=user.id, txn_data=txn_data)


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
        user_id=user.id,
        txn_id=transaction_id,
        notice_data=notice_data
    )
