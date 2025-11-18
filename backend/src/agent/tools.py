"""Agent tools definition."""
import time
import uuid
import asyncio
from agno.tools import Toolkit
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class AgentToolkit(Toolkit):
    """Agent 工具集"""

    def __init__(
        self,
        session_id: str,
        db: AsyncSession,
        event_queue: Optional[asyncio.Queue] = None
    ):
        """
        初始化工具集

        Args:
            session_id: 当前会话 ID
            db: 数据库会话
            event_queue: 事件队列（用于发送工具调用事件）
        """
        super().__init__(name="agent_toolkit")
        self.session_id = session_id
        self.db = db
        self.event_queue = event_queue
        # 只注册 display_table，移除 finalize_answer
        self.register(self.display_table)

    async def _emit_event(self, event: dict):
        """发送事件到队列"""
        if self.event_queue:
            await self.event_queue.put(event)

    async def finalize_answer(self, answer: str) -> dict:
        """
        输出最终答案（必须调用此工具来输出回复）

        Args:
            answer: 最终答案内容

        Returns:
            包含最终答案的字典
        """
        tool_id = f"tool_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        # 发送工具调用开始事件
        await self._emit_event({
            "event_type": "tool_call_start",
            "tool_id": tool_id,
            "tool_name": "finalize_answer",
            "description": "输出最终答案",
            "arguments": {"answer_length": len(answer)}
        })

        logger.info(f"[finalize_answer] 输出最终答案，长度: {len(answer)} 字符")

        # 发送内容事件
        await self._emit_event({
            "event_type": "content",
            "content": answer,
            "format": "markdown",
            "is_complete": True
        })

        result = {
            "type": "final_answer",
            "content": answer
        }

        # 发送工具调用结束事件
        duration_ms = int((time.time() - start_time) * 1000)
        await self._emit_event({
            "event_type": "tool_call_end",
            "tool_id": tool_id,
            "status": "success",
            "result": result,
            "duration_ms": duration_ms
        })

        return result

    async def display_table(
        self,
        table_name: str,
        columns: list[str],
        data: list[list]
    ) -> dict:
        """
        展示表格数据

        Args:
            table_name: 表格名称
            columns: 列名列表
            data: 数据列表（二维列表）

        Returns:
            包含表格数据的字典

        Example:
            await display_table(
                table_name="销售数据",
                columns=["产品", "销量", "金额"],
                data=[
                    ["产品A", 100, 5000],
                    ["产品B", 200, 8000]
                ]
            )
        """
        tool_id = f"tool_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        # 发送工具调用开始事件
        await self._emit_event({
            "event_type": "tool_call_start",
            "tool_id": tool_id,
            "tool_name": "display_table",
            "description": f"展示表格: {table_name}",
            "arguments": {
                "table_name": table_name,
                "columns": len(columns),
                "rows": len(data)
            }
        })

        logger.info(
            f"[display_table] 表格: {table_name}, "
            f"列数: {len(columns)}, 行数: {len(data)}"
        )

        # 构建表格数据
        table_data = {
            "name": table_name,
            "columns": columns,
            "rows": data
        }

        # 发送数据事件
        await self._emit_event({
            "event_type": "data",
            "data_type": "dataframe",
            "data": table_data,
            "metadata": {"description": f"表格数据: {table_name}"}
        })

        result = {
            "type": "dataframe_display",
            "dataframe_name": table_name,
            "columns": columns,
            "data": data
        }

        # 发送工具调用结束事件
        duration_ms = int((time.time() - start_time) * 1000)
        await self._emit_event({
            "event_type": "tool_call_end",
            "tool_id": tool_id,
            "status": "success",
            "result": result,
            "duration_ms": duration_ms
        })

        return result
