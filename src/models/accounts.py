from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from decimal import Decimal


class Country(str, Enum):
    RU = 'RU'
    US = 'US'
    GB = 'GB'
    TR = 'TR'
    GE = 'GE'
    ES = 'ES'
    FR = 'FR'
    CN = 'CN'


class AccountBase(BaseModel):
    company: str
    city: str
    country: Country
    description: str


class Account(AccountBase):
    id: int
    account_number: str
    registered_at: datetime
    credit: Decimal
    balance: Decimal

    class Config:
        from_attributes = True


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    company: str | None = None
    city: str | None = None
    country: Country | None = None
    description: str | None = None


class AccountPublic(AccountBase):
    account_number: str
