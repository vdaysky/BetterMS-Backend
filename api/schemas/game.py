from enum import Enum

from schemas.common import ObjectId
from pydantic.main import BaseModel


class CreateGame(BaseModel):
    match: ObjectId
    map: ObjectId


class JoinGame(BaseModel):
    game: ObjectId


class GamePlugin(str, Enum):
    DefusalPlugin = "DefusalPlugin"
    DeathmatchPlugin = "DeathmatchPlugin"
    DuelPlugin = "DuelPlugin"
    RankedPlugin = "RankedPlugin"
    WarmUpPlugin = "WarmUpPlugin"
    TargetPracticePlugin = "TargetPracticePlugin"
    WhitelistPlugin = "WhitelistPlugin"
    CompetitivePlugin = "CompetitivePlugin"
    GunGamePlugin = "GunGamePlugin"
