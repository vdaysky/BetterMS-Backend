from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    message: str
    payload: Optional[Dict] = None


class ObjectId(BaseModel):
    obj_id: int | None
    entity: str
    dependencies: list[ObjectId] = []
