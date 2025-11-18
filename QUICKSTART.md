# 快速启动指南

## 前置要求

- Python 3.11+
- Node.js 18+
- DashScope API Key（从 https://dashscope.aliyun.com/ 获取）

## 5 分钟快速启动

### 1. 启动后端

```bash
# 进入后端目录
cd template/backend

# 安装 uv（如果没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env，添加你的 DASHSCOPE_API_KEY

# 启动后端服务
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**后端服务：** http://localhost:8000
**API 文档：** http://localhost:8000/docs

### 2. 启动前端

打开新终端：

```bash
# 进入前端目录
cd template/frontend

# 安装依赖
npm install

# 启动前端服务
npm run dev
```

**前端服务：** http://localhost:3000

### 3. 开始使用

1. 打开浏览器访问 http://localhost:3000
2. 开始对话！
3. 尝试上传图片（点击 📎 按钮）
4. 点击"思考过程"查看 Agent 的工作流程

## 项目结构

```
template/
├── README.md                  # 项目总览
├── QUICKSTART.md             # 本文件
├── backend/                  # 后端服务
│   ├── src/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置
│   │   ├── db/              # 数据库
│   │   ├── models/          # 数据模型
│   │   ├── api/routes/      # API 路由
│   │   ├── services/        # 业务逻辑
│   │   ├── agent/           # Agent 配置
│   │   └── utils/           # 工具函数
│   ├── pyproject.toml       # Python 依赖
│   ├── .env.example         # 环境变量示例
│   └── README.md            # 后端文档
└── frontend/                # 前端应用
    ├── app/                 # Next.js 页面
    ├── components/          # React 组件
    ├── types/               # TypeScript 类型
    ├── package.json         # Node 依赖
    ├── .env.example         # 环境变量示例
    └── README.md            # 前端文档
```

## 核心功能

### 对话功能
- ✅ 流式响应（SSE）
- ✅ Markdown 渲染
- ✅ 代码高亮

### 思考过程展示
- ✅ 可折叠的思考过程
- ✅ 工具调用可视化
- ✅ 实时状态更新

### 工具系统
- ✅ `finalize_answer` - 输出最终答案
- ✅ `display_table` - 展示表格数据

### 文件上传
- ✅ 图片上传（JPG/PNG）
- ✅ 文件预览
- ✅ 数据库存储

### 数据持久化
- ✅ SQLite 数据库
- ✅ 会话管理
- ✅ 消息历史

## 自定义开发

### 添加新工具

**后端** (`backend/src/agent/tools.py`):
```python
async def your_tool(self, param: str) -> dict:
    """工具描述"""
    # 实现逻辑
    return {"result": "success"}
```

**前端** (`frontend/components/ToolCallDisplay.tsx`):
```typescript
const TOOL_INFO = {
  your_tool: {
    icon: YourIcon,
    label: "工具名称",
    color: "text-blue-500"
  }
};
```

### 修改 Agent 行为

编辑 `backend/src/agent/agent.py` 中的 `SYSTEM_PROMPT`。

### 修改样式

编辑 `frontend/app/globals.css` 或使用 TailwindCSS 类名。

## 常见问题

**Q: 后端启动失败？**
A: 检查是否配置了 `DASHSCOPE_API_KEY` 环境变量。

**Q: 前端无法连接后端？**
A: 确认后端服务已启动在 http://localhost:8000，检查 CORS 配置。

**Q: 数据库在哪里？**
A: 默认在 `backend/data.db`，可通过 `DATABASE_URL` 修改。

**Q: 如何重置数据库？**
A: 删除 `backend/data.db` 文件，重启后端会自动重新创建。

## 下一步

- 📖 阅读 [完整文档](README.md)
- 🔧 查看 [后端文档](backend/README.md)
- 🎨 查看 [前端文档](frontend/README.md)
- 🚀 开始自定义开发！

## 技术支持

遇到问题？
- 查看 API 文档：http://localhost:8000/docs
- 检查浏览器控制台
- 查看后端日志

祝开发愉快！🎉
