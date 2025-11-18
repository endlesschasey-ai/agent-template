"""测试 Dashscope API 连接"""
import asyncio
from agno.agent import Agent
from agno.models.dashscope import DashScope
from dotenv import load_dotenv
import os

load_dotenv()

async def test_dashscope():
    """测试 Dashscope API"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    print(f"API Key: {api_key[:10]}...")
    print(f"Base URL: {base_url}")
    print(f"模型: qwen-max")
    print("-" * 50)

    # 创建模型
    model = DashScope(
        id="qwen-max",  # 尝试不同的模型 ID
        base_url=base_url,
        api_key=api_key,
    )

    # 创建简单的 Agent
    agent = Agent(
        model=model,
        instructions="你是一个AI助手",
        markdown=True,
        debug_mode=True,
    )

    print("开始测试...")
    try:
        response = agent.run(input="你好，请简单回复", stream=False)
        print(f"\n✅ 成功! 响应: {response.content}")
    except Exception as e:
        print(f"\n❌ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dashscope())
