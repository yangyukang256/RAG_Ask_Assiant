from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.session import ChatSession
from app.models.message import Message
from app.core.exceptions import not_found, forbidden


class ChatService:
    """会话与消息服务"""

    @staticmethod
    def list_sessions(db: Session, user_id: int, page: int = 1, page_size: int = 20):
        """获取用户会话列表"""
        query = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.status == "active",
        ).order_by(desc(ChatSession.updated_at))

        total = query.count()
        sessions = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [s.to_dict() for s in sessions],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    @staticmethod
    def create_session(db: Session, user_id: int, title: str = "新会话") -> ChatSession:
        """创建新会话"""
        session = ChatSession(user_id=user_id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def update_session(db: Session, session_id: int, user_id: int, **kwargs) -> ChatSession:
        """更新会话"""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise not_found("会话不存在")
        if session.user_id != user_id:
            raise forbidden("无权操作此会话")
        for key, value in kwargs.items():
            if hasattr(session, key) and value is not None:
                setattr(session, key, value)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def delete_session(db: Session, session_id: int, user_id: int):
        """删除会话"""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise not_found("会话不存在")
        if session.user_id != user_id:
            raise forbidden("无权操作此会话")
        db.delete(session)
        db.commit()

    @staticmethod
    def get_messages(db: Session, session_id: int, user_id: int, page: int = 1, page_size: int = 50):
        """获取消息历史"""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise not_found("会话不存在")
        if session.user_id != user_id:
            raise forbidden("无权查看此会话")

        query = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at)

        total = query.count()
        messages = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "messages": [m.to_dict() for m in messages],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    def save_message(db: Session, session_id: int, role: str, content: str, citations: Optional[str] = None, token_count: int = 0) -> Message:
        """保存消息"""
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            citations=citations,
            token_count=token_count,
        )
        db.add(message)

        # 更新会话时间
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            from datetime import datetime, timezone
            session.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(message)
        return message