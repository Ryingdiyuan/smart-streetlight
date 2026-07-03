from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ControlCommandCreate(BaseModel):
    command: str
    brightness: int | None = None


class ControlLogRead(BaseModel):
    id: int
    device_id: int
    command: str
    source: str
    result: str
    request_payload: dict[str, Any] | None = None
    reply_payload: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
