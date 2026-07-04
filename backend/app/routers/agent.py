from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.agent import AgentChatRequest, AgentChatResponse, AgentRelatedDevice
from app.services.agent_context import AgentContextError, build_agent_context
from app.services.llm_client import generate_agent_answer

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
def chat_with_agent(
    request: AgentChatRequest,
    db: Session = Depends(get_db),
) -> AgentChatResponse:
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="question 不能为空",
        )
    if len(question) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="question 不能超过 500 字",
        )

    try:
        context = build_agent_context(
            db,
            device_id=request.device_id,
            device_code=request.device_code,
        )
    except AgentContextError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    answer, source = generate_agent_answer(question, context)
    related_device = None
    if context["scope"] == "device":
        device = context["device"]
        related_device = AgentRelatedDevice(
            id=device["id"],
            device_code=device["device_code"],
            device_name=device["device_name"],
        )

    return AgentChatResponse(
        answer=answer,
        source=source,
        related_device=related_device,
        context_summary=context["summary"],
    )
