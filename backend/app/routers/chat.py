import json
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import (
    SessionCreate, SessionUpdate, SessionResponse,
    MessageRequest, ChatHistoryResponse, MessageResponse,
)
from app.services.chat_service import ChatService
from app.services.rag_service import rag_service
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1", tags=["聊天"])


# ===== 会话管理 =====

@router.get("/sessions", summary="获取会话列表")
def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ChatService.list_sessions(db, current_user.id, page, page_size)


@router.post("/sessions", response_model=SessionResponse, summary="创建会话")
def create_session(
    req: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = ChatService.create_session(db, current_user.id, req.title)
    return SessionResponse.model_validate(session)


@router.put("/sessions/{session_id}", response_model=SessionResponse, summary="更新会话")
def update_session(
    session_id: int,
    req: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = ChatService.update_session(
        db, session_id, current_user.id,
        title=req.title, status=req.status,
    )
    return SessionResponse.model_validate(session)


@router.delete("/sessions/{session_id}", summary="删除会话")
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ChatService.delete_session(db, session_id, current_user.id)
    return {"message": "会话已删除"}


# ===== 消息管理 =====

@router.get("/sessions/{session_id}/messages", summary="获取消息历史")
def get_messages(
    session_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ChatService.get_messages(db, session_id, current_user.id, page, page_size)


@router.post("/sessions/{session_id}/messages", summary="发送消息（SSE 流式返回）")
async def send_message(
    session_id: int,
    req: MessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发送消息并通过 SSE 流式返回 AI 回答"""

    async def event_generator():
        async for event in rag_service.generate_answer(
            db, session_id, req.content, current_user.id
        ):
            if event["type"] == "text":
                yield f"data: {json.dumps({'type': 'text', 'content': event['content']}, ensure_ascii=False)}\n\n"
            elif event["type"] == "end":
                yield f"data: {json.dumps({'type': 'end', 'citations': event['citations'], 'token_count': event['token_count']}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            elif event["type"] == "error":
                yield f"data: {json.dumps({'type': 'error', 'content': event['content']}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )