"""
LLM API统一调用接口模块

支持多种LLM API提供商:
- OpenAI (GPT-3.5/4)
- Anthropic (Claude)
- Ollama (本地模型)
- 自定义API (兼容OpenAI格式)

提供统一的接口抽象和错误处理
"""

import asyncio
import time
from typing import Dict, List, Optional, AsyncIterator
import sys

# 尝试导入各个API客户端
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  openai库未安装（安装: pip install openai）")

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  anthropic库未安装（安装: pip install anthropic）")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("⚠️  httpx库未安装（安装: pip install httpx）")

from utils import count_tokens, count_messages_tokens


class LLMClient:
    """
    统一的LLM客户端接口

    支持多种API提供商的统一调用
    """

    def __init__(self, config: Dict):
        """
        初始化LLM客户端

        Args:
            config: 配置字典，包含provider, api_key, model等
        """
        self.provider = config.get("provider", "openai")
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.max_tokens = config.get("max_tokens", 8000)
        self.temperature = config.get("temperature", 0.7)
        self.timeout = config.get("timeout", 60)
        self.max_retries = config.get("max_retries", 3)

        self.client = None
        self._init_client()

    def _init_client(self):
        """
        根据provider初始化对应的客户端
        """
        try:
            if self.provider == "openai":
                if not OPENAI_AVAILABLE:
                    raise ImportError("openai库未安装")

                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url

                self.client = AsyncOpenAI(**kwargs)

            elif self.provider == "anthropic":
                if not ANTHROPIC_AVAILABLE:
                    raise ImportError("anthropic库未安装")

                self.client = AsyncAnthropic(api_key=self.api_key)

            elif self.provider == "ollama":
                if not OPENAI_AVAILABLE:
                    raise ImportError("openai库未安装（Ollama使用OpenAI兼容接口）")

                # Ollama使用OpenAI兼容的API
                self.client = AsyncOpenAI(
                    base_url=self.base_url or "http://localhost:11434/v1",
                    api_key="ollama"  # Ollama不需要真实的API key
                )

            elif self.provider == "custom":
                if not OPENAI_AVAILABLE:
                    raise ImportError("openai库未安装")

                # 自定义API（假设兼容OpenAI格式）
                self.client = AsyncOpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key or "custom"
                )

            else:
                raise ValueError(f"不支持的provider: {self.provider}")

        except Exception as e:
            print(f"❌ 初始化{self.provider}客户端失败: {e}")
            self.client = None

    async def chat(self, messages: List[Dict], stream: bool = True,
                   max_output_tokens: Optional[int] = None) -> str:
        """
        发送对话请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            stream: 是否使用流式输出
            max_output_tokens: 最大输出token数

        Returns:
            模型响应内容

        Raises:
            Exception: API调用失败
        """
        if not self.client:
            raise Exception("客户端未初始化")

        # 清理消息格式（移除自定义字段）
        clean_messages = []
        for msg in messages:
            clean_msg = {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }
            clean_messages.append(clean_msg)

        # 根据provider调用相应的方法
        try:
            if self.provider == "anthropic":
                return await self._chat_anthropic(clean_messages, stream, max_output_tokens)
            else:
                # OpenAI格式（包括ollama和custom）
                return await self._chat_openai(clean_messages, stream, max_output_tokens)

        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")

    async def _chat_openai(self, messages: List[Dict], stream: bool,
                           max_output_tokens: Optional[int]) -> str:
        """
        OpenAI格式的API调用

        Args:
            messages: 消息列表
            stream: 是否流式输出
            max_output_tokens: 最大输出token数

        Returns:
            响应内容
        """
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": stream
        }

        if max_output_tokens:
            params["max_tokens"] = max_output_tokens

        if stream:
            # 流式输出
            response_text = ""
            async for chunk in await self.client.chat.completions.create(**params):
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    response_text += content

            print()  # 换行
            return response_text
        else:
            # 非流式输出
            response = await self.client.chat.completions.create(**params)
            return response.choices[0].message.content

    async def _chat_anthropic(self, messages: List[Dict], stream: bool,
                              max_output_tokens: Optional[int]) -> str:
        """
        Anthropic API调用

        Args:
            messages: 消息列表
            stream: 是否流式输出
            max_output_tokens: 最大输出token数

        Returns:
            响应内容
        """
        # Anthropic的消息格式需要分离system消息
        system_message = ""
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message += msg["content"] + "\n"
            else:
                user_messages.append(msg)

        params = {
            "model": self.model,
            "messages": user_messages,
            "temperature": self.temperature,
            "max_tokens": max_output_tokens or 2000
        }

        if system_message:
            params["system"] = system_message.strip()

        if stream:
            # 流式输出
            response_text = ""
            async with self.client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    print(text, end="", flush=True)
                    response_text += text

            print()  # 换行
            return response_text
        else:
            # 非流式输出
            response = await self.client.messages.create(**params)
            return response.content[0].text

    async def test_connection(self) -> bool:
        """
        测试API连接

        Returns:
            连接是否成功
        """
        if not self.client:
            print("❌ 客户端未初始化")
            return False

        try:
            print(f"🔄 测试{self.provider}连接...")

            # 发送简单测试消息
            test_messages = [
                {"role": "user", "content": "Hi"}
            ]

            response = await self.chat(test_messages, stream=False)

            if response:
                print(f"✅ 连接成功！模型响应: {response[:50]}...")
                return True
            else:
                print("❌ 连接失败：无响应")
                return False

        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    def get_model_info(self) -> Dict:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream_support": True
        }

    def count_tokens(self, text: str) -> int:
        """
        计算token数量

        Args:
            text: 文本内容

        Returns:
            token数量
        """
        return count_tokens(text, self.model)

    def count_messages_tokens(self, messages: List[Dict]) -> int:
        """
        计算消息列表的token数量

        Args:
            messages: 消息列表

        Returns:
            总token数
        """
        return count_messages_tokens(messages, self.model)

    async def chat_with_retry(self, messages: List[Dict], stream: bool = True,
                              max_retries: Optional[int] = None) -> str:
        """
        带重试机制的对话请求

        Args:
            messages: 消息列表
            stream: 是否流式输出
            max_retries: 最大重试次数

        Returns:
            响应内容
        """
        max_retries = max_retries or self.max_retries
        last_error = None

        for attempt in range(max_retries):
            try:
                return await self.chat(messages, stream)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"\n⚠️  请求失败，{wait_time}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"\n❌ 达到最大重试次数")

        raise Exception(f"API调用失败（已重试{max_retries}次）: {last_error}")


class MockLLMClient(LLMClient):
    """
    模拟LLM客户端（用于测试，无需真实API）
    """

    def __init__(self, config: Dict):
        self.provider = "mock"
        self.model = "mock-model"
        self.max_tokens = config.get("max_tokens", 8000)
        self.client = "mock"

    async def chat(self, messages: List[Dict], stream: bool = True,
                   max_output_tokens: Optional[int] = None) -> str:
        """
        模拟对话响应
        """
        # 模拟延迟
        await asyncio.sleep(0.5)

        # 生成简单的模拟响应
        last_message = messages[-1]["content"] if messages else ""

        responses = [
            f"这是一个模拟响应，针对你的问题：{last_message[:30]}...",
            "我理解你的需求，让我们一步步来解决这个问题。",
            "根据上下文，我建议采用以下方法...",
            "这是一个有趣的问题！让我详细解释一下。"
        ]

        import random
        response = random.choice(responses)

        if stream:
            # 模拟流式输出
            for char in response:
                print(char, end="", flush=True)
                await asyncio.sleep(0.02)
            print()

        return response

    async def test_connection(self) -> bool:
        """
        模拟连接测试
        """
        print("✅ Mock客户端连接成功")
        return True

    def get_model_info(self) -> Dict:
        """
        获取模拟模型信息
        """
        return {
            "provider": "mock",
            "model": "mock-model",
            "max_tokens": self.max_tokens,
            "note": "这是一个模拟客户端，用于测试"
        }


async def test_client():
    """
    测试LLM客户端
    """
    print("🧪 测试LLM客户端...\n")

    # 测试模拟客户端
    print("=" * 60)
    print("测试1: Mock客户端")
    print("=" * 60)

    mock_config = {"provider": "mock", "max_tokens": 8000}
    mock_client = MockLLMClient(mock_config)

    success = await mock_client.test_connection()
    print(f"连接测试: {'✅ 成功' if success else '❌ 失败'}\n")

    messages = [{"role": "user", "content": "你好，这是一个测试"}]
    print("发送测试消息...")
    response = await mock_client.chat(messages, stream=True)
    print(f"响应长度: {len(response)}字符\n")

    # 如果有真实配置，可以测试真实API
    # print("=" * 60)
    # print("测试2: 真实API（需要配置）")
    # print("=" * 60)
    # from config_loader import load_config
    # config = load_config()
    # if config.get("api_key"):
    #     client = LLMClient(config)
    #     await client.test_connection()

    print("✅ LLM客户端测试完成！")


if __name__ == "__main__":
    asyncio.run(test_client())
