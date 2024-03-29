"""Create OAuthToken model

Revision ID: a1b1c84aed19
Revises: b1928e574f1a
Create Date: 2024-02-19 02:12:40.546422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b1c84aed19'
down_revision: Union[str, None] = 'b1928e574f1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('refresh', sa.Boolean(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('client_name', sa.String(), nullable=True),
    sa.Column('token', sa.String(), nullable=True),
    sa.Column('expire_date', sa.DateTime(), nullable=True),
    sa.Column('revoke_date', sa.DateTime(), nullable=True),
    sa.Column('revoked', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['client_name'], ['clients.name'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tokens')
    # ### end Alembic commands ###
