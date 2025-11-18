"""Chat API with StreamingEngine - SSE streaming support."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
from typing import AsyncGenerator

from ...db import AsyncSessionLocal
from ...services import ChatService
from ...agent import create_agent
from ...models.schema import ChatRequest
from ...utils.logger import get_logger
from ...utils.streaming_engine import (
    StreamingEngine,
    SessionStatus,
    ToolStatus,
    DataType,
    ErrorType
)

router = APIRouter()
logger = get_logger(__name__)


async def generate_sse_response(
    session_id: str,
    content: str,
    file_ids: list[str] | None
) -> AsyncGenerator[str, None]:
    """
    使用 StreamingEngine 生成 SSE 格式的流式响应

    流程：
    1. 创建 StreamingEngine 实例
    2. 创建事件队列（用于工具调用事件）
    3. 创建用户消息并关联文件
    4. 构建上下文（历史消息）
    5. 创建 Agent 并传入事件队列
    6. 并发处理 Agent 流式输出和事件队列
    7. 保存 assistant 消息
    8. 发送会话结束事件

    Args:
        session_id: 会话 ID
        content: 用户消息内容
        file_ids: 关联的文件 IDs

    Yields:
        SSE 格式的事件字符串
    """
    # 创建流式输出引擎
    engine = StreamingEngine()

    # 创建事件队列（用于工具调用事件）
    event_queue = asyncio.Queue()

    async with AsyncSessionLocal() as db:
        try:
            service = ChatService(db)

            # 验证会话是否存在
            session = await service.get_session(session_id)
            if not session:
                yield engine.emit_error(
                    ErrorType.VALIDATION,
                    "会话不存在",
                    recoverable=False
                )
                yield engine.emit_session_end(SessionStatus.ERROR)
                return

            # 发送会话开始事件
            yield engine.emit_session_start(session_id)

            # 创建用户消息并关联文件
            user_msg = await service.create_user_message(
                session_id=session_id,
                content=content,
                file_ids=file_ids
            )

            logger.info(
                f"[chat] 创建用户消息: {user_msg.message_id}, "
                f"关联文件: {file_ids or []}"
            )

            # 累积内容（用于保存）
            accumulated_content = ""
            tool_calls_metadata = []
            data_blocks_metadata = []

            # 构建上下文（历史消息）
            messages = await service.get_messages(session_id, limit=20)
            context_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            # 创建 Agent（传入事件队列）
            agent = create_agent(
                session_id=session_id,
                db=db,
                event_queue=event_queue
            )

            logger.info(
                f"[chat] 调用 Agent，上下文消息数: {len(context_messages)}, "
                f"当前输入: {content[:50]}"
            )

            # 流式调用 Agent
            response = agent.arun(input=content, stream=True)

            # 标记 Agent 流式响应是否结束
            agent_done = False

            async def process_agent_stream():
                """处理 Agent 流式响应"""
                nonlocal accumulated_content, agent_done
                try:
                    async for chunk in response:
                        # 文本内容 - 发送为正文内容
                        if hasattr(chunk, "content") and chunk.content:
                            accumulated_content += chunk.content
                            yield engine.emit_content(
                                content=chunk.content,
                                format="markdown",
                                is_complete=False
                            )
                except Exception as e:
                    logger.error(f"[process_agent_stream] 处理流时出错: {e}", exc_info=True)
                finally:
                    agent_done = True
                    await event_queue.put({"event_type": "agent_done"})

            # 启动 Agent 流式处理任务
            agent_generator = process_agent_stream()

            # 同时处理两个流：Agent 输出流和事件队列
            try:
                agent_streaming = True
                agent_task_running = None

                while agent_streaming or not event_queue.empty():
                    tasks = []

                    # Agent 输出流任务 - 只有在没有任务运行时才创建新的
                    if agent_streaming and agent_task_running is None:
                        agent_task_running = asyncio.create_task(
                            anext(agent_generator, None)
                        )

                    if agent_task_running is not None:
                        tasks.append(agent_task_running)

                    # 事件队列任务（带超时，避免永久等待）
                    try:
                        queue_task = asyncio.create_task(
                            asyncio.wait_for(event_queue.get(), timeout=0.1)
                        )
                        tasks.append(queue_task)
                    except asyncio.TimeoutError:
                        pass

                    if not tasks:
                        break

                    # 等待任意任务完成
                    done, pending = await asyncio.wait(
                        tasks,
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    # 处理完成的任务
                    for task in done:
                        # 检查是否是 agent_task 完成了
                        if task is agent_task_running:
                            agent_task_running = None

                        try:
                            result = task.result()

                            # 如果是 Agent 输出
                            if result and isinstance(result, str):
                                yield result

                            # 如果是 Agent 完成信号
                            elif result is None and agent_streaming:
                                agent_streaming = False

                            # 如果是事件队列的事件
                            elif result and isinstance(result, dict):
                                event = result

                                # Agent 完成
                                if event.get("event_type") == "agent_done":
                                    agent_streaming = False
                                    continue

                                # 工具调用开始
                                elif event.get("event_type") == "tool_call_start":
                                    sse_event = engine.emit_tool_call_start(
                                        tool_id=event["tool_id"],
                                        tool_name=event["tool_name"],
                                        description=event["description"],
                                        arguments=event.get("arguments")
                                    )
                                    yield sse_event

                                    # 记录到元数据
                                    tool_calls_metadata.append({
                                        "tool_id": event["tool_id"],
                                        "tool_name": event["tool_name"],
                                        "description": event["description"]
                                    })

                                # 工具调用结束
                                elif event.get("event_type") == "tool_call_end":
                                    status = ToolStatus.SUCCESS if event["status"] == "success" else ToolStatus.FAILED
                                    sse_event = engine.emit_tool_call_end(
                                        tool_id=event["tool_id"],
                                        status=status,
                                        result=event.get("result"),
                                        error=event.get("error"),
                                        duration_ms=event.get("duration_ms")
                                    )
                                    yield sse_event

                                # 内容事件
                                elif event.get("event_type") == "content":
                                    content_text = event["content"]
                                    accumulated_content += content_text
                                    sse_event = engine.emit_content(
                                        content=content_text,
                                        format=event.get("format", "markdown"),
                                        is_complete=event.get("is_complete", False)
                                    )
                                    yield sse_event

                                # 数据事件
                                elif event.get("event_type") == "data":
                                    sse_event = engine.emit_data(
                                        data_type=DataType(event["data_type"]),
                                        data=event["data"],
                                        metadata=event.get("metadata")
                                    )
                                    yield sse_event

                                    # 记录到元数据
                                    data_blocks_metadata.append({
                                        "data_type": event["data_type"],
                                        "name": event["data"].get("name", "未命名数据")
                                    })

                        except asyncio.TimeoutError:
                            # 队列超时是正常的，继续处理其他任务
                            continue
                        except Exception as e:
                            logger.error(f"[chat] 处理任务结果时出错: {e}", exc_info=True)
                            continue

                    # 取消未完成的任务（除了 agent_task）
                    for task in pending:
                        if task is not agent_task_running:
                            task.cancel()

            finally:
                # 确保 Agent 任务完成
                try:
                    async for _ in agent_generator:
                        pass
                except StopAsyncIteration:
                    pass

            # 保存 assistant 消息
            metadata = None
            if tool_calls_metadata or data_blocks_metadata:
                metadata = {}
                if tool_calls_metadata:
                    metadata["tool_calls"] = tool_calls_metadata
                if data_blocks_metadata:
                    metadata["data_blocks"] = data_blocks_metadata

            await service.create_assistant_message(
                session_id=session_id,
                content=accumulated_content,
                metadata=metadata
            )

            # 发送会话结束事件
            yield engine.emit_session_end(
                SessionStatus.COMPLETED,
                summary={
                    "tool_calls": len(tool_calls_metadata),
                    "data_blocks": len(data_blocks_metadata),
                    "content_length": len(accumulated_content)
                }
            )

            logger.info(
                f"[chat] 消息完成，session={session_id}, "
                f"回复长度={len(accumulated_content)}, "
                f"工具调用={len(tool_calls_metadata)}, "
                f"数据块={len(data_blocks_metadata)}"
            )

        except ValueError as e:
            # 业务逻辑错误
            logger.warning(f"[chat] 业务错误: {e}")
            yield engine.emit_error(
                ErrorType.VALIDATION,
                str(e),
                recoverable=False
            )
            yield engine.emit_session_end(SessionStatus.ERROR)

        except Exception as e:
            # 系统错误
            logger.error(f"[chat] 系统错误: {e}", exc_info=True)
            await db.rollback()
            yield engine.emit_error(
                ErrorType.SYSTEM,
                f"系统错误: {str(e)}",
                details={"exception": str(e)},
                recoverable=False
            )
            yield engine.emit_session_end(SessionStatus.ERROR)


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    发送消息并获取流式响应（使用 StreamingEngine）

    主要改进：
    - 统一的事件格式和类型
    - 完整的元数据支持
    - 更好的错误处理
    - 详细的日志记录

    Args:
        request: 包含 session_id、content、file_ids

    Returns:
        SSE 流式响应
    """
    return StreamingResponse(
        generate_sse_response(
            session_id=request.session_id,
            content=request.content,
            file_ids=request.file_ids
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
