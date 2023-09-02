from schemas.common import ObjectId
from pydantic import BaseModel


class Queue(BaseModel):
    queue: ObjectId


class PickPlayer(BaseModel):
    queue: ObjectId
    player: ObjectId

