# AI Agent Template - Backend

基于 FastAPI + Agno + 千问模型的 AI Agent 后端服务。

## 快速开始

### 1. 安装依赖

推荐使用 `uv`（比 pip 快 10-100 倍）：

```bash
# 安装 uv（如果没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖（自动创建虚拟环境）
uv sync
```

或使用传统的 pip：

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e .
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，添加 DashScope API Key：

```bash
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

获取 API Key：https://dashscope.aliyun.com/

### 3. 启动服务

```bash
# 使用 uv
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后：
- **API 文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

## 项目结构

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
    └── logger.py             # 日志工具
```

## API 接口

### 会话管理

- `POST /api/session/create` - 创建新会话
- `GET /api/session/list` - 获取会话列表
- `GET /api/session/{session_id}` - 获取会话详情

### 文件上传

- `POST /api/upload` - 上传图片文件

### 对话

- `POST /api/chat` - 发送消息（SSE 流式响应）

## 数据库

项目使用 SQLite 数据库，数据文件默认保存在 `data.db`。

### 表结构

**sessions**（会话表）
- session_id: 会话 ID（主键）
- title: 会话标题
- created_at: 创建时间
- last_activity_at: 最后活动时间

**messages**（消息表）
- message_id: 消息 ID（主键）
- session_id: 会话 ID（外键）
- role: 角色（user/assistant）
- content: 消息内容
- metadata: 元数据（JSON）
- created_at: 创建时间

**files**（文件表）
- file_id: 文件 ID（主键）
- session_id: 会话 ID（外键）
- message_id: 消息 ID（外键）
- filename: 文件名
- file_type: MIME 类型
- file_size: 文件大小
- file_data: 文件二进制数据（BLOB）
- uploaded_at: 上传时间

### 重置数据库

```bash
rm data.db
# 重启服务，数据库会自动重新创建
```

## 自定义 Agent

### 添加新工具

在 `src/agent/tools.py` 中的 `AgentToolkit` 类中添加新方法：

```python
async def your_tool_name(self, arg1: str, arg2: int) -> dict:
    """
    工具描述

    Args:
        arg1: 参数说明
        arg2: 参数说明

    Returns:
        返回值说明
    """
    # 工具逻辑
    return {"result": "success"}
```

然后在 `__init__` 方法中注册工具：

```python
self.register(self.your_tool_name)
```

### 修改系统提示词

编辑 `src/agent/agent.py` 中的 `SYSTEM_PROMPT` 变量。

## 开发建议

### 日志调试

设置环境变量 `LOG_LEVEL=DEBUG` 查看详细日志：

```bash
LOG_LEVEL=DEBUG uv run uvicorn src.main:app --reload
```

### 数据库调试

设置 `SQLALCHEMY_ECHO=true` 查看 SQL 语句：

```bash
SQLALCHEMY_ECHO=true uv run uvicorn src.main:app --reload
```

## 部署

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .

COPY src ./src
COPY .env .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产环境建议

1. 使用 PostgreSQL 替代 SQLite
2. 配置反向代理（Nginx/Caddy）
3. 启用 HTTPS
4. 配置日志收集
5. 使用环境变量管理敏感信息

## 许可证

MIT License
