# 流式输出协议设计文档

## 1. 消息类型规范

### 1.1 事件类型定义

| 事件类型 | 说明 | 使用场景 | 数据结构 |
|---------|------|---------|---------|
| `session_start` | 会话开始 | 开始处理请求时 | `{ session_id, request_id }` |
| `thinking` | 思考过程 | Agent 推理过程 | `{ content }` |
| `tool_call_start` | 工具调用开始 | 工具执行前 | `{ tool_id, tool_name, arguments }` |
| `tool_call_progress` | 工具执行进度 | 长时间工具执行 | `{ tool_id, progress, message }` |
| `tool_call_end` | 工具调用结束 | 工具执行后 | `{ tool_id, status, result?, error? }` |
| `content` | 主要内容 | 最终答案输出 | `{ content, format? }` |
| `data` | 结构化数据 | 表格、图表等 | `{ data_type, data, metadata? }` |
| `error` | 错误信息 | 发生错误时 | `{ error_type, message, details? }` |
| `session_end` | 会话结束 | 请求处理完成 | `{ status, summary? }` |

### 1.2 统一消息格式

```json
{
  "type": "事件类型",
  "data": {
    // 类型特定的数据
  },
  "metadata": {
    "request_id": "请求唯一ID",
    "timestamp": 1234567890,
    "sequence": 1  // 消息序号
  }
}
```

### 1.3 详细事件规范

#### session_start
```json
{
  "type": "session_start",
  "data": {
    "session_id": "sess_xxx",
    "request_id": "req_xxx"
  },
  "metadata": {
    "timestamp": 1234567890,
    "sequence": 0
  }
}
```

#### thinking
```json
{
  "type": "thinking",
  "data": {
    "content": "思考内容片段",
    "stage": "reasoning" | "planning" | "analyzing"  // 可选：思考阶段
  },
  "metadata": {
    "request_id": "req_xxx",
    "timestamp": 1234567890,
    "sequence": 1
  }
}
```

#### tool_call_start
```json
{
  "type": "tool_call_start",
  "data": {
    "tool_id": "tool_xxx",
    "tool_name": "display_table",
    "description": "展示表格数据",  // 中文描述
    "arguments": {
      "table_name": "销售数据",
      "columns": ["产品", "销量"]
    }
  },
  "metadata": {
    "request_id": "req_xxx",
    "timestamp": 1234567890,
    "sequence": 2
  }
}
```

#### tool_call_end
```json
{
  "type": "tool_call_end",
  "data": {
    "tool_id": "tool_xxx",
    "status": "success" | "failed",
    "result": {
      // 工具返回结果（可选）
    },
    "error": {
      "message": "错误信息",
      "code": "ERROR_CODE"
    }  // 仅在 status = failed 时
  },
  "metadata": {
    "request_id": "req_xxx",
    "timestamp": 1234567890,
    "sequence": 3,
    "duration_ms": 150  // 执行耗时
  }
}
```

#### content
```json
{
  "type": "content",
  "data": {
    "content": "最终答案内容片段",
    "format": "markdown" | "text" | "html",  // 默认 markdown
    "is_complete": false  // 是否是最后一个片段
  },
  "metadata": {
    "request_id": "req_xxx",
    "timestamp": 1234567890,
    "sequence": 4
  }
}
```

#### data
```json
{
  "type": "data",
  "data": {
    "data_type": "dataframe" | "chart" | "image" | "custom",
    "data": {
      // 根据 data_type 的具体数据
      "name": "数据名称",
      "columns": [...],
      "rows": [...]
    },
    "metadata": {
      "description": "数据描述"
    }
  },
  "metadata": {
    "request_id": "req_xxx",
    "timestamp": 1234567890,
    "sequence": 5
  }
}
```

#### error
```json
{
  "type": "error",
  "data": {
    "error_type": "validation" | "execution" | "timeout" | "system",
    "message": "用户可见的错误信息",
    "details": {
      // 详细错误信息（调试用）
      "stack_trace": "...",
      "context": {}
    },
    "recoverable": true | false
  },
  "metadata": {
    "request_id": "req_xxx",
    "timestamp": 1234567890,
    "sequence": 6
  }
}
```

#### session_end
```json
{
  "type": "session_end",
  "data": {
    "status": "completed" | "error" | "cancelled",
    "summary": {
      "total_tokens": 1500,
      "duration_ms": 3000,
      "tool_calls": 3
    }
  },
  "metadata": {
    "request_id": "req_xxx",
    "timestamp": 1234567890,
    "sequence": 7
  }
}
```

## 2. StreamingEngine 架构设计

### 2.1 核心职责

1. **事件发送**：统一的事件发送接口
2. **格式化**：自动添加 metadata、时间戳、序号
3. **验证**：验证事件类型和数据格式
4. **日志**：记录所有事件用于调试
5. **错误处理**：优雅处理发送失败

### 2.2 类设计

```python
class StreamingEngine:
    """流式输出引擎"""

    def __init__(self, request_id: str):
        self.request_id = request_id
        self.sequence = 0
        self.start_time = time.time()

    async def emit_session_start(self, session_id: str) -> str:
        """发送会话开始事件"""

    async def emit_thinking(self, content: str, stage: str = None) -> str:
        """发送思考过程事件"""

    async def emit_tool_call_start(
        self,
        tool_id: str,
        tool_name: str,
        description: str,
        arguments: dict
    ) -> str:
        """发送工具调用开始事件"""

    async def emit_tool_call_end(
        self,
        tool_id: str,
        status: str,
        result: dict = None,
        error: dict = None,
        duration_ms: int = None
    ) -> str:
        """发送工具调用结束事件"""

    async def emit_content(
        self,
        content: str,
        format: str = "markdown",
        is_complete: bool = False
    ) -> str:
        """发送内容事件"""

    async def emit_data(
        self,
        data_type: str,
        data: dict,
        metadata: dict = None
    ) -> str:
        """发送结构化数据事件"""

    async def emit_error(
        self,
        error_type: str,
        message: str,
        details: dict = None,
        recoverable: bool = False
    ) -> str:
        """发送错误事件"""

    async def emit_session_end(
        self,
        status: str,
        summary: dict = None
    ) -> str:
        """发送会话结束事件"""
```

## 3. 前端状态管理

### 3.1 消息状态结构

```typescript
interface MessageState {
  // 基础信息
  messageId: string;
  role: 'user' | 'assistant';

  // 不同类型的内容
  thinkingContent: string;        // 思考过程
  mainContent: string;            // 最终答案

  // 工具调用
  toolCalls: ToolCall[];

  // 结构化数据
  dataBlocks: DataBlock[];

  // 状态
  isStreaming: boolean;
  hasError: boolean;
  errorMessage?: string;

  // 元数据
  metadata: {
    requestId: string;
    startTime: number;
    endTime?: number;
  };
}
```

### 3.2 事件处理器

```typescript
class MessageStreamHandler {
  private message: MessageState;

  handleEvent(event: SSEEvent) {
    switch (event.type) {
      case 'session_start':
        this.handleSessionStart(event);
        break;
      case 'thinking':
        this.handleThinking(event);
        break;
      case 'tool_call_start':
        this.handleToolCallStart(event);
        break;
      case 'tool_call_end':
        this.handleToolCallEnd(event);
        break;
      case 'content':
        this.handleContent(event);
        break;
      case 'data':
        this.handleData(event);
        break;
      case 'error':
        this.handleError(event);
        break;
      case 'session_end':
        this.handleSessionEnd(event);
        break;
    }
  }
}
```

## 4. 优化要点

### 4.1 性能优化

1. **批量更新**：累积多个小片段再更新 UI
2. **虚拟滚动**：长对话列表使用虚拟滚动
3. **懒加载**：思考过程默认折叠

### 4.2 用户体验

1. **进度指示**：显示当前执行阶段
2. **错误恢复**：支持重试机制
3. **平滑动画**：过渡动画优化

### 4.3 可维护性

1. **类型安全**：前后端完整类型定义
2. **事件验证**：运行时验证事件格式
3. **日志追踪**：完整的事件日志

## 5. 实现计划

1. ✅ 后端实现 StreamingEngine
2. ✅ 更新 Agent tools 使用新引擎
3. ✅ 更新 chat API 路由
4. ✅ 前端更新类型定义
5. ✅ 前端实现 MessageStreamHandler
6. ✅ 更新 UI 组件
7. ✅ 测试和文档

## 6. 向后兼容

为了保持向后兼容，旧的事件类型映射到新类型：

| 旧类型 | 新类型 | 说明 |
|-------|-------|------|
| `token` | `content` | 内容片段 |
| `tool_call` | `tool_call_start` | 工具调用开始 |
| `tool_result` | `tool_call_end` | 工具调用结束 |
| `thinking` | `thinking` | 保持不变 |
| `final_answer` | `content` | 最终答案 |
| `dataframe_data` | `data` | 结构化数据 |
| `done` | `session_end` | 会话结束 |
| `error` | `error` | 保持不变 |
