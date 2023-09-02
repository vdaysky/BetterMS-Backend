from fastapi import APIRouter

from exceptions import BadRequestError
from schemas.auth import LoginCredentials, UserCreate, AuthResponse
from dependencies import PlayerAuthDependency, SessionDependency
from models import Player, AuthSession
from services import auth
from services.auth import login_user, register_user, get_name_status
from exceptions import AuthorizationError
router = APIRouter()


@router.get('/me')
async def get_me(player: Player = PlayerAuthDependency):
    return {
        "player_id": player.id
    }


@router.post('/logout')
async def logout(session: AuthSession = SessionDependency):
    auth.delete_session(session)
    return None


@router.post('/login', response_model=AuthResponse)
async def login(credentials: LoginCredentials):

    session = await login_user(credentials.username, credentials.password)

    if session is None:
        raise AuthorizationError

    return {
        'session_key': session.session_key,
        "player_id": session.player.id
    }


@router.post('/register', response_model=AuthResponse)
async def register(data: UserCreate):

    try:
        session = await register_user(data.username, data.verification_code, data.password)
    except ValueError as e:
        raise BadRequestError(str(e))

    return {
        'session_key': session.session_key,
        "player_id": session.player.id
    }


@router.get('/name/status')
async def fetch_name_status(name: str):
    status = await get_name_status(name)
    return {'status': status}

