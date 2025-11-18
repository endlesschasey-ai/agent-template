"""Pydantic models for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ==================== Session ====================

class SessionCreate(BaseModel):
    """创建会话请求"""
    title: Optional[str] = "新对话"


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    title: str
    created_at: datetime
    last_activity_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


# ==================== Message ====================

class ChatRequest(BaseModel):
    """发送消息请求"""
    session_id: str
    content: str
    file_ids: Optional[list[str]] = None  # 附件文件 ID 列表


class MessageResponse(BaseModel):
    """消息响应"""
    message_id: str
    session_id: str
    role: str
    content: str
    metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== File ====================

class FileUploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str
    filename: str
    file_type: str
    file_size: int
    uploaded_at: datetime


class FileResponse(BaseModel):
    """文件详情响应"""
    file_id: str
    filename: str
    file_type: str
    file_size: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ==================== SSE Events ====================

class ThinkingEvent(BaseModel):
    """思考过程事件"""
    type: str = "thinking"
    content: str


class ToolCallEvent(BaseModel):
    """工具调用事件"""
    type: str = "tool_call"
    tool_id: str
    tool_name: str
    tool_args: str = ""
    status: str = "calling"


class ToolResultEvent(BaseModel):
    """工具结果事件"""
    type: str = "tool_result"
    tool_id: str
    status: str  # completed | failed


class FinalAnswerEvent(BaseModel):
    """最终答案事件"""
    type: str = "final_answer"
    content: str


class DataFrameEvent(BaseModel):
    """表格数据事件"""
    type: str = "dataframe_data"
    data: dict


class DoneEvent(BaseModel):
    """完成事件"""
    type: str = "done"


class ErrorEvent(BaseModel):
    """错误事件"""
    type: str = "error"
    message: str
