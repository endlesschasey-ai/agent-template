# AI Agent Template - Frontend

基于 Next.js 15 + React 19 + TypeScript 的 AI Agent 前端应用。

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量（可选）

```bash
cp .env.example .env.local
```

编辑 `.env.local` 文件：

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

## 项目结构

```
app/
├── layout.tsx                # 根布局
├── page.tsx                  # 主页面
└── globals.css               # 全局样式

components/
├── ChatInterface.tsx         # 对话界面（核心组件）
├── ThinkingCollapse.tsx      # 思考过程折叠框
├── ToolCallDisplay.tsx       # 工具调用展示
└── DataFrameViewer.tsx       # 表格展示

types/
└── index.ts                  # TypeScript 类型定义
```

## 核心组件

### ChatInterface

主对话界面组件，包含以下功能：
- 流式对话响应（SSE）
- 思考过程展示（可折叠）
- 工具调用可视化
- 图片上传
- DataFrame 表格展示
- Markdown 渲染

### ThinkingCollapse

思考过程折叠框组件：
- 展示 Agent 的思考过程
- 显示工具调用列表
- 支持展开/折叠
- 流式更新

### ToolCallDisplay

工具调用展示组件：
- 优雅展示工具调用过程
- 状态动画（执行中/完成）
- 时间戳显示

### DataFrameViewer

表格数据展示组件：
- 展示结构化数据
- 响应式设计
- 支持大数据量

## 技术栈

- **Next.js 15** - React 框架
- **React 19** - UI 库
- **TypeScript** - 类型安全
- **TailwindCSS** - 样式框架
- **Lucide Icons** - 图标库
- **React Markdown** - Markdown 渲染
- **remark-gfm** - GitHub Flavored Markdown 支持

## 自定义开发

### 添加新组件

```tsx
// components/NewComponent.tsx
export default function NewComponent() {
  return <div>New Component</div>;
}
```

### 修改样式

使用 TailwindCSS 类名：

```tsx
<div className="bg-blue-500 text-white p-4 rounded-lg">
  内容
</div>
```

### 添加新的工具图标

在 `components/ToolCallDisplay.tsx` 中添加：

```tsx
const TOOL_INFO: Record<string, { icon: any; label: string; color: string }> = {
  your_tool_name: {
    icon: YourIcon,
    label: "工具中文名",
    color: "text-blue-500"
  },
  // ...
};
```

## 开发建议

### 类型检查

```bash
npx tsc --noEmit
```

### 代码格式化

```bash
npm run lint
```

### 构建生产版本

```bash
npm run build
npm start
```

## 部署

### Vercel 部署（推荐）

1. 将代码推送到 GitHub
2. 在 Vercel 中导入项目
3. 配置环境变量 `NEXT_PUBLIC_API_URL`
4. 自动部署

### 自托管部署

```bash
npm run build
npm start
```

使用 PM2 管理进程：

```bash
pm2 start npm --name "ai-agent-frontend" -- start
```

## 常见问题

### 无法连接后端

确认后端服务已启动：
- 后端地址：http://localhost:8000
- 检查 `.env.local` 中的 `NEXT_PUBLIC_API_URL` 配置

### SSE 连接中断

检查浏览器控制台的 EventSource 连接状态。确保后端正确配置 CORS。

### 样式不生效

确认 TailwindCSS 配置正确，运行 `npm run dev` 重新编译。

## 许可证

MIT License
