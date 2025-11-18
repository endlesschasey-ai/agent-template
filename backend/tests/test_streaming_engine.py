"""
StreamingEngine 单元测试

测试所有事件类型的生成和格式化
"""

import pytest
import json
import time
from src.utils.streaming_engine import (
    StreamingEngine,
    EventType,
    ToolStatus,
    SessionStatus,
    DataType,
    ErrorType,
)


class TestStreamingEngine:
    """StreamingEngine 核心功能测试"""

    def setup_method(self):
        """每个测试前的设置"""
        self.engine = StreamingEngine(request_id="test_req_123")

    def test_initialization(self):
        """测试引擎初始化"""
        assert self.engine.request_id == "test_req_123"
        assert self.engine.sequence == 0
        assert self.engine.start_time > 0

    def test_session_start_event(self):
        """测试会话开始事件"""
        sse_data = self.engine.emit_session_start("session_abc")

        # 解析 SSE 格式
        assert sse_data.startswith("data: ")
        json_str = sse_data.replace("data: ", "").strip()
        event = json.loads(json_str)

        # 验证事件结构
        assert event["type"] == EventType.SESSION_START
        assert event["data"]["session_id"] == "session_abc"
        assert event["data"]["request_id"] == "test_req_123"
        assert "metadata" in event
        assert event["metadata"]["request_id"] == "test_req_123"
        assert event["metadata"]["sequence"] == 1

    def test_thinking_event(self):
        """测试思考过程事件"""
        sse_data = self.engine.emit_thinking("正在分析问题...", stage="reasoning")
        json_str = sse_data.replace("data: ", "").strip()
        event = json.loads(json_str)

        assert event["type"] == EventType.THINKING
        assert event["data"]["content"] == "正在分析问题..."
        assert event["data"]["stage"] == "reasoning"

    def test_tool_call_start_event(self):
        """测试工具调用开始事件"""
        sse_data = self.engine.emit_tool_call_start(
            tool_id="tool_001",
            tool_name="search_database",
            description="搜索数据库",
            arguments={"query": "test"}
        )
        json_str = sse_data.replace("data: ", "").strip()
        event = json.loads(json_str)

        assert event["type"] == EventType.TOOL_CALL_START
        assert event["data"]["tool_id"] == "tool_001"
        assert event["data"]["tool_name"] == "search_database"
        assert event["data"]["description"] == "搜索数据库"
        assert event["data"]["arguments"]["query"] == "test"

    def test_tool_call_end_event(self):
        """测试工具调用结束事件"""
        sse_data = self.engine.emit_tool_call_end(
            tool_id="tool_001",
            status=ToolStatus.SUCCESS,
            result={"count": 5}
        )
        json_str = sse_data.replace("data: ", "").strip()
        event = json.loads(json_str)

        assert event["type"] == EventType.TOOL_CALL_END
        assert event["data"]["tool_id"] == "tool_001"
        assert event["data"]["status"] == ToolStatus.SUCCESS
        assert event["data"]["result"]["count"] == 5
        assert "duration_ms" in event["metadata"]

    def test_content_event(self):
        """测试内容事件"""
        sse_data = self.engine.emit_content(
            content="这是最终答案",
            format="markdown",
            is_complete=True
        )
        json_str = sse_data.replace("data: ", "").strip()
        event = json.loads(json_str)

        assert event["type"] == EventType.CONTENT
        assert event["data"]["content"] == "这是最终答案"
        assert event["data"]["format"] == "markdown"
        assert event["data"]["is_complete"] is True

    def test_data_event_dataframe(self):
        """测试数据事件 - DataFrame"""
        df_data = {
            "columns": ["A", "B"],
            "data": [[1, 2], [3, 4]]
        }
        sse_data = self.engine.emit_data(
            data_type=DataType.DATAFRAME,
            data=df_data,
            metadata={"name": "结果表"}
        )
        json_str = sse_data.replace("data: ", "").strip()
        event = json.loads(json_str)

        assert event["type"] == EventType.DATA
        assert event["data"]["data_type"] == DataType.DATAFRAME
        assert event["data"]["data"]["columns"] == ["A", "B"]
        assert event["data"]["metadata"]["name"] == "结果表"

    def test_error_event(self):
        """测试错误事件"""
        sse_data = self.engine.emit_error(
            message="发生了一个错误",
            error_type=ErrorType.EXECUTION,
            details={"line": 42}
        )
        json_str = sse_data.replace("data: ", "").strip()
        event = json.loads(json_str)

        assert event["type"] == EventType.ERROR
        assert event["data"]["message"] == "发生了一个错误"
        assert event["data"]["error_type"] == ErrorType.EXECUTION
        assert event["data"]["details"]["line"] == 42

    def test_session_end_event(self):
        """测试会话结束事件"""
        sse_data = self.engine.emit_session_end(
            status=SessionStatus.COMPLETED,
            summary="成功完成"
        )
        json_str = sse_data.replace("data: ", "").strip()
        event = json.loads(json_str)

        assert event["type"] == EventType.SESSION_END
        assert event["data"]["status"] == SessionStatus.COMPLETED
        assert event["data"]["summary"] == "成功完成"
        assert "total_duration_ms" in event["data"]

    def test_sequence_increment(self):
        """测试序列号自动递增"""
        # 第一个事件
        sse1 = self.engine.emit_thinking("思考1")
        event1 = json.loads(sse1.replace("data: ", "").strip())

        # 第二个事件
        sse2 = self.engine.emit_thinking("思考2")
        event2 = json.loads(sse2.replace("data: ", "").strip())

        # 序列号应该递增
        assert event1["metadata"]["sequence"] == 1
        assert event2["metadata"]["sequence"] == 2

    def test_timestamp_generation(self):
        """测试时间戳生成"""
        sse_data = self.engine.emit_thinking("测试")
        event = json.loads(sse_data.replace("data: ", "").strip())

        timestamp = event["metadata"]["timestamp"]
        current_time = int(time.time() * 1000)

        # 时间戳应该接近当前时间（允许1秒误差）
        assert abs(timestamp - current_time) < 1000

    def test_request_id_consistency(self):
        """测试 request_id 一致性"""
        # 所有事件应该有相同的 request_id
        event1 = json.loads(self.engine.emit_thinking("测试1").replace("data: ", "").strip())
        event2 = json.loads(self.engine.emit_content("测试2").replace("data: ", "").strip())

        assert event1["metadata"]["request_id"] == "test_req_123"
        assert event2["metadata"]["request_id"] == "test_req_123"

    def test_auto_request_id_generation(self):
        """测试自动生成 request_id"""
        engine = StreamingEngine()  # 不提供 request_id

        sse_data = engine.emit_thinking("测试")
        event = json.loads(sse_data.replace("data: ", "").strip())

        # 应该自动生成 request_id
        assert event["metadata"]["request_id"].startswith("req_")
        assert len(event["metadata"]["request_id"]) == 16  # req_ + 12字符


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_content(self):
        """测试空内容"""
        engine = StreamingEngine()
        sse_data = engine.emit_content("")
        event = json.loads(sse_data.replace("data: ", "").strip())

        assert event["data"]["content"] == ""

    def test_unicode_content(self):
        """测试 Unicode 内容"""
        engine = StreamingEngine()
        content = "测试 emoji 🚀 和特殊字符 ñ é ü"
        sse_data = engine.emit_thinking(content)
        event = json.loads(sse_data.replace("data: ", "").strip())

        assert event["data"]["content"] == content

    def test_large_data(self):
        """测试大数据量"""
        engine = StreamingEngine()
        large_data = {
            "columns": [f"col_{i}" for i in range(100)],
            "data": [[i] * 100 for i in range(1000)]
        }
        sse_data = engine.emit_data(DataType.DATAFRAME, large_data)
        event = json.loads(sse_data.replace("data: ", "").strip())

        assert len(event["data"]["data"]["columns"]) == 100
        assert len(event["data"]["data"]["data"]) == 1000

    def test_special_characters_in_tool_name(self):
        """测试工具名中的特殊字符"""
        engine = StreamingEngine()
        sse_data = engine.emit_tool_call_start(
            tool_id="tool_001",
            tool_name="search_with_特殊字符",
            description="测试/描述"
        )
        event = json.loads(sse_data.replace("data: ", "").strip())

        assert event["data"]["tool_name"] == "search_with_特殊字符"
        assert event["data"]["description"] == "测试/描述"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
