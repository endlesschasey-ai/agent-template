"""Session management API routes."""
from fastapi import APIRouter, HTTPException
from typing import List

from ...db import AsyncSessionLocal
from ...services import ChatService
from ...models.schema import SessionCreate, SessionResponse

router = APIRouter()


@router.post("/create", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    """创建新会话"""
    async with AsyncSessionLocal() as db:
        service = ChatService(db)
        session = await service.create_session(title=request.title or "新对话")

        # 获取消息数量
        message_count = await service.get_message_count(session.session_id)

        return SessionResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            last_activity_at=session.last_activity_at,
            message_count=message_count
        )


@router.get("/list", response_model=List[SessionResponse])
async def list_sessions():
    """获取所有会话列表"""
    async with AsyncSessionLocal() as db:
        service = ChatService(db)
        sessions = await service.list_sessions(limit=50)

        result = []
        for session in sessions:
            message_count = await service.get_message_count(session.session_id)
            result.append(
                SessionResponse(
                    session_id=session.session_id,
                    title=session.title,
                    created_at=session.created_at,
                    last_activity_at=session.last_activity_at,
                    message_count=message_count
                )
            )

        return result


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """获取会话详情"""
    async with AsyncSessionLocal() as db:
        service = ChatService(db)
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        message_count = await service.get_message_count(session.session_id)

        return SessionResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            last_activity_at=session.last_activity_at,
            message_count=message_count
        )
