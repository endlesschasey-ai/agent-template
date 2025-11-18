"""File ORM model."""
from sqlalchemy import Column, String, Integer, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class File(Base):
    """文件表 - 存储用户上传的图片（仅支持图片）"""
    __tablename__ = "files"

    file_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    message_id = Column(String, ForeignKey("messages.message_id", ondelete="CASCADE"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # 例: 'image/png', 'image/jpeg'
    file_size = Column(Integer, nullable=False)
    file_data = Column(LargeBinary, nullable=False)  # 图片二进制数据
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="files")
    message = relationship("Message", back_populates="files")
