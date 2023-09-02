from fastapi import APIRouter

from models import Game, Session
from services.ranked import compute_elo

from sqlmodel import select
router = APIRouter()


@router.get("/predict/{game_id}")
async def get_elo(game_id: int):

    stmt = select(Game).where(Game.id == game_id)
    game = Session().exec(stmt).first()

    a_win, a_loose = compute_elo(game.team_a, game.team_b)
    b_win, b_loose = compute_elo(game.team_b, game.team_a)

    return {
        "team_a_win": a_win,
        "team_a_loss": a_loose,
        "team_b_win": b_win,
        "team_b_loss": b_loose,
    }
