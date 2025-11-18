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
                logger.info("[process_agent_stream] 🚀 开始处理 Agent 流式响应")
                chunk_count = 0
                try:
                    logger.info("[process_agent_stream] 📡 准备迭代响应流...")
                    async for chunk in response:
                        chunk_count += 1
                        logger.info(f"[process_agent_stream] 📦 收到 chunk #{chunk_count}: type={type(chunk)}, has_content={hasattr(chunk, 'content')}")

                        # 打印 chunk 的属性
                        if hasattr(chunk, '__dict__'):
                            logger.debug(f"[process_agent_stream] chunk 属性: {chunk.__dict__}")

                        # 文本内容 - 发送为正文内容
                        if hasattr(chunk, "content") and chunk.content:
                            logger.info(f"[process_agent_stream] ✅ 有内容: {chunk.content[:100]}...")
                            accumulated_content += chunk.content

                            # 将 Agent 的文本输出作为正文内容发送
                            yield engine.emit_content(
                                content=chunk.content,
                                format="markdown",
                                is_complete=False
                            )
                        else:
                            logger.warning(f"[process_agent_stream] ⚠️  chunk 没有 content 或 content 为空")

                    logger.info(f"[process_agent_stream] ✅ 流式响应结束，共收到 {chunk_count} 个 chunks")
                except Exception as e:
                    logger.error(f"[process_agent_stream] ❌ 处理流时出错: {e}", exc_info=True)
                finally:
                    agent_done = True
                    logger.info("[process_agent_stream] 🏁 设置 agent_done=True，发送完成事件")
                    await event_queue.put({"event_type": "agent_done"})

            # 启动 Agent 流式处理任务
            agent_generator = process_agent_stream()

            # 同时处理两个流：Agent 输出流和事件队列
            try:
                # 使用标志跟踪哪个流还在运行
                agent_streaming = True
                loop_count = 0
                agent_task_running = None  # 跟踪当前运行的 agent_task

                logger.info("[main_loop] 🔄 开始主循环，同时处理 Agent 流和事件队列")

                while agent_streaming or not event_queue.empty():
                    loop_count += 1
                    logger.debug(f"[main_loop] 循环 #{loop_count}, agent_streaming={agent_streaming}, queue_empty={event_queue.empty()}")

                    # 创建两个任务
                    tasks = []

                    # Agent 输出流任务 - 只有在没有任务运行时才创建新的
                    if agent_streaming and agent_task_running is None:
                        agent_task_running = asyncio.create_task(
                            anext(agent_generator, None)
                        )
                        logger.debug(f"[main_loop] 创建新的 agent_task")

                    if agent_task_running is not None:
                        tasks.append(agent_task_running)

                    # 事件队列任务（带超时，避免永久等待）
                    try:
                        queue_task = asyncio.create_task(
                            asyncio.wait_for(event_queue.get(), timeout=0.1)
                        )
                        tasks.append(queue_task)
                        logger.debug(f"[main_loop] 添加 queue_task")
                    except asyncio.TimeoutError:
                        pass

                    if not tasks:
                        logger.info("[main_loop] 没有任务，退出循环")
                        break

                    # 等待任意任务完成
                    logger.debug(f"[main_loop] 等待 {len(tasks)} 个任务完成...")
                    done, pending = await asyncio.wait(
                        tasks,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    logger.debug(f"[main_loop] {len(done)} 个任务完成，{len(pending)} 个任务待处理")

                    # 处理完成的任务
                    for task in done:
                        # 检查是否是 agent_task 完成了
                        if task is agent_task_running:
                            agent_task_running = None
                            logger.debug("[main_loop] agent_task 已完成，重置为 None")

                        try:
                            result = task.result()
                            logger.debug(f"[main_loop] 任务结果: type={type(result)}, value={str(result)[:200] if result else 'None'}")

                            # 如果是 Agent 输出
                            if result and isinstance(result, str):
                                logger.info(f"[main_loop] 📤 Agent 输出 (str): {result[:100]}...")
                                yield result

                            # 如果是 Agent 完成信号
                            elif result is None and agent_streaming:
                                logger.info("[main_loop] 🏁 Agent 完成信号 (None)")
                                agent_streaming = False

                            # 如果是事件队列的事件
                            elif result and isinstance(result, dict):
                                event = result
                                logger.info(f"[main_loop] 📨 事件队列事件: {event.get('event_type')}")

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
