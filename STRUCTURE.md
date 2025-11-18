# 项目结构说明

## 完整文件树

```
template/
├── README.md                           # 项目总览文档
├── QUICKSTART.md                       # 5分钟快速启动指南
├── STRUCTURE.md                        # 本文件 - 项目结构说明
│
├── backend/                            # 后端服务（FastAPI + Agno）
│   ├── README.md                       # 后端详细文档
│   ├── pyproject.toml                  # Python 项目配置（uv 格式）
│   ├── .env.example                    # 环境变量示例
│   ├── .gitignore                      # Git 忽略文件
│   │
│   └── src/                            # 源代码目录
│       ├── main.py                     # FastAPI 应用入口
│       ├── config.py                   # 环境配置（Pydantic Settings）
│       │
│       ├── db/                         # 数据库模块
│       │   ├── __init__.py
│       │   ├── base.py                 # SQLAlchemy Base
│       │   └── session.py              # 数据库会话管理
│       │
│       ├── models/                     # 数据模型
│       │   ├── __init__.py
│       │   ├── schema.py               # Pydantic 请求/响应模型
│       │   └── db/                     # SQLAlchemy ORM 模型
│       │       ├── __init__.py
│       │       ├── base.py             # Base 重导出
│       │       ├── session.py          # 会话表
│       │       ├── message.py          # 消息表
│       │       └── file.py             # 文件表
│       │
│       ├── api/                        # API 路由层
│       │   ├── __init__.py
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── session.py          # 会话管理 API
│       │       ├── upload.py           # 文件上传 API
│       │       └── chat.py             # 对话 API（SSE）
│       │
│       ├── services/                   # 业务逻辑层
│       │   ├── __init__.py
│       │   └── chat_service.py         # 聊天服务（封装数据库操作）
│       │
│       ├── agent/                      # Agent 模块
│       │   ├── __init__.py
│       │   ├── agent.py                # Agent 配置和创建
│       │   └── tools.py                # 工具定义（Toolkit）
│       │
│       └── utils/                      # 工具函数
│           ├── __init__.py
│           └── logger.py               # 日志配置
│
└── frontend/                           # 前端应用（Next.js 15）
    ├── README.md                       # 前端详细文档
    ├── package.json                    # Node 依赖配置
    ├── tsconfig.json                   # TypeScript 配置
    ├── next.config.ts                  # Next.js 配置
    ├── tailwind.config.ts              # TailwindCSS 配置
    ├── postcss.config.mjs              # PostCSS 配置
    ├── .eslintrc.json                  # ESLint 配置
    ├── .env.example                    # 环境变量示例
    ├── .gitignore                      # Git 忽略文件
    │
    ├── app/                            # Next.js App Router
    │   ├── layout.tsx                  # 根布局
    │   ├── page.tsx                    # 主页面
    │   └── globals.css                 # 全局样式
    │
    ├── components/                     # React 组件
    │   ├── ChatInterface.tsx           # 对话界面（核心组件）
    │   ├── ThinkingCollapse.tsx        # 思考过程折叠框
    │   ├── ToolCallDisplay.tsx         # 工具调用展示
    │   └── DataFrameViewer.tsx         # 表格展示
    │
    └── types/                          # TypeScript 类型定义
        └── index.ts                    # 全局类型定义
```

## 模块说明

### 后端模块

#### 核心模块
- **main.py**: FastAPI 应用入口，配置 CORS、注册路由、生命周期管理
- **config.py**: 使用 Pydantic Settings 管理环境变量

#### 数据层
- **db/**: 数据库会话管理，表初始化
- **models/db/**: SQLAlchemy ORM 模型（Session, Message, File）
- **models/schema.py**: Pydantic 请求/响应验证模型

#### API 层
- **api/routes/session.py**: 会话 CRUD 操作
- **api/routes/upload.py**: 文件上传处理
- **api/routes/chat.py**: SSE 流式对话接口

#### 业务层
- **services/chat_service.py**: 封装会话、消息、文件的数据库操作

#### Agent 层
- **agent/agent.py**: 创建和配置 Agno Agent
- **agent/tools.py**: 工具定义（Toolkit 模式）

### 前端模块

#### 页面
- **app/page.tsx**: 主页面，管理会话状态
- **app/layout.tsx**: 根布局，配置元数据

#### 核心组件
- **ChatInterface.tsx**: 对话界面，包含：
  - SSE 流式响应处理
  - 消息渲染（用户/助手）
  - 文件上传
  - 思考过程展示
  - 表格数据展示

- **ThinkingCollapse.tsx**: 思考过程折叠框
  - 展示思考内容
  - 显示工具调用列表
  - 支持展开/折叠

- **ToolCallDisplay.tsx**: 工具调用可视化
  - 状态动画（执行中/完成）
  - 工具图标和描述
  - 时间戳显示

- **DataFrameViewer.tsx**: 表格数据展示
  - 响应式设计
  - 列排序
  - 行悬停效果

#### 类型定义
- **types/index.ts**: 全局 TypeScript 类型
  - Message 相关类型
  - SSE Event 类型
  - Session 相关类型
  - File 相关类型
  - DataFrame 相关类型

## 数据流

### 对话流程

```
用户输入
  ↓
[ChatInterface] 发送消息
  ↓
[POST /api/chat] 接收请求
  ↓
[ChatService] 创建用户消息
  ↓
[Agent] 处理请求（工具调用）
  ↓
[SSE 流式响应] thinking → tool_call → tool_result → final_answer → done
  ↓
[ChatInterface] 解析 SSE 事件
  ↓
[React State] 更新消息列表
  ↓
[UI 渲染] 展示结果
```

### 文件上传流程

```
用户选择文件
  ↓
[ChatInterface] 暂存文件（预览）
  ↓
[发送消息时] 批量上传文件
  ↓
[POST /api/upload] 接收文件
  ↓
[ChatService] 存储文件到数据库
  ↓
[返回 file_id]
  ↓
[关联到消息] file_ids → message
```

## 数据库设计

### Session（会话表）
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    last_activity_at DATETIME NOT NULL
);
```

### Message（消息表）
```sql
CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata TEXT,  -- JSON: 工具调用、表格数据等
    created_at DATETIME NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);
```

### File（文件表）
```sql
CREATE TABLE files (
    file_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    message_id TEXT,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_data BLOB NOT NULL,  -- 图片二进制数据
    uploaded_at DATETIME NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE
);
```

## SSE 事件协议

| 事件类型 | 说明 | 示例 |
|---------|------|------|
| `thinking` | 思考过程 | `{"type": "thinking", "content": "正在分析..."}` |
| `tool_call` | 工具调用开始 | `{"type": "tool_call", "tool_id": "...", "tool_name": "..."}` |
| `tool_result` | 工具调用完成 | `{"type": "tool_result", "tool_id": "...", "status": "completed"}` |
| `final_answer` | 最终答案 | `{"type": "final_answer", "content": "这是答案..."}` |
| `dataframe_data` | 表格数据 | `{"type": "dataframe_data", "data": {...}}` |
| `done` | 流式输出完成 | `{"type": "done"}` |
| `error` | 错误 | `{"type": "error", "message": "错误信息"}` |

## 技术栈总结

### 后端
- **FastAPI** - 异步 Web 框架
- **Agno** - AI Agent 框架
- **DashScope** - 千问模型 API
- **SQLAlchemy 2.0** - ORM
- **SQLite** - 数据库
- **Pydantic** - 数据验证
- **aiosqlite** - 异步 SQLite 驱动
- **Pillow** - 图片处理

### 前端
- **Next.js 15** - React 框架
- **React 19** - UI 库
- **TypeScript** - 类型安全
- **TailwindCSS** - 样式框架
- **Lucide Icons** - 图标库
- **React Markdown** - Markdown 渲染
- **remark-gfm** - GitHub Flavored Markdown

## 关键设计模式

1. **分层架构**: API → Service → Database
2. **依赖注入**: 数据库会话通过参数传递
3. **事件驱动**: 工具调用通过事件队列通信
4. **流式响应**: SSE 实时推送数据
5. **乐观更新**: 前端先更新 UI，再发送请求

## 扩展建议

- [ ] 添加用户认证（JWT）
- [ ] 支持多模态输入（音频、视频）
- [ ] 添加 Redis 缓存
- [ ] 使用 PostgreSQL（生产环境）
- [ ] 添加消息搜索功能
- [ ] 支持会话分享
- [ ] 添加 Agent 性能监控
- [ ] 支持多语言（i18n）
