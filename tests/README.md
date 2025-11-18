# 测试文档

本目录包含 AI Agent 模板的测试用例。

## 测试结构

```
tests/
├── bvt.py                          # 基本验证测试（E2E）
└── README.md                       # 本文件

backend/tests/
├── __init__.py
├── test_streaming_engine.py        # StreamingEngine 单元测试
└── test_chat_api.py                # Chat API 集成测试

frontend/__tests__/
└── messageStreamHandler.test.ts    # MessageStreamHandler 单元测试
```

## 运行测试

### 1. 后端单元测试

**前提条件：**
- 已安装 Python 依赖（`uv sync` 或 `pip install -e .`）

**运行所有测试：**
```bash
cd backend
uv run pytest tests/ -v
```

**运行特定测试文件：**
```bash
# StreamingEngine 测试
uv run pytest tests/test_streaming_engine.py -v

# Chat API 测试
uv run pytest tests/test_chat_api.py -v
```

**查看测试覆盖率：**
```bash
uv run pytest tests/ --cov=src --cov-report=html
```

### 2. 前端单元测试

**前提条件：**
- 已安装 Node.js 依赖（`npm install`）
- 已配置 Jest（通常 Next.js 项目自带）

**运行测试：**
```bash
cd frontend

# 运行所有测试
npm test

# 运行特定测试
npm test messageStreamHandler

# 查看覆盖率
npm test -- --coverage
```

### 3. E2E 基本验证测试

**前提条件：**
- 后端服务已启动（`http://localhost:8000`）
- 已配置有效的 `DASHSCOPE_API_KEY`

**运行 BVT：**
```bash
# 从项目根目录运行
cd template
python tests/bvt.py

# 指定自定义后端地址
python tests/bvt.py --url http://localhost:8000
```

**BVT 测试内容：**
1. ✓ 健康检查 - 验证服务是否运行
2. ✓ 创建会话 - 测试会话创建功能
3. ✓ SSE 流式响应 - 测试聊天流式输出
4. ✓ 会话状态查询 - 测试会话管理

## 测试说明

### StreamingEngine 单元测试

**测试内容：**
- ✅ 8 种事件类型的生成和格式化
- ✅ 自动元数据管理（request_id、timestamp、sequence）
- ✅ 序列号自动递增
- ✅ 时间戳生成
- ✅ 边界情况（空内容、Unicode、大数据等）

**关键测试用例：**
```python
def test_session_start_event(self):
    """测试会话开始事件"""
    sse_data = self.engine.emit_session_start("session_abc")
    # 验证事件格式和内容

def test_thinking_event(self):
    """测试思考过程事件"""
    sse_data = self.engine.emit_thinking("正在分析问题...", stage="reasoning")
    # 验证思考事件

# ... 更多测试用例
```

### Chat API 集成测试

**测试内容：**
- ✅ 会话创建
- ✅ 基本对话流程
- ✅ 无效会话处理
- ✅ SSE 事件格式验证
- ✅ 新旧协议兼容性

**注意事项：**
- 某些测试需要有效的 DASHSCOPE_API_KEY
- 使用内存数据库进行测试，不影响生产数据

### MessageStreamHandler 单元测试

**测试内容：**
- ✅ 新协议事件处理（8 种事件类型）
- ✅ 旧协议事件处理（向后兼容）
- ✅ 累积更新测试
- ✅ SSE 行解析

**关键测试用例：**
```typescript
test('处理 thinking 事件', () => {
  const handler = new MessageStreamHandler(mockUpdateMessage, mockOnComplete);
  const event = { type: 'thinking', data: { content: '思考中...' }, ... };
  handler.handleEvent(event);
  expect(updatedMessage?.thinkingContent).toBe('思考中...');
});
```

### E2E 基本验证测试

**测试流程：**
1. 健康检查 → 验证服务启动
2. 创建会话 → 获取 session_id
3. 发送消息 → 验证 SSE 流式响应
4. 检查事件 → 验证事件类型和格式
5. 查询状态 → 验证会话管理

**示例输出：**
```
============================================================
基本验证测试 (BVT)
============================================================

[TEST] 健康检查
  ✓ 服务正常运行

[TEST] 创建会话
  ✓ 会话创建成功: session_abc123

[TEST] SSE 流式响应
  ✓ 接收到 15 个事件
  ✓ 检测到 thinking 事件
  ✓ 检测到 content 事件
  ✓ 检测到 session_end 事件

[TEST] 会话状态查询
  ✓ 会话状态: {...}

============================================================
测试总结
============================================================

  总耗时: 3.45s
  通过: 8
  失败: 0
  总计: 8

✓ 所有测试通过！
```

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -e .
          pip install pytest pytest-cov
      - name: Run tests
        run: cd backend && pytest tests/ -v

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd frontend && npm install
      - name: Run tests
        run: cd frontend && npm test
```

## 故障排查

### 后端测试失败

**问题：** `ImportError: No module named 'src'`
**解决：** 确保已安装项目依赖 `pip install -e .`

**问题：** `DASHSCOPE_API_KEY not found`
**解决：** 配置 `.env` 文件或设置环境变量

### 前端测试失败

**问题：** `Cannot find module '@/utils/messageStreamHandler'`
**解决：** 检查 `tsconfig.json` 中的路径配置

**问题：** Jest 配置错误
**解决：** 确保 `jest.config.js` 正确配置

### BVT 测试失败

**问题：** `无法连接到服务`
**解决：** 确保后端服务已启动在正确的端口

**问题：** `未检测到 content 事件`
**解决：** 检查 DASHSCOPE_API_KEY 是否有效

## 最佳实践

1. **测试前清理** - 删除测试数据库和临时文件
2. **隔离测试** - 每个测试应该独立，不依赖其他测试
3. **Mock 外部依赖** - 使用 Mock 对象替代真实 API 调用
4. **覆盖边界情况** - 测试空值、异常值、大数据等
5. **定期运行** - 在每次提交前运行测试

## 添加新测试

### 后端测试

1. 在 `backend/tests/` 中创建 `test_*.py` 文件
2. 使用 pytest 框架编写测试
3. 使用 fixtures 管理测试数据

### 前端测试

1. 在 `frontend/__tests__/` 中创建 `*.test.ts` 文件
2. 使用 Jest + React Testing Library
3. Mock 外部依赖（API、组件等）

## 参考资料

- [pytest 文档](https://docs.pytest.org/)
- [Jest 文档](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
