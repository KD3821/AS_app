"""Create Service, Operation, upgrade Account models

Revision ID: 1fce0e688189
Revises: f2152ad5afe5
Create Date: 2024-02-28 21:08:38.977564

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1fce0e688189'
down_revision: Union[str, None] = 'f2152ad5afe5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('services',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('is_reccurent', sa.Boolean(), nullable=True),
    sa.Column('recurring_interval', sa.Integer(), nullable=True),
    sa.Column('fee', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('operations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('account_number', sa.String(), nullable=True),
    sa.Column('service_id', sa.Integer(), nullable=True),
    sa.Column('service_name', sa.String(), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.Column('remaining_balance', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.ForeignKeyConstraint(['account_number'], ['accounts.account_number'], ),
    sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_email', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('client_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('client_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('debit', sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.drop_constraint('accounts_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'clients', ['client_id'], ['client_id'])
        batch_op.create_foreign_key(None, 'users', ['user_email'], ['email'])
        batch_op.drop_column('description')
        batch_op.drop_column('user_id')
        batch_op.drop_column('city')
        batch_op.drop_column('country')
        batch_op.drop_column('company')

    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_email', sa.String(), nullable=True))
        batch_op.drop_constraint('transactions_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_email'], ['email'])
        batch_op.drop_column('user_id')

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('transactions_user_id_fkey', 'users', ['user_id'], ['id'])
        batch_op.drop_column('user_email')

    with op.batch_alter_table('accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('company', sa.VARCHAR(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('country', sa.VARCHAR(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('city', sa.VARCHAR(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('accounts_user_id_fkey', 'users', ['user_id'], ['id'])
        batch_op.drop_column('debit')
        batch_op.drop_column('client_name')
        batch_op.drop_column('client_id')
        batch_op.drop_column('user_email')

    op.drop_table('operations')
    op.drop_table('services')
    # ### end Alembic commands ###
