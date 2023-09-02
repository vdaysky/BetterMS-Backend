from typing import Optional

from adapters.mojang import get_uuid
from constants import NameStatus
from models import Player, AuthSession, Role, Session
from sqlmodel import select, delete


async def login_user(username: str, password: str) -> Optional[AuthSession]:

    uuid = await get_uuid(username)

    player = select(Player).where(Player.uuid == uuid)
    player = Session().exec(player).first()

    if player is None:
        return None

    if player.password != password:
        return None


    # uuid = await get_uuid(username)
    #
    # user = Player.objects.get(uuid=uuid)
    #
    # if not check_password(password, user.password):
    #     return None

    return AuthSession.create(player)

codes = {}


async def register_user(username: str, code: int, password: str) -> AuthSession:
    user_uuid = await get_uuid(username)

    player = select(Player).where(Player.uuid == user_uuid)
    player = Session().exec(player).first()

    if player is None:
        raise ValueError("User not found")

    if player.is_verified():
        raise ValueError("User already verified")

    if player.verification_code != code:
        raise ValueError("Invalid Code")

    player.password = password
    player.verification_code = None
    Session().commit()

    return AuthSession.create(player)


async def get_name_status(name) -> NameStatus:
    uuid = await get_uuid(name)

    if uuid is None:
        return NameStatus.NAME_INVALID

    player = select(Player).where(Player.uuid == uuid)
    player = Session().exec(player).first()

    if player is not None and player.is_verified():
        return NameStatus.NAME_TAKEN

    return NameStatus.NAME_AVAILABLE


def get_player(session_id):
    session = AuthSession.objects.filter(session_key=session_id).first()

    if session is None:
        return None

    return session.player


def delete_session(session):
    stmt = delete(AuthSession).where(AuthSession.session_key == session.session_key)
    Session().exec(stmt)
    Session().commit()
