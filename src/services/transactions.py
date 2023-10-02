from typing import List
from datetime import datetime
from decimal import Decimal

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

import tables
from models.transactions import TransactionCreate, TransactionUpdate, Kind
from models.accounts import Account
from database import get_session


class TransactionsService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def _get_account(self, user_id) -> tables.Account:
        account = (
            self.session
            .query(tables.Account)
            .filter_by(user_id=user_id)
            .first()
        )

        if not account:
            raise HTTPException(
                detail='No account found.',
                status_code=status.HTTP_404_NOT_FOUND
            )

        return account

    def _get_txn(self, txn_id, user_id) -> tables.Transaction:
        txn = (
            self.session
            .query(tables.Transaction)
            .filter_by(
                id=txn_id,
                user_id=user_id,
            )
            .first()
        )

        if not txn:
            raise HTTPException(
                detail='Transaction is not found.',
                status_code=status.HTTP_404_NOT_FOUND
            )

        return txn

    def validate_receiver(self, receiver_account: str) -> tables.Account:
        receiver = (
            self.session
            .query(tables.Account)
            .filter_by(account_number=receiver_account)
            .first()
        )

        if not receiver:
            raise HTTPException(
                detail="No receiver's account found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return receiver

    @staticmethod
    def update_balance(amount: Decimal, sender: Account | None, receiver: Account | None) -> None:
        if sender and receiver:
            sender.balance -= amount
            receiver.balance += amount

        elif sender and not receiver:
            sender.balance -= amount

        else:
            receiver.balance += amount

    def get_list(self, user_id: int, kind: Kind | None = None) -> List[tables.Transaction]:
        account = self._get_account(user_id)

        query = (
            self.session
            .query(tables.Transaction)
            .filter(or_(
                tables.Transaction.receiver_account == account.account_number,
                tables.Transaction.sender_account == account.account_number
            ))
        )

        if kind:
            query = query.filter_by(type=kind)

        transactions = query.all()

        return transactions

    def create(self, user_id: int, txn_data: TransactionCreate) -> tables.Transaction:
        account = self._get_account(user_id)

        timestamp = datetime.utcnow()

        if txn_data.type == 'withdraw':
            receiver = None
            sender = account

        elif txn_data.type == 'deposit':
            receiver = account
            sender = None

        else:
            receiver = self.validate_receiver(txn_data.receiver_account)
            sender = account

        data = txn_data.model_dump()

        data.pop('receiver_account')

        transaction = tables.Transaction(
            **data,
            sender_account=sender.account_number if sender else 'CASH BOX',
            receiver_account=receiver.account_number if receiver else 'CASH BOX',
            user_id=user_id,
            date=timestamp
        )

        self.update_balance(
            amount=data.get('amount'),
            sender=sender,
            receiver=receiver
        )

        self.session.add(transaction)
        self.session.commit()

        return transaction

    def update(self, user_id: int, txn_id: int,  notice_data: TransactionUpdate) -> tables.Transaction:
        txn = self._get_txn(txn_id, user_id)

        txn.notice = notice_data.notice

        self.session.commit()

        return txn
