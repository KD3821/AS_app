from enum import Enum
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel


class Kind(str, Enum):
    TRANSFER = 'transfer'
    DEPOSIT = 'deposit'
    WITHDRAW = 'withdraw'


class BaseTransaction(BaseModel):
    amount: Decimal
    receiver_account: str
    notice: str


class Transaction(BaseTransaction):
    id: int
    user_email: str
    sender_account: str
    date: datetime


class TransactionCreate(BaseTransaction):
    sender_account: str


class TransactionUpdate(BaseModel):
    notice: str | None = None


class TransactionAutoCreate(TransactionCreate):
    type: Kind
