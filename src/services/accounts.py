from typing import List
from datetime import datetime
from decimal import Decimal

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

import tables
from database import get_session
from models.accounts import Country, AccountCreate, AccountUpdate


class AccountsService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def _get(self, user_id: int) -> tables.Account:
        account = (
            self.session
            .query(tables.Account)
            .filter_by(user_id=user_id)
            .first()
        )

        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return account

    def get_list(self, country: Country | None = None) -> List[tables.Account]:
        query = self.session.query(tables.Account)

        if country:
            query = query.filter_by(country=country)

        accounts = query.all()

        return accounts

    def get(self, user_id: int) -> tables.Account:
        return self._get(user_id)

    def create(self, user_id: int, account_data: AccountCreate) -> tables.Account:
        if self.session.query(tables.Account).filter_by(user_id=user_id).first():
            raise HTTPException(
                detail='Account already exists. Please close current account.',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        timestamp = datetime.utcnow()

        timestamp_str = str(timestamp.timestamp())

        account = tables.Account(
            **account_data.model_dump(),
            user_id=user_id,
            registered_at=timestamp,
            account_number=timestamp_str.split('.')[0],
            balance=Decimal('100000.00'),
            credit=Decimal('-100000.00')
        )

        self.session.add(account)
        self.session.commit()

        return account

    def update(self, user_id: int, account_data: AccountUpdate) -> tables.Account:
        account = self._get(user_id)

        for field, value in account_data:
            if value:
                setattr(account, field, value)

        self.session.commit()

        return account

    def delete(self, user_id: int) -> None:
        account = self._get(user_id)

        if account.credit + account.balance < 0:
            raise HTTPException(
                detail='Closing Account is not allowed due to account credit amount.',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        self.session.delete(account)
        self.session.commit()
