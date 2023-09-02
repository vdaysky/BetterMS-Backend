from pydantic.main import BaseModel

from constants import LocationCode


class CreateTeam(BaseModel):
    short_name: str
    name: str
    location: LocationCode
