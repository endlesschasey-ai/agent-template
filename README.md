# AI Agent Template

基于 **Agno + 千问模型 (Qwen)** 的 AI Agent 模板，支持流式对话、工具调用和数据展示。

## 功能特性

- ✅ 流式对话响应（SSE）
- ✅ 工具调用可视化
- ✅ 表格数据展示
- ✅ 会话持久化
- ✅ 消息历史记录

## 技术栈

**后端：**
- FastAPI + Agno + DashScope (Qwen)
- SQLAlchemy 2.0 + SQLite

**前端：**
- Next.js 15 + TypeScript + TailwindCSS

## 快速开始

详见 [QUICKSTART.md](./QUICKSTART.md)

## 项目结构

```
├── backend/              # FastAPI 后端
│   ├── src/
│   │   ├── agent/       # Agent 配置和工具
│   │   ├── api/         # API 路由
│   │   ├── db/          # 数据库配置
│   │   ├── models/      # 数据模型
│   │   ├── services/    # 业务逻辑
│   │   └── utils/       # 工具函数
│   └── pyproject.toml
│
└── frontend/            # Next.js 前端
    ├── app/            # 页面
    ├── components/     # 组件
    ├── utils/          # 工具函数
    └── types/          # TypeScript 类型

## 开发指南

### 添加新工具

在 `backend/src/agent/tools.py` 中定义新工具：

```python
async def your_tool(self, param: str) -> dict:
    """工具描述"""
    # 发送工具调用开始事件
    await self._emit_event({
        "event_type": "tool_call_start",
        "tool_id": "tool_xxx",
        "tool_name": "your_tool",
        "description": "工具描述"
    })

    # 执行逻辑...

    # 发送工具调用结束事件
    await self._emit_event({
        "event_type": "tool_call_end",
        "tool_id": "tool_xxx",
        "status": "success"
    })

    return result
```

然后在 `__init__` 中注册：`self.register(self.your_tool)`

## License

MIT
