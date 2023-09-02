from datetime import datetime

from schemas.common import ObjectId
from pydantic.class_validators import validator
from pydantic.main import BaseModel


class CreateMatch(BaseModel):
    event: ObjectId
    start_date: datetime
    name: str
    team_a: ObjectId
    team_b: ObjectId
    map_count: int

    @validator('map_count')
    def validate_map_count(cls, v):
        assert v in [1, 3, 5], 'Invalid map count'
        return v


class PickMap(BaseModel):
    map: ObjectId
