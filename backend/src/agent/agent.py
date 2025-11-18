"""Agent configuration and creation."""
import logging
from agno.agent import Agent
from agno.models.dashscope import DashScope
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from .tools import AgentToolkit

logger = logging.getLogger(__name__)

# Agent 系统提示词（可根据需求自定义）
SYSTEM_PROMPT = """你是一个智能 AI 助手，能够与用户进行对话交流。

核心能力：
- 理解和回答用户的问题
- 进行逻辑推理和分析
- 展示表格数据（使用 display_table 工具）

工作方式：
- 直接回答用户问题，使用清晰、准确、有条理的语言
- 需要展示数据时，使用 display_table 工具
- 使用 markdown 格式来组织答案
"""


def create_agent(
    session_id: str,
    db: AsyncSession,
    event_queue=None
) -> Agent:
    """
    创建 AI Agent

    Args:
        session_id: 当前会话 ID
        db: 数据库会话
        event_queue: 事件队列（asyncio.Queue）

    Returns:
        配置好的 Agent 实例
    """
    # 创建工具集
    toolkit = AgentToolkit(
        session_id=session_id,
        db=db,
        event_queue=event_queue
    )

    # 创建模型实例
    model = DashScope(
        id="qwen-max",
        base_url=settings.DASHSCOPE_BASE_URL,
        api_key=settings.DASHSCOPE_API_KEY,
    )

    # 创建 Agent
    agent = Agent(
        model=model,
        tools=[toolkit],
        instructions=SYSTEM_PROMPT,
        markdown=True,
        debug_mode=True,
    )

    logger.info(f"[Agent] Created for session {session_id}")

    return agent
