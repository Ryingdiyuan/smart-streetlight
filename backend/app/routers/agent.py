from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_user_or_above
from app.models.chat_message import ChatMessage
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentRelatedDevice,
    ChatHistoryResponse,
    ChatMessageResponse,
)
from app.services.agent_context import AgentContextError, build_agent_context
from app.services.llm_client import generate_agent_answer

router = APIRouter(prefix="/agent", tags=["agent"])

MAX_HISTORY = 100


@router.post("/chat", response_model=AgentChatResponse)
def chat_with_agent(
    request: AgentChatRequest,
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_user_or_above),
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

    # Save user question
    user_message = ChatMessage(
        user_id=_current_user.id,
        role="user",
        content=question,
        device_id=request.device_id,
        device_code=request.device_code,
    )
    db.add(user_message)

    answer, source = generate_agent_answer(question, context)

    # Save assistant answer
    assistant_message = ChatMessage(
        user_id=_current_user.id,
        role="assistant",
        content=answer,
        device_id=request.device_id,
        device_code=request.device_code,
    )
    db.add(assistant_message)
    db.commit()

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


@router.get("/history", response_model=ChatHistoryResponse)
def get_chat_history(
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_user_or_above),
) -> ChatHistoryResponse:
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == _current_user.id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .limit(MAX_HISTORY)
        .all()
    )
    return ChatHistoryResponse(
        messages=[ChatMessageResponse.model_validate(msg) for msg in messages],
        total=len(messages),
    )


@router.delete("/history")
def clear_chat_history(
    db: Session = Depends(get_db),
    _current_user: object = Depends(require_user_or_above),
) -> dict[str, bool]:
    db.query(ChatMessage).filter(ChatMessage.user_id == _current_user.id).delete()
    db.commit()
    return {"ok": True}
