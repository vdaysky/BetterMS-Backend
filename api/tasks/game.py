from sqlalchemy import func
from sqlmodel import select

from api.constants import AVAILABLE_PUBS_THRESHOLD
from api.models import Game, GraphQLSession
from api.services.game import create_pub, create_deathmatch, create_duels, create_game


async def keep_open_pubs():
    """ Make sure there are always some open pubs. """

    stmt = select(func.count(Game.id)).where(Game.mode == Game.Mode.PUB, Game.status == Game.Status.NOT_STARTED)
    open_pubs = GraphQLSession().exec(stmt).one()

    for _ in range(AVAILABLE_PUBS_THRESHOLD - open_pubs):
        # create new game
        await create_game(None, Game.Mode.PUB)


async def keep_open_deathmatch():
    """ Make sure there are always some open deathmatch. """

    stmt = select(func.count(Game.id)).where(Game.mode == Game.Mode.DEATHMATCH,
                                             Game.status == Game.Status.NOT_STARTED)
    open_deathmatch = GraphQLSession().exec(stmt).one()

    for _ in range(AVAILABLE_PUBS_THRESHOLD - open_deathmatch):
        # create new game
        await create_game(None, Game.Mode.DEATHMATCH)


async def keep_open_duels():
    """ Make sure there are always some open duels. """

    stmt = select(func.count(Game.id)).where(Game.mode == Game.Mode.DUELS,
                                             Game.status == Game.Status.NOT_STARTED)
    open_duels = GraphQLSession().exec(stmt).one()

    for _ in range(AVAILABLE_PUBS_THRESHOLD - open_duels):
        # create new game
        await create_game(None, Game.Mode.DUEL)
