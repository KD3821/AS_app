from pydantic import BaseModel
from enum import Enum
from decimal import Decimal
from datetime import datetime


class Kind(str, Enum):
    TRANSFER = 'transfer'
    DEPOSIT = 'deposit'
    WITHDRAW = 'withdraw'


class BaseTransaction(BaseModel):
    type: Kind
    amount: Decimal
    receiver_account: str
    notice: str


class Transaction(BaseTransaction):
    id: int
    user_id: int
    sender_account: str
    date: datetime


class TransactionCreate(BaseTransaction):
    receiver_account: str | None = None


class TransactionUpdate(BaseModel):
    notice: str | None = None
