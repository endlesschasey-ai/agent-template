"""Message ORM model."""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
import uuid
import json

from .base import Base


class Message(Base):
    """消息表 - 存储对话消息"""
    __tablename__ = "messages"

    message_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    role = Column(String, CheckConstraint("role IN ('user', 'assistant')"), nullable=False)
    content = Column(Text, nullable=False)
    extra_data = Column("metadata", Text, nullable=True)  # JSON: 存储工具调用、表格数据等
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="messages")
    files = relationship("File", back_populates="message", cascade="all, delete-orphan")

    @property
    def metadata_dict(self) -> Optional[dict]:
        """解析 metadata JSON"""
        if not self.extra_data:
            return None
        try:
            return json.loads(self.extra_data)
        except json.JSONDecodeError:
            return None

    def set_metadata(self, metadata: dict):
        """设置 metadata"""
        self.extra_data = json.dumps(metadata, ensure_ascii=False)
