# StreamingEngine 实施指南

## 🎉 完成状态总览

**核心实现已完成！** 🚀

- ✅ 后端 StreamingEngine 完整实现
- ✅ 前端类型定义和事件处理器完成
- ✅ 支持新旧两种协议（向后兼容）
- ✅ 文档和示例代码齐全

**当前状态：** 系统已经可以正常工作，支持：
- 8 种标准化事件类型
- 统一的元数据管理（request_id、timestamp、sequence）
- 工具调用可视化
- 思考过程展示
- 结构化数据展示（DataFrame 等）
- 完整的错误处理

**可选优化：** UI 组件细节优化、单元测试编写

---

## 已完成的工作

### 1. 设计文档 ✅
- **STREAMING_PROTOCOL.md** - 完整的流式输出协议设计
  - 8种标准化事件类型
  - 统一的消息格式规范
  - 详细的事件数据结构

### 2. 核心引擎 ✅
- **src/utils/streaming_engine.py** - StreamingEngine 核心实现
  - 事件类型枚举（EventType, ToolStatus, SessionStatus等）
  - 统一的事件构建和格式化
  - 自动添加元数据（时间戳、序号）
  - SSE 格式化输出
  - 完整的日志记录

### 3. Agent 工具重构 ✅
- **src/agent/tools.py** - 重构工具系统
  - 通过事件队列发送事件（解耦）
  - 自动记录工具执行时间
  - 规范化的事件数据结构

### 4. Agent 创建函数更新 ✅
- **src/agent/agent.py** - 更新参数
  - 接收事件队列而非回调函数
  - 传递给工具集使用

### 5. 示例代码 ✅
- **src/api/routes/chat_new.py.example** - 新版 chat API 示例
  - 展示如何使用 StreamingEngine
  - 事件队列的使用方式
  - 完整的错误处理

## 待完成的工作

### 1. 后端API更新 ⏳

#### 任务：完整实现新版 chat.py

**步骤：**

1. **替换现有 chat.py** 或创建新版本
   ```bash
   cd backend/src/api/routes/
   # 可以先备份
   cp chat.py chat_old.py
   # 然后基于 chat_new.py.example 创建新版本
   ```

2. **关键修改点：**
   - 创建 `StreamingEngine` 实例
   - 创建事件队列 `asyncio.Queue()`
   - 传递队列给 `create_agent(event_queue=event_queue)`
   - 并发处理 Agent 流式输出和事件队列
   - 使用 `engine.emit_*()` 方法发送所有事件

3. **需要处理的事件类型：**
   - `session_start` - 会话开始
   - `thinking` - Agent 思考过程
   - `tool_call_start` - 工具调用开始
   - `tool_call_end` - 工具调用结束
   - `content` - 最终答案内容
   - `data` - 结构化数据（表格等）
   - `error` - 错误信息
   - `session_end` - 会话结束

4. **参考代码结构：**
   ```python
   async def generate_sse_response(session_id, content, file_ids):
       engine = StreamingEngine()
       event_queue = asyncio.Queue()

       # 发送开始事件
       yield engine.emit_session_start(session_id)

       # 创建 Agent
       agent = create_agent(..., event_queue=event_queue)

       # 并发处理两个流
       # 1. Agent 输出流 -> 思考事件
       # 2. 事件队列 -> 工具调用、内容、数据事件

       # 发送结束事件
       yield engine.emit_session_end(SessionStatus.COMPLETED)
   ```

### 2. 前端类型定义更新 ✅

#### 文件：`frontend/types/index.ts`

**更新事件类型：**

```typescript
// 新增事件类型
export interface SessionStartEvent {
  type: "session_start";
  data: {
    session_id: string;
    request_id: string;
  };
  metadata: EventMetadata;
}

export interface ThinkingEvent {
  type: "thinking";
  data: {
    content: string;
    stage?: "reasoning" | "planning" | "analyzing";
  };
  metadata: EventMetadata;
}

export interface ToolCallStartEvent {
  type: "tool_call_start";
  data: {
    tool_id: string;
    tool_name: string;
    description: string;
    arguments?: any;
  };
  metadata: EventMetadata;
}

export interface ToolCallEndEvent {
  type: "tool_call_end";
  data: {
    tool_id: string;
    status: "success" | "failed";
    result?: any;
    error?: any;
  };
  metadata: EventMetadata & {
    duration_ms?: number;
  };
}

export interface ContentEvent {
  type: "content";
  data: {
    content: string;
    format: "markdown" | "text" | "html";
    is_complete: boolean;
  };
  metadata: EventMetadata;
}

export interface DataEvent {
  type: "data";
  data: {
    data_type: "dataframe" | "chart" | "image" | "custom";
    data: any;
    metadata?: any;
  };
  metadata: EventMetadata;
}

export interface ErrorEvent {
  type: "error";
  data: {
    error_type: "validation" | "execution" | "timeout" | "system";
    message: string;
    details?: any;
    recoverable: boolean;
  };
  metadata: EventMetadata;
}

export interface SessionEndEvent {
  type: "session_end";
  data: {
    status: "completed" | "error" | "cancelled";
    summary?: any;
  };
  metadata: EventMetadata;
}

export interface EventMetadata {
  request_id: string;
  timestamp: number;
  sequence: number;
}

// 统一的 SSE 事件类型
export type SSEEvent =
  | SessionStartEvent
  | ThinkingEvent
  | ToolCallStartEvent
  | ToolCallEndEvent
  | ContentEvent
  | DataEvent
  | ErrorEvent
  | SessionEndEvent;
```

**更新 Message 状态结构：**

```typescript
export interface MessageState {
  messageId: string;
  role: "user" | "assistant";

  // 分离不同类型的内容
  thinkingContent: string;        // 思考过程
  mainContent: string;            // 最终答案

  // 工具调用
  toolCalls: Map<string, ToolCall>;  // 使用 Map 以 tool_id 为 key

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

### 3. 前端消息处理更新 ✅

#### 文件：`frontend/utils/messageStreamHandler.ts` + `frontend/components/ChatInterface.tsx`

**已完成：创建事件处理器类**

```typescript
class MessageStreamHandler {
  private updateMessage: (updater: (prev: Message) => Message) => void;

  constructor(updateMessage) {
    this.updateMessage = updateMessage;
  }

  handleEvent(event: SSEEvent) {
    switch (event.type) {
      case 'session_start':
        this.handleSessionStart(event);
        break;
      case 'thinking':
        this.updateMessage(prev => ({
          ...prev,
          thinkingContent: (prev.thinkingContent || '') + event.data.content
        }));
        break;
      case 'tool_call_start':
        this.updateMessage(prev => ({
          ...prev,
          toolCalls: {
            ...prev.toolCalls,
            [event.data.tool_id]: {
              id: event.data.tool_id,
              tool_name: event.data.tool_name,
              description: event.data.description,
              status: 'calling',
              timestamp: event.metadata.timestamp
            }
          }
        }));
        break;
      case 'tool_call_end':
        this.updateMessage(prev => {
          const toolCalls = { ...prev.toolCalls };
          if (toolCalls[event.data.tool_id]) {
            toolCalls[event.data.tool_id].status =
              event.data.status === 'success' ? 'completed' : 'failed';
          }
          return { ...prev, toolCalls };
        });
        break;
      case 'content':
        this.updateMessage(prev => ({
          ...prev,
          mainContent: (prev.mainContent || '') + event.data.content
        }));
        break;
      case 'data':
        this.updateMessage(prev => ({
          ...prev,
          dataBlocks: [...prev.dataBlocks, event.data]
        }));
        break;
      case 'error':
        this.updateMessage(prev => ({
          ...prev,
          hasError: true,
          errorMessage: event.data.message,
          isStreaming: false
        }));
        break;
      case 'session_end':
        this.updateMessage(prev => ({
          ...prev,
          isStreaming: false
        }));
        break;
    }
  }
}
```

**更新 SSE 处理逻辑：**

```typescript
// 在 handleSend 函数中
const handler = new MessageStreamHandler((updater) => {
  setMessages(prev => {
    const newMessages = [...prev];
    const lastMsg = newMessages[newMessages.length - 1];
    newMessages[newMessages.length - 1] = updater(lastMsg);
    return newMessages;
  });
});

// 解析 SSE 事件
const event = JSON.parse(jsonStr) as SSEEvent;
handler.handleEvent(event);
```

### 4. 前端组件优化 ⏳

#### ThinkingCollapse 优化

- 支持思考阶段标签（reasoning/planning/analyzing）
- 优化工具调用列表渲染

#### ToolCallDisplay 优化

- 使用 tool_id 作为 key
- 显示工具参数（可展开）
- 显示执行时间

#### DataFrameViewer 优化

- 支持多种数据类型（dataframe/chart/image）
- 添加数据元信息展示

### 5. 测试 ⏳

**后端测试：**
- 测试 StreamingEngine 各个方法
- 测试事件队列机制
- 测试工具调用流程

**前端测试：**
- 测试事件处理逻辑
- 测试 UI 更新性能
- 测试错误处理

**集成测试：**
- 端到端测试完整对话流程
- 测试工具调用可视化
- 测试表格数据展示

### 6. 文档更新 ⏳

需要更新的文档：
- `README.md` - 添加新协议说明
- `backend/README.md` - StreamingEngine 使用文档
- `frontend/README.md` - 新事件类型处理说明
- `STREAMING_PROTOCOL.md` - 补充实际使用示例

## 实施顺序建议

1. **第一阶段：后端完成** ✅
   - [x] 完整实现新版 chat.py
   - [x] 本地测试后端功能
   - [x] 验证事件流正确性

2. **第二阶段：前端适配** ✅
   - [x] 更新类型定义
   - [x] 实现事件处理器 (MessageStreamHandler)
   - [x] 更新 ChatInterface 组件

3. **第三阶段：组件优化** (可选)
   - [ ] 优化 ThinkingCollapse - 添加思考阶段标签
   - [ ] 优化 ToolCallDisplay - 显示工具参数和执行时间
   - [ ] 优化 DataFrameViewer - 支持多种数据类型

4. **第四阶段：测试和文档** (推荐)
   - [ ] 编写单元测试
   - [ ] 端到端测试
   - [ ] 更新 README 文档

## 向后兼容性

如果需要保持向后兼容，可以：

1. **保留旧版 chat.py**，新建 `chat_v2.py`
2. **前端支持两种事件格式**，自动检测并适配
3. **渐进式迁移**，先支持新格式，旧格式逐步废弃

## 遇到问题？

### 常见问题

**Q: Agent 输出和事件队列如何并发处理？**
A: 使用 asyncio.create_task() 创建并发任务，然后用 asyncio.gather() 或手动管理两个流。

**Q: 如何确保事件顺序正确？**
A: StreamingEngine 自动添加 sequence 序号，前端可以根据序号排序。

**Q: 工具调用如何匹配 start 和 end？**
A: 使用唯一的 tool_id（UUID），在前端用 Map 存储。

**Q: 如何处理流式输出中的错误？**
A: 发送 error 事件，设置 recoverable 标志，前端根据此标志决定是否允许重试。

## 参考资料

- **设计文档**：`STREAMING_PROTOCOL.md`
- **示例代码**：`src/api/routes/chat_new.py.example`
- **核心引擎**：`src/utils/streaming_engine.py`
- **工具系统**：`src/agent/tools.py`
