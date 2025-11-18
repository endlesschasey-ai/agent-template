#!/usr/bin/env python3
"""
基本验证测试 (Basic Verification Test)

快速验证系统的核心功能是否正常工作
"""

import asyncio
import httpx
import sys
import time
from typing import Optional


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


class BVT:
    """基本验证测试类"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.passed = 0
        self.failed = 0

    def log_test(self, name: str):
        """记录测试开始"""
        print(f"\n{Colors.BLUE}[TEST]{Colors.RESET} {name}")

    def log_pass(self, message: str):
        """记录测试通过"""
        print(f"  {Colors.GREEN}✓{Colors.RESET} {message}")
        self.passed += 1

    def log_fail(self, message: str):
        """记录测试失败"""
        print(f"  {Colors.RED}✗{Colors.RESET} {message}")
        self.failed += 1

    def log_info(self, message: str):
        """记录信息"""
        print(f"  {Colors.YELLOW}ℹ{Colors.RESET} {message}")

    async def test_health_check(self):
        """测试健康检查"""
        self.log_test("健康检查")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/")
                if response.status_code == 200:
                    self.log_pass("服务正常运行")
                    return True
                else:
                    self.log_fail(f"服务返回状态码 {response.status_code}")
                    return False
        except Exception as e:
            self.log_fail(f"无法连接到服务: {e}")
            return False

    async def test_create_session(self):
        """测试创建会话"""
        self.log_test("创建会话")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/api/session/create")

                if response.status_code == 200:
                    data = response.json()
                    if "session_id" in data:
                        self.session_id = data["session_id"]
                        self.log_pass(f"会话创建成功: {self.session_id}")
                        return True
                    else:
                        self.log_fail("响应中缺少 session_id")
                        return False
                else:
                    self.log_fail(f"创建会话失败，状态码: {response.status_code}")
                    return False
        except Exception as e:
            self.log_fail(f"创建会话出错: {e}")
            return False

    async def test_sse_streaming(self):
        """测试 SSE 流式响应"""
        self.log_test("SSE 流式响应")

        if not self.session_id:
            self.log_fail("没有有效的会话 ID")
            return False

        try:
            payload = {
                "session_id": self.session_id,
                "content": "你好，请简单介绍一下你自己",
                "file_ids": []
            }

            event_count = 0
            has_thinking = False
            has_content = False
            has_session_end = False

            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    if response.status_code != 200:
                        self.log_fail(f"聊天请求失败，状态码: {response.status_code}")
                        return False

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            event_count += 1
                            data_str = line[6:]  # 移除 "data: " 前缀

                            try:
                                import json
                                event = json.loads(data_str)

                                # 检查事件类型
                                if event.get("type") == "thinking":
                                    has_thinking = True
                                elif event.get("type") == "content":
                                    has_content = True
                                elif event.get("type") == "session_end":
                                    has_session_end = True
                                    break  # 会话结束，停止读取

                                # 验证新协议格式
                                if "metadata" in event:
                                    if "request_id" not in event["metadata"]:
                                        self.log_fail("事件缺少 request_id")
                                    if "timestamp" not in event["metadata"]:
                                        self.log_fail("事件缺少 timestamp")

                            except json.JSONDecodeError:
                                # 忽略解析错误
                                pass

            # 验证结果
            if event_count > 0:
                self.log_pass(f"接收到 {event_count} 个事件")
            else:
                self.log_fail("未接收到任何事件")
                return False

            if has_thinking:
                self.log_pass("检测到 thinking 事件")
            else:
                self.log_info("未检测到 thinking 事件（可能模型直接输出）")

            if has_content:
                self.log_pass("检测到 content 事件")
            else:
                self.log_fail("未检测到 content 事件")
                return False

            if has_session_end:
                self.log_pass("检测到 session_end 事件")
            else:
                self.log_fail("未检测到 session_end 事件")
                return False

            return True

        except Exception as e:
            self.log_fail(f"SSE 流式响应测试出错: {e}")
            return False

    async def test_session_status(self):
        """测试会话状态查询"""
        self.log_test("会话状态查询")

        if not self.session_id:
            self.log_fail("没有有效的会话 ID")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/session/{self.session_id}/status"
                )

                if response.status_code == 200:
                    data = response.json()
                    self.log_pass(f"会话状态: {data}")
                    return True
                else:
                    self.log_fail(f"查询会话状态失败，状态码: {response.status_code}")
                    return False
        except Exception as e:
            self.log_fail(f"查询会话状态出错: {e}")
            return False

    async def run_all(self):
        """运行所有测试"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BLUE}基本验证测试 (BVT){Colors.RESET}")
        print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"\n目标服务: {self.base_url}\n")

        start_time = time.time()

        # 运行测试
        tests = [
            self.test_health_check(),
            self.test_create_session(),
            self.test_sse_streaming(),
            self.test_session_status(),
        ]

        for test in tests:
            await test

        end_time = time.time()
        duration = end_time - start_time

        # 打印总结
        print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BLUE}测试总结{Colors.RESET}")
        print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        print(f"  总耗时: {duration:.2f}s")
        print(f"  {Colors.GREEN}通过: {self.passed}{Colors.RESET}")
        print(f"  {Colors.RED}失败: {self.failed}{Colors.RESET}")
        print(f"  总计: {self.passed + self.failed}")

        if self.failed == 0:
            print(f"\n{Colors.GREEN}✓ 所有测试通过！{Colors.RESET}\n")
            return 0
        else:
            print(f"\n{Colors.RED}✗ 有 {self.failed} 个测试失败{Colors.RESET}\n")
            return 1


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="基本验证测试")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="后端服务地址 (默认: http://localhost:8000)"
    )
    args = parser.parse_args()

    bvt = BVT(base_url=args.url)
    exit_code = await bvt.run_all()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
