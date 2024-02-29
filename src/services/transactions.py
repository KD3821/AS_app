from typing import List
from datetime import datetime

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

import tables
from models.transactions import TransactionCreate, TransactionUpdate, Kind
from database import get_session


class TransactionsService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def _get_account(self, user_email, account_number) -> tables.Account:
        account = (
            self.session
            .query(tables.Account)
            .filter_by(user_email=user_email)
            .filter_by(account_number=account_number)
            .first()
        )

        if not account:
            raise HTTPException(
                detail='No account found.',
                status_code=status.HTTP_404_NOT_FOUND
            )

        return account

    def _get_txn(self, txn_id, user_email) -> tables.Transaction:
        txn = (
            self.session
            .query(tables.Transaction)
            .filter_by(
                id=txn_id,
                user_email=user_email,
            )
            .first()
        )

        if not txn:
            raise HTTPException(
                detail='Transaction is not found.',
                status_code=status.HTTP_404_NOT_FOUND
            )

        return txn

    def validate_receiver(self, user_email: str, receiver_account: str) -> tables.Account:
        receiver = (
            self.session
            .query(tables.Account)
            .filter_by(user_email=user_email)
            .filter_by(account_number=receiver_account)
            .first()
        )

        if not receiver:
            raise HTTPException(
                detail="Wrong receiver's account.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return receiver

    def get_list(self, user_email: str, account_number: str, kind: Kind | None = None) -> List[tables.Transaction]:
        account = self._get_account(user_email, account_number)

        query = (
            self.session
            .query(tables.Transaction)
            .filter(tables.Transaction.user_email == user_email)
            .filter(or_(
                tables.Transaction.receiver_account == account.account_number,
                tables.Transaction.sender_account == account.account_number
            ))
        )

        if kind:
            query = query.filter_by(type=kind)

        transactions = query.all()

        return transactions

    def create(self, user_email: str, txn_data: TransactionCreate) -> tables.Transaction:
        sender_account = self._get_account(user_email, txn_data.sender_account)

        timestamp = datetime.utcnow()

        receiver_account = self.validate_receiver(user_email, txn_data.receiver_account)

        data = txn_data.model_dump()

        transaction = tables.Transaction(
            **data,
            user_email=user_email,
            type='transfer',
            date=timestamp
        )

        amount = data.get('amount')
        sender_account.balance -= amount
        sender_account.credit -= amount
        receiver_account.balance += amount
        receiver_account.debit += amount

        self.session.add(transaction)
        self.session.commit()

        return transaction

    def update(self, user_email: str, txn_id: int,  notice_data: TransactionUpdate) -> tables.Transaction:
        txn = self._get_txn(txn_id, user_email)

        txn.notice = notice_data.notice

        self.session.commit()

        return txn
