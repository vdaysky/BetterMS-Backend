"""empty message

Revision ID: da203fb2b748
Revises: 2c203c71192b
Create Date: 2023-05-17 21:12:03.704007

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'da203fb2b748'
down_revision = '2c203c71192b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('blacklisted_player', sa.Column('game_id', sa.Integer(), nullable=False))
    op.drop_constraint('blacklisted_player_map_id_fkey', 'blacklisted_player', type_='foreignkey')
    op.create_foreign_key(None, 'blacklisted_player', 'game', ['game_id'], ['id'])
    op.drop_column('blacklisted_player', 'map_id')
    op.add_column('player_permissions', sa.Column('role_id', sa.Integer(), nullable=False))
    op.drop_constraint('player_permissions_player_id_fkey', 'player_permissions', type_='foreignkey')
    op.create_foreign_key(None, 'player_permissions', 'role', ['role_id'], ['id'])
    op.drop_column('player_permissions', 'player_id')
    op.add_column('whitelisted_player', sa.Column('game_id', sa.Integer(), nullable=False))
    op.drop_constraint('whitelisted_player_map_id_fkey', 'whitelisted_player', type_='foreignkey')
    op.create_foreign_key(None, 'whitelisted_player', 'game', ['game_id'], ['id'])
    op.drop_column('whitelisted_player', 'map_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('whitelisted_player', sa.Column('map_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'whitelisted_player', type_='foreignkey')
    op.create_foreign_key('whitelisted_player_map_id_fkey', 'whitelisted_player', 'map', ['map_id'], ['id'])
    op.drop_column('whitelisted_player', 'game_id')
    op.add_column('player_permissions', sa.Column('player_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'player_permissions', type_='foreignkey')
    op.create_foreign_key('player_permissions_player_id_fkey', 'player_permissions', 'player', ['player_id'], ['id'])
    op.drop_column('player_permissions', 'role_id')
    op.add_column('blacklisted_player', sa.Column('map_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'blacklisted_player', type_='foreignkey')
    op.create_foreign_key('blacklisted_player_map_id_fkey', 'blacklisted_player', 'map', ['map_id'], ['id'])
    op.drop_column('blacklisted_player', 'game_id')
    # ### end Alembic commands ###