"""Chat service for managing sessions, messages, and files."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from typing import Optional
import json

from ..models.db import Session, Message, File
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ChatService:
    """聊天服务 - 封装会话、消息、文件的数据库操作"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Session ====================

    async def create_session(self, title: str = "新对话") -> Session:
        """创建新会话"""
        session = Session(title=title)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        logger.info(f"[ChatService] 创建会话: {session.session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        result = await self.db.execute(
            select(Session).where(Session.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_sessions(self, limit: int = 50) -> list[Session]:
        """列出所有会话（按最后活动时间倒序）"""
        result = await self.db.execute(
            select(Session)
            .order_by(Session.last_activity_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_session_activity(self, session_id: str):
        """更新会话最后活动时间"""
        session = await self.get_session(session_id)
        if session:
            session.update_activity()
            await self.db.commit()

    # ==================== Message ====================

    async def create_user_message(
        self,
        session_id: str,
        content: str,
        file_ids: Optional[list[str]] = None
    ) -> Message:
        """
        创建用户消息并关联文件

        Args:
            session_id: 会话 ID
            content: 消息内容
            file_ids: 文件 ID 列表

        Returns:
            创建的消息对象
        """
        message = Message(
            session_id=session_id,
            role="user",
            content=content
        )
        self.db.add(message)
        await self.db.flush()  # 获取 message_id

        # 关联文件
        if file_ids:
            for file_id in file_ids:
                file = await self.get_file(file_id)
                if file:
                    file.message_id = message.message_id

        await self.db.commit()
        await self.db.refresh(message)

        # 更新会话活动时间
        await self.update_session_activity(session_id)

        logger.info(
            f"[ChatService] 创建用户消息: {message.message_id}, "
            f"关联文件: {file_ids or []}"
        )

        return message

    async def create_assistant_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> Message:
        """
        创建 assistant 消息

        Args:
            session_id: 会话 ID
            content: 消息内容
            metadata: 元数据（工具调用、表格数据等）

        Returns:
            创建的消息对象
        """
        message = Message(
            session_id=session_id,
            role="assistant",
            content=content
        )

        if metadata:
            message.set_metadata(metadata)

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        # 更新会话活动时间
        await self.update_session_activity(session_id)

        logger.info(f"[ChatService] 创建 assistant 消息: {message.message_id}")

        return message

    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> list[Message]:
        """获取会话的所有消息（按创建时间升序）"""
        query = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_message_count(self, session_id: str) -> int:
        """获取会话的消息数量"""
        result = await self.db.execute(
            select(func.count(Message.message_id))
            .where(Message.session_id == session_id)
        )
        return result.scalar() or 0

    # ==================== File ====================

    async def create_file(
        self,
        session_id: str,
        filename: str,
        file_type: str,
        file_size: int,
        file_data: bytes
    ) -> File:
        """创建文件记录"""
        file = File(
            session_id=session_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            file_data=file_data
        )
        self.db.add(file)
        await self.db.commit()
        await self.db.refresh(file)

        logger.info(
            f"[ChatService] 创建文件: {file.file_id}, "
            f"文件名: {filename}, 大小: {file_size} bytes"
        )

        return file

    async def get_file(self, file_id: str) -> Optional[File]:
        """获取文件"""
        result = await self.db.execute(
            select(File).where(File.file_id == file_id)
        )
        return result.scalar_one_or_none()

    async def get_session_files(self, session_id: str) -> list[File]:
        """获取会话的所有文件"""
        result = await self.db.execute(
            select(File)
            .where(File.session_id == session_id)
            .order_by(File.uploaded_at.desc())
        )
        return list(result.scalars().all())
