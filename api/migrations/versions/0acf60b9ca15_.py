"""empty message

Revision ID: 0acf60b9ca15
Revises: dcca1a87e8fd
Create Date: 2023-08-02 12:37:09.974511

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '0acf60b9ca15'
down_revision = 'dcca1a87e8fd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('player', sa.Column('active_game_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'player', 'game', ['active_game_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'player', type_='foreignkey')
    op.drop_column('player', 'active_game_id')
    # ### end Alembic commands ###
