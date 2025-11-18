# 快速启动指南

## 前置要求

- Python 3.11+
- Node.js 18+
- DashScope API Key（从 https://dashscope.aliyun.com/ 获取）

## 快速启动

### 1. 启动后端

```bash
cd backend

# 安装 uv（推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env，添加你的 DASHSCOPE_API_KEY

# 启动服务
uvicorn src.main:app --reload
```

**后端服务：** http://localhost:8000
**API 文档：** http://localhost:8000/docs

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动服务
npm run dev
```

**前端服务：** http://localhost:3000

## 核心功能

- 流式对话响应（SSE）
- 工具调用可视化
- 表格数据展示
- 会话持久化

## 自定义开发

### 添加新工具

在 `backend/src/agent/tools.py` 中：

```python
async def your_tool(self, param: str) -> dict:
    """工具描述"""
    tool_id = f"tool_{uuid.uuid4().hex[:8]}"

    # 发送开始事件
    await self._emit_event({
        "event_type": "tool_call_start",
        "tool_id": tool_id,
        "tool_name": "your_tool",
        "description": "工具描述"
    })

    # 执行逻辑
    result = {"data": "result"}

    # 发送结束事件
    await self._emit_event({
        "event_type": "tool_call_end",
        "tool_id": tool_id,
        "status": "success",
        "result": result
    })

    return result
```

然后在 `__init__` 中注册：
```python
self.register(self.your_tool)
```

### 修改 Agent 提示词

编辑 `backend/src/agent/agent.py` 中的 `SYSTEM_PROMPT`

## 常见问题

**Q: 后端启动失败？**
A: 检查是否配置了 `DASHSCOPE_API_KEY`

**Q: 前端无法连接后端？**
A: 确认后端运行在 http://localhost:8000

**Q: 如何重置数据库？**
A: 删除 `backend/data.db` 文件并重启

祝开发愉快！🎉
