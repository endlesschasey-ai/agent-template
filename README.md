# AI Agent Template

基于 **Agno + 千问模型 (Qwen)** 的 AI Agent 模板，支持对话、工具调用、思考过程展示和图片上传。

## 🎉 最新更新

**v2.0 - StreamingEngine 重构** (已完成)

- ✨ **StreamingEngine** - 统一的流式输出引擎
  - 8 种标准化事件类型
  - 自动元数据管理（request_id、timestamp、sequence）
  - 完整的日志记录
- 🔄 **MessageStreamHandler** - 前端事件处理器
  - 自动协议检测（新旧兼容）
  - 类型安全的事件处理
  - 优化的状态管理
- 📚 **完整文档** - 协议设计和实施指南
  - [STREAMING_PROTOCOL.md](./STREAMING_PROTOCOL.md) - 协议规范
  - [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) - 实施指南

## 功能特性

### 核心功能
- ✅ 流式对话响应（SSE）- **采用新协议**
- ✅ 思考过程展示（可折叠）
- ✅ 工具调用可视化 - **带时间统计**
- ✅ 表格数据展示（DataFrame）
- ✅ 图片上传支持
- ✅ 会话持久化（SQLite）
- ✅ 消息历史记录
- ✅ 向后兼容（支持新旧协议）

### 技术栈

**后端：**
- FastAPI - 异步 Web 框架
- Agno - AI Agent 框架
- DashScope (Qwen) - 大语言模型
- SQLAlchemy 2.0 + SQLite - 数据库 ORM
- Pydantic - 数据验证

**前端：**
- Next.js 15 - React 框架
- TypeScript - 类型安全
- TailwindCSS - 样式框架
- Lucide Icons - 图标库
- React Markdown - Markdown 渲染

## 快速开始

### 1. 后端设置

```bash
cd template/backend

# 安装依赖（使用 uv，推荐）
uv sync

# 或使用 pip
pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env，添加 DASHSCOPE_API_KEY

# 启动后端服务
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**后端服务：** http://localhost:8000
**API 文档：** http://localhost:8000/docs

### 2. 前端设置

```bash
cd template/frontend

# 安装依赖
npm install

# 配置环境变量（可选）
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# 启动前端服务
npm run dev
```

**前端服务：** http://localhost:3000

## 项目结构

### 后端 (backend/)

```
src/
├── main.py                    # FastAPI 应用入口
├── config.py                  # 环境配置
├── db/
│   ├── base.py               # SQLAlchemy Base
│   └── session.py            # 数据库会话管理
├── models/
│   ├── db/                   # 数据库 ORM 模型
│   │   ├── session.py        # 会话表
│   │   ├── message.py        # 消息表
│   │   └── file.py           # 文件表
│   └── schema.py             # Pydantic 请求/响应模型
├── api/routes/               # API 路由
│   ├── session.py            # 会话管理
│   ├── upload.py             # 文件上传
│   └── chat.py               # 对话接口（SSE）
├── services/
│   └── chat_service.py       # 业务逻辑层
├── agent/
│   ├── agent.py              # Agent 配置
│   └── tools.py              # 工具定义
└── utils/
    ├── streaming_engine.py   # ⭐ 流式输出引擎（新）
    └── logger.py             # 日志工具
```

**核心文件：**
- `utils/streaming_engine.py` - StreamingEngine 核心实现
- `agent/tools.py` - 工具系统（已重构使用事件队列）
- `api/routes/chat.py` - 聊天接口（已重写使用新协议）
- `api/routes/chat_old.py` - 旧版备份

### 前端 (frontend/)

```
app/
├── layout.tsx                # 根布局
└── page.tsx                  # 主页面

components/
├── ChatInterface.tsx         # ⭐ 对话界面（已更新）
├── ThinkingCollapse.tsx      # 思考过程折叠框
├── ToolCallDisplay.tsx       # 工具调用展示
└── DataFrameViewer.tsx       # 表格展示

types/
└── index.ts                  # ⭐ TypeScript 类型定义（已扩展）

utils/
└── messageStreamHandler.ts   # ⭐ 消息流处理器（新）
```

**核心文件：**
- `utils/messageStreamHandler.ts` - MessageStreamHandler 类和工具函数
- `types/index.ts` - 完整的事件和消息类型定义
- `components/ChatInterface.tsx` - 使用新事件处理器

⭐ = 核心文件/已更新文件
```

## 数据库设计

### Session（会话表）
| 字段 | 类型 | 说明 |
|------|------|------|
| session_id | String (PK) | 会话唯一ID |
| title | String | 会话标题 |
| created_at | DateTime | 创建时间 |
| last_activity_at | DateTime | 最后活动时间 |

### Message（消息表）
| 字段 | 类型 | 说明 |
|------|------|------|
| message_id | String (PK) | 消息唯一ID |
| session_id | String (FK) | 所属会话ID |
| role | String | 角色（user/assistant） |
| content | Text | 消息内容 |
| metadata | Text (JSON) | 扩展数据（工具调用等） |
| created_at | DateTime | 创建时间 |

### File（文件表）
| 字段 | 类型 | 说明 |
|------|------|------|
| file_id | String (PK) | 文件唯一ID |
| session_id | String (FK) | 所属会话ID |
| message_id | String (FK) | 关联消息ID |
| filename | String | 文件名 |
| file_type | String | MIME 类型 |
| file_data | BLOB | 文件二进制数据 |
| uploaded_at | DateTime | 上传时间 |

## SSE 事件协议

后端通过 Server-Sent Events (SSE) 发送流式响应。系统支持**新旧两种协议格式**。

### 新协议（v2.0 推荐）

采用统一的事件格式，包含 `data` 和 `metadata` 字段：

```json
{
  "type": "thinking",
  "data": {
    "content": "正在分析问题...",
    "stage": "reasoning"
  },
  "metadata": {
    "request_id": "req_abc123",
    "timestamp": 1699999999999,
    "sequence": 1
  }
}
```

**8 种标准事件类型：**
1. **session_start** - 会话开始
2. **thinking** - 思考过程
3. **tool_call_start** - 工具调用开始
4. **tool_call_end** - 工具调用结束
5. **content** - 最终答案内容
6. **data** - 结构化数据
7. **error** - 错误信息
8. **session_end** - 会话结束

**详细文档：** [STREAMING_PROTOCOL.md](./STREAMING_PROTOCOL.md)

### 旧协议（向后兼容）

系统完全支持旧协议格式（不带 metadata），例如：

```json
{
  "type": "thinking",
  "content": "正在分析问题..."
}
```

**旧协议事件类型：** thinking, tool_call, tool_result, final_answer, dataframe_data, done, error

前端 `MessageStreamHandler` 会自动检测并处理两种格式，确保平滑迁移。

## 自定义开发

### 添加新工具

1. 在 `backend/src/agent/tools.py` 中定义工具函数：

```python
from agno.tools import tool

@tool
async def search_knowledge(query: str) -> str:
    """
    搜索知识库

    Args:
        query: 搜索关键词

    Returns:
        搜索结果
    """
    # 实现工具逻辑
    return f"搜索结果：{query}"
```

2. 在 `agent.py` 中注册工具：

```python
agent = Agent(
    model=model,
    tools=[search_knowledge],
    # ...
)
```

3. 在前端 `components/ToolCallDisplay.tsx` 中添加工具图标和描述：

```typescript
const TOOL_INFO: Record<string, { icon: any; label: string }> = {
  search_knowledge: {
    icon: Search,
    label: "搜索知识库"
  },
  // ...
}
```

### 扩展数据库模型

1. 在 `backend/src/models/db/` 中创建新模型
2. 在 `db/session.py` 的 `init_db()` 中导入模型
3. 重启后端服务自动创建表

### 自定义 Agent 行为

编辑 `backend/src/agent/agent.py` 中的 `SYSTEM_PROMPT` 来定制 Agent 的行为和角色设定。

## 环境变量

### 后端 (.env)
```bash
# 必填 - DashScope API Key
DASHSCOPE_API_KEY=sk-xxxxxxxx

# 可选 - 数据库路径
DATABASE_URL=sqlite:///./data.db

# 可选 - 日志级别
LOG_LEVEL=INFO

# 可选 - CORS 设置
CORS_ORIGINS=http://localhost:3000
```

### 前端 (.env.local)
```bash
# 可选 - 后端 API 地址
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 常见问题

### 后端相关

**Q: 如何获取 DashScope API Key？**
A: 访问 https://dashscope.aliyun.com/ 注册并获取 API Key。

**Q: 数据库文件在哪里？**
A: 默认在 `backend/data.db`，可通过 `DATABASE_URL` 环境变量修改。

**Q: 如何重置数据库？**
A: 删除 `data.db` 文件，重启后端服务会自动重新创建。

### 前端相关

**Q: 如何修改样式？**
A: 使用 TailwindCSS 类名，或在组件中使用 `className` 修改。

**Q: 如何支持更多文件类型？**
A: 修改 `components/ChatInterface.tsx` 中的 `accept` 属性和后端的文件处理逻辑。

## 测试

本项目包含完整的测试套件，确保代码质量和功能正确性。

### 后端测试

```bash
cd backend

# 运行所有测试
uv run pytest tests/ -v

# 运行特定测试
uv run pytest tests/test_streaming_engine.py -v

# 查看覆盖率
uv run pytest tests/ --cov=src --cov-report=html
```

**测试内容：**
- StreamingEngine 单元测试（所有事件类型）
- Chat API 集成测试
- SSE 协议格式验证

### 前端测试

```bash
cd frontend

# 安装依赖（如果还没安装）
npm install

# 运行测试
npm test

# 查看覆盖率
npm test -- --coverage
```

**测试内容：**
- MessageStreamHandler 事件处理
- 新旧协议兼容性
- SSE 行解析

### E2E 基本验证测试

```bash
# 确保后端服务已启动
cd template
python tests/bvt.py

# 指定自定义后端地址
python tests/bvt.py --url http://localhost:8000
```

**BVT 测试流程：**
1. ✓ 健康检查
2. ✓ 创建会话
3. ✓ SSE 流式响应
4. ✓ 会话状态查询

**详细文档：** 参见 [tests/README.md](./tests/README.md)

## 开发建议

1. **开发模式**：使用 `--reload` 启动后端，修改代码后自动重启
2. **日志调试**：设置 `LOG_LEVEL=DEBUG` 查看详细日志
3. **类型检查**：前端使用 `npm run type-check` 检查类型错误
4. **代码规范**：遵循 PEP 8（Python）和 ESLint（TypeScript）规范
5. **运行测试**：每次提交前运行测试套件

## 部署建议

### 后端部署
- 使用 Docker 容器化部署
- 配置反向代理（Nginx/Caddy）
- 使用 PostgreSQL 替代 SQLite（生产环境）
- 配置 HTTPS

### 前端部署
- 使用 Vercel/Netlify 一键部署
- 或使用 `npm run build && npm start` 自托管
- 配置环境变量指向生产后端 API

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
