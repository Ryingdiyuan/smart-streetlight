from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ControlCommandCreate(BaseModel):
    command: str
    brightness: int | None = None


class BatchControlCommandCreate(ControlCommandCreate):
    device_ids: list[int] = Field(min_length=1)


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


class BatchControlLogItemRead(BaseModel):
    device_id: int
    device_code: str
    result: str
    log_id: int
    created_at: datetime


class BatchControlLogRead(BaseModel):
    command: str
    total: int
    success_count: int
    failed_count: int
    skipped_count: int
    results: list[BatchControlLogItemRead]
