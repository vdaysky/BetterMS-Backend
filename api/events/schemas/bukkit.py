from enum import Enum, IntEnum
from typing import Optional


from pydantic import BaseModel

from schemas.common import ObjectId


class IntentEvent(BaseModel):
    pass


class ServerStartEvent(BaseModel):
    pass


class PlayerGenerateCodeIntent(BaseModel):
    player: ObjectId


class CreateGameIntentEvent(IntentEvent):
    mapName: str | None
    mode: str
    player: ObjectId | None


class ChangePlayerWhitelistStatusAtGameIntent(IntentEvent):
    player: ObjectId
    game: ObjectId
    isWhitelisted: bool
    manager: ObjectId


class ChangePlayerBlacklistStatusAtGameIntent(IntentEvent):
    player: ObjectId
    game: ObjectId
    isBlacklisted: bool
    manager: ObjectId
    reason: str | None


class PlayerLeaveGameIntentEvent(IntentEvent):
    game: ObjectId
    player: ObjectId


class GameDeleteIntentEvent(IntentEvent):
    game: ObjectId


class PlayerJoinGameIntentEvent(IntentEvent):
    game: ObjectId
    player: ObjectId
    team: str | None  # T / CT
    spectate: bool


class PlayerLeaveGameEvent(BaseModel):
    game: ObjectId
    player: ObjectId


class GameTerminatedEvent(BaseModel):
    game: ObjectId


class PlayerTeamChangeIntentEvent(IntentEvent):
    game: ObjectId
    player: ObjectId
    team: str


class PreGameEndEvent(BaseModel):
    game: ObjectId
    winner: Optional[ObjectId]
    looser: Optional[ObjectId]


class GameStartedEvent(BaseModel):
    game: ObjectId


class PlayerJoinServerEvent(BaseModel):
    player: ObjectId


class PlayerLeaveServerEvent(BaseModel):
    player: ObjectId


class PlayerDeathEvent(BaseModel):
    damagee: ObjectId
    damager: Optional[ObjectId]
    game: ObjectId
    damageSource: str
    modifiers: dict
    reason: str
    round: int


class RoundWinReason(IntEnum):
    TIME_RUN_OUT = 0
    OBJECTIVE = 1
    ELIMINATION = 2


class WinReason(str, Enum):
    TIME_RUN_OUT = "TIME_RUN_OUT"
    OBJECTIVE = "OBJECTIVE"
    ELIMINATION = "ELIMINATION"


class RoundWinEvent(BaseModel):

    game: ObjectId
    winner: Optional[ObjectId]
    looser: Optional[ObjectId]
    roundNumber: int
    reason: WinReason


class PlayerGameConnectEvent(BaseModel):
    player_id: ObjectId
    game_id: ObjectId
    team_id: ObjectId | None
    status: int


