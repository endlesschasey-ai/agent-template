"""流式输出引擎 - 统一管理所有 SSE 事件的发送"""
import json
import time
import uuid
from typing import Optional, AsyncGenerator
from enum import Enum

from .logger import get_logger

logger = get_logger(__name__)


class EventType(str, Enum):
    """SSE 事件类型枚举"""
    SESSION_START = "session_start"
    THINKING = "thinking"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_PROGRESS = "tool_call_progress"
    TOOL_CALL_END = "tool_call_end"
    CONTENT = "content"
    DATA = "data"
    ERROR = "error"
    SESSION_END = "session_end"


class ToolStatus(str, Enum):
    """工具执行状态"""
    SUCCESS = "success"
    FAILED = "failed"


class SessionStatus(str, Enum):
    """会话状态"""
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class DataType(str, Enum):
    """数据类型"""
    DATAFRAME = "dataframe"
    CHART = "chart"
    IMAGE = "image"
    CUSTOM = "custom"


class ErrorType(str, Enum):
    """错误类型"""
    VALIDATION = "validation"
    EXECUTION = "execution"
    TIMEOUT = "timeout"
    SYSTEM = "system"


class StreamingEngine:
    """
    流式输出引擎

    功能：
    - 统一的事件发送接口
    - 自动添加元数据（时间戳、序号）
    - 事件类型验证
    - 日志记录
    """

    def __init__(self, request_id: Optional[str] = None):
        """
        初始化流式输出引擎

        Args:
            request_id: 请求唯一ID，如果不提供则自动生成
        """
        self.request_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        self.sequence = 0
        self.start_time = time.time()

    def _build_event(
        self,
        event_type: EventType,
        data: dict,
        extra_metadata: Optional[dict] = None
    ) -> dict:
        """
        构建事件对象

        Args:
            event_type: 事件类型
            data: 事件数据
            extra_metadata: 额外的元数据

        Returns:
            完整的事件对象
        """
        self.sequence += 1

        metadata = {
            "request_id": self.request_id,
            "timestamp": int(time.time() * 1000),
            "sequence": self.sequence
        }

        if extra_metadata:
            metadata.update(extra_metadata)

        event = {
            "type": event_type.value,
            "data": data,
            "metadata": metadata
        }

        return event

    def _format_sse(self, event: dict) -> str:
        """
        格式化为 SSE 格式

        Args:
            event: 事件对象

        Returns:
            SSE 格式字符串
        """
        json_str = json.dumps(event, ensure_ascii=False)
        return f"data: {json_str}\n\n"

    def emit_session_start(self, session_id: str) -> str:
        """
        发送会话开始事件

        Args:
            session_id: 会话ID

        Returns:
            SSE 格式字符串
        """
        event = self._build_event(
            EventType.SESSION_START,
            {
                "session_id": session_id,
                "request_id": self.request_id
            }
        )

        logger.info(f"[StreamingEngine] Session start: {session_id}, request: {self.request_id}")
        return self._format_sse(event)

    def emit_thinking(
        self,
        content: str,
        stage: Optional[str] = None
    ) -> str:
        """
        发送思考过程事件

        Args:
            content: 思考内容片段
            stage: 思考阶段 (reasoning/planning/analyzing)

        Returns:
            SSE 格式字符串
        """
        data = {"content": content}
        if stage:
            data["stage"] = stage

        event = self._build_event(EventType.THINKING, data)
        return self._format_sse(event)

    def emit_tool_call_start(
        self,
        tool_id: str,
        tool_name: str,
        description: str,
        arguments: Optional[dict] = None
    ) -> str:
        """
        发送工具调用开始事件

        Args:
            tool_id: 工具唯一ID
            tool_name: 工具名称
            description: 工具描述（中文）
            arguments: 工具参数

        Returns:
            SSE 格式字符串
        """
        data = {
            "tool_id": tool_id,
            "tool_name": tool_name,
            "description": description
        }

        if arguments:
            data["arguments"] = arguments

        event = self._build_event(EventType.TOOL_CALL_START, data)

        logger.info(
            f"[StreamingEngine] Tool call start: {tool_name} ({description}), "
            f"tool_id: {tool_id}"
        )

        return self._format_sse(event)

    def emit_tool_call_progress(
        self,
        tool_id: str,
        progress: float,
        message: str
    ) -> str:
        """
        发送工具执行进度事件（用于长时间执行的工具）

        Args:
            tool_id: 工具唯一ID
            progress: 进度 (0-100)
            message: 进度消息

        Returns:
            SSE 格式字符串
        """
        data = {
            "tool_id": tool_id,
            "progress": progress,
            "message": message
        }

        event = self._build_event(EventType.TOOL_CALL_PROGRESS, data)
        return self._format_sse(event)

    def emit_tool_call_end(
        self,
        tool_id: str,
        status: ToolStatus,
        result: Optional[dict] = None,
        error: Optional[dict] = None,
        duration_ms: Optional[int] = None
    ) -> str:
        """
        发送工具调用结束事件

        Args:
            tool_id: 工具唯一ID
            status: 执行状态 (success/failed)
            result: 执行结果（可选）
            error: 错误信息（status=failed 时）
            duration_ms: 执行耗时（毫秒）

        Returns:
            SSE 格式字符串
        """
        data = {
            "tool_id": tool_id,
            "status": status.value
        }

        if result:
            data["result"] = result

        if error:
            data["error"] = error

        extra_metadata = {}
        if duration_ms is not None:
            extra_metadata["duration_ms"] = duration_ms

        event = self._build_event(EventType.TOOL_CALL_END, data, extra_metadata)

        logger.info(
            f"[StreamingEngine] Tool call end: {tool_id}, "
            f"status: {status.value}, duration: {duration_ms}ms"
        )

        return self._format_sse(event)

    def emit_content(
        self,
        content: str,
        format: str = "markdown",
        is_complete: bool = False
    ) -> str:
        """
        发送内容事件（最终答案）

        Args:
            content: 内容片段
            format: 内容格式 (markdown/text/html)
            is_complete: 是否是最后一个片段

        Returns:
            SSE 格式字符串
        """
        data = {
            "content": content,
            "format": format,
            "is_complete": is_complete
        }

        event = self._build_event(EventType.CONTENT, data)
        return self._format_sse(event)

    def emit_data(
        self,
        data_type: DataType,
        data: dict,
        metadata: Optional[dict] = None
    ) -> str:
        """
        发送结构化数据事件

        Args:
            data_type: 数据类型 (dataframe/chart/image/custom)
            data: 数据内容
            metadata: 数据元信息

        Returns:
            SSE 格式字符串
        """
        event_data = {
            "data_type": data_type.value,
            "data": data
        }

        if metadata:
            event_data["metadata"] = metadata

        event = self._build_event(EventType.DATA, event_data)

        logger.info(
            f"[StreamingEngine] Data event: type={data_type.value}, "
            f"size={len(json.dumps(data))} bytes"
        )

        return self._format_sse(event)

    def emit_error(
        self,
        error_type: ErrorType,
        message: str,
        details: Optional[dict] = None,
        recoverable: bool = False
    ) -> str:
        """
        发送错误事件

        Args:
            error_type: 错误类型
            message: 用户可见的错误信息
            details: 详细错误信息（调试用）
            recoverable: 是否可恢复

        Returns:
            SSE 格式字符串
        """
        data = {
            "error_type": error_type.value,
            "message": message,
            "recoverable": recoverable
        }

        if details:
            data["details"] = details

        event = self._build_event(EventType.ERROR, data)

        logger.error(
            f"[StreamingEngine] Error event: type={error_type.value}, "
            f"message={message}, recoverable={recoverable}"
        )

        return self._format_sse(event)

    def emit_session_end(
        self,
        status: SessionStatus,
        summary: Optional[dict] = None
    ) -> str:
        """
        发送会话结束事件

        Args:
            status: 会话状态 (completed/error/cancelled)
            summary: 会话摘要信息

        Returns:
            SSE 格式字符串
        """
        duration_ms = int((time.time() - self.start_time) * 1000)

        data = {
            "status": status.value
        }

        if summary:
            data["summary"] = summary
        else:
            data["summary"] = {
                "duration_ms": duration_ms,
                "total_events": self.sequence
            }

        event = self._build_event(EventType.SESSION_END, data)

        logger.info(
            f"[StreamingEngine] Session end: status={status.value}, "
            f"duration={duration_ms}ms, events={self.sequence}"
        )

        return self._format_sse(event)


# ==================== 辅助生成器函数 ====================

async def stream_with_engine(
    engine: StreamingEngine,
    content_generator: AsyncGenerator[str, None]
) -> AsyncGenerator[str, None]:
    """
    使用 StreamingEngine 包装内容生成器

    Args:
        engine: 流式输出引擎实例
        content_generator: 内容生成器

    Yields:
        SSE 格式的事件字符串
    """
    try:
        async for chunk in content_generator:
            yield engine.emit_content(chunk)
    except Exception as e:
        yield engine.emit_error(
            ErrorType.EXECUTION,
            f"内容生成失败: {str(e)}",
            details={"exception": str(e)},
            recoverable=False
        )
        raise
