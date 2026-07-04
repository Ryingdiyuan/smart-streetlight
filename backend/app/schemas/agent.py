from typing import Any

from pydantic import BaseModel, ConfigDict


class AgentChatRequest(BaseModel):
    question: str
    device_id: int | None = None
    device_code: str | None = None


class AgentRelatedDevice(BaseModel):
    id: int
    device_code: str
    device_name: str

    model_config = ConfigDict(from_attributes=True)


class AgentChatResponse(BaseModel):
    answer: str
    source: str
    related_device: AgentRelatedDevice | None = None
    context_summary: dict[str, Any]
