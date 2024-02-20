import sqlalchemy as sa
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)
    email = sa.Column(sa.String, unique=True)
    is_admin = sa.Column(sa.Boolean, default=False)
    hashed_password = sa.Column(sa.String)


class Account(Base):
    __tablename__ = 'accounts'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    account_number = sa.Column(sa.String, unique=True)
    company = sa.Column(sa.String)
    city = sa.Column(sa.String)
    country = sa.Column(sa.String)
    description = sa.Column(sa.Text, nullable=True)
    registered_at = sa.Column(sa.DateTime)
    credit = sa.Column(sa.Numeric(10, 2))
    balance = sa.Column(sa.Numeric(10, 2))


class Transaction(Base):
    __tablename__ = 'transactions'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    sender_account = sa.Column(sa.String)
    receiver_account = sa.Column(sa.String)
    date = sa.Column(sa.DateTime)
    type = sa.Column(sa.String)
    amount = sa.Column(sa.Numeric(8, 2))
    notice = sa.Column(sa.String, nullable=True)


class OAuthClient(Base):
    __tablename__ = 'clients'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, unique=True)
    hashed_password = sa.Column(sa.String)
    client_id = sa.Column(sa.String, unique=True)
    secret_key = sa.Column(sa.String)


class OAuthToken(Base):
    __tablename__ = 'tokens'
    id = sa.Column(sa.Integer, primary_key=True)
    refresh = sa.Column(sa.Boolean, default=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    user_email = sa.Column(sa.String, sa.ForeignKey('users.email'))
    client_name = sa.Column(sa.String, sa.ForeignKey('clients.name'))
    scope = sa.Column(sa.String, nullable=True)
    token = sa.Column(sa.String)
    expire_date = sa.Column(sa.DateTime)
    revoke_date = sa.Column(sa.DateTime, nullable=True)
    revoked = sa.Column(sa.Boolean, default=False)
