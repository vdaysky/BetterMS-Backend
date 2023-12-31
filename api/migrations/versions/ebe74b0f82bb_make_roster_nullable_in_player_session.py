"""Make roster nullable in player session

Revision ID: ebe74b0f82bb
Revises: c4e19d057f07
Create Date: 2023-06-11 11:14:34.817093

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'ebe74b0f82bb'
down_revision = 'c4e19d057f07'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('playersession', 'roster_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('playersession', 'roster_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
