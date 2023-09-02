from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from constants import LocationCode


class PlayerCreate(BaseModel):
    uuid: UUID
    location_code: LocationCode


class VerifyPlayer(BaseModel):
    verification_code: int = Field(ge=100_000, le=999_999)


class SendInviteData(BaseModel):
    player_id: int
