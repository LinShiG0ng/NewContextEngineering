"""
LLM驱动的智能上下文压缩模块

使用大语言模型（LLM）进行真正的语义理解和智能压缩
支持OpenAI、Anthropic Claude等多种LLM提供商
"""

import os
import time
import json
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from utils import count_tokens


class LLMCompressor:
    """
    基于大语言模型的智能压缩器

    通过LLM的语义理解能力，实现真正的智能压缩和信息提炼
    """

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3
    ):
        """
        初始化LLM压缩器

        Args:
            provider: LLM提供商 ("openai", "anthropic", "azure")
            model: 模型名称
            api_key: API密钥
            max_tokens: 压缩摘要的最大token数
            temperature: 生成温度（越低越确定）
        """
        self.provider = provider.lower()
        self.max_tokens = max_tokens
        self.temperature = temperature

        # 设置默认模型
        if model is None:
            if self.provider == "openai":
                model = "gpt-4o-mini"
            elif self.provider == "anthropic":
                model = "claude-3-5-haiku-20241022"
            else:
                model = "gpt-4o-mini"

        self.model = model

        # 初始化客户端
        if self.provider == "openai":
            self.client = AsyncOpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY")
            )
        elif self.provider == "anthropic":
            self.client = AsyncAnthropic(
                api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
            )
        else:
            raise ValueError(f"不支持的provider: {provider}")

        # 统计信息
        self.stats = {
            "compressions": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "total_time": 0
        }

    def _build_compression_prompt(
        self,
        messages: List[Dict],
        entities: Optional[Dict] = None,
        target_ratio: float = 0.7
    ) -> str:
        """
        构建压缩提示词

        Args:
            messages: 要压缩的消息列表
            entities: 提取的关键实体（可选）
            target_ratio: 目标压缩率

        Returns:
            压缩提示词
        """
        # 格式化消息
        formatted_messages = []
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", 0)

            formatted_messages.append(f"""
【消息 #{i}】
角色: {role}
时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}
内容:
{content}
""")

        conversation_text = "\n".join(formatted_messages)

        # 构建实体提示
        entity_hint = ""
        if entities:
            entity_items = []
            if entities.get("files"):
                entity_items.append(f"- 文件: {', '.join(entities['files'][:10])}")
            if entities.get("functions"):
                entity_items.append(f"- 函数: {', '.join(entities['functions'][:10])}")
            if entities.get("errors"):
                entity_items.append(f"- 错误: {', '.join(entities['errors'][:5])}")
            if entities.get("ip_addresses"):
                entity_items.append(f"- IP地址: {', '.join(entities['ip_addresses'][:5])}")
            if entities.get("tools"):
                entity_items.append(f"- 工具: {', '.join(entities['tools'][:5])}")
            if entities.get("vulnerabilities"):
                entity_items.append(f"- 漏洞: {', '.join(entities['vulnerabilities'][:5])}")

            if entity_items:
                entity_hint = f"""

关键实体参考（请确保在摘要中保留这些实体）：
{chr(10).join(entity_items)}
"""

        # 计算原始token数和目标token数
        original_tokens = sum(msg.get("tokens", count_tokens(msg.get("content", "")))
                             for msg in messages)
        target_tokens = int(original_tokens * (1 - target_ratio))

        prompt = f"""你是一个专业的上下文压缩专家，擅长从对话中提炼核心信息，保留关键内容。

# 任务
请将以下对话压缩成简洁的摘要，保留所有关键信息和上下文。

# 对话内容
{conversation_text}
{entity_hint}

# 压缩要求
1. **保留关键信息**：
   - 所有文件名、函数名、类名、变量名
   - 所有错误信息和异常
   - 所有IP地址、端口、漏洞名称、工具名称
   - 重要的决策和解决方案
   - 关键的代码片段（完整保留）

2. **压缩策略**：
   - 删除冗余和重复的内容
   - 合并相似的讨论点
   - 使用简洁的语言重新表述
   - 保持时间顺序和因果关系

3. **输出格式**：
   使用结构化的Markdown格式，包含：
   - 📌 核心主题
   - 🔑 关键实体（如果有）
   - 💬 重要讨论点（按时间顺序）
   - 💻 关键代码片段（如果有）
   - ⚠️  错误和解决方案（如果有）

4. **目标**：
   - 原始约 {original_tokens} tokens
   - 目标约 {target_tokens} tokens
   - 压缩率约 {target_ratio*100:.0f}%
   - 信息保留率 > 90%

# 输出摘要
请直接输出压缩后的摘要，不要包含任何解释或元信息。"""

        return prompt

    async def compress(
        self,
        messages: List[Dict],
        entities: Optional[Dict] = None,
        target_ratio: float = 0.7
    ) -> Dict:
        """
        使用LLM压缩对话

        Args:
            messages: 要压缩的消息列表
            entities: 提取的关键实体（可选）
            target_ratio: 目标压缩率 (0-1)

        Returns:
            压缩结果字典
        """
        start_time = time.time()

        print("\n" + "━" * 60)
        print("🤖 正在使用LLM执行智能压缩...")
        print(f"   模型: {self.model}")
        print(f"   提供商: {self.provider}")
        print("━" * 60 + "\n")

        # 计算原始token数
        original_tokens = sum(msg.get("tokens", count_tokens(msg.get("content", "")))
                             for msg in messages)

        # 构建提示词
        prompt = self._build_compression_prompt(messages, entities, target_ratio)

        print(f"📝 准备压缩 {len(messages)} 条消息 ({original_tokens:,} tokens)")
        print(f"🎯 目标压缩率: {target_ratio*100:.0f}%\n")

        try:
            # 调用LLM
            if self.provider == "openai":
                response = await self._compress_with_openai(prompt)
            elif self.provider == "anthropic":
                response = await self._compress_with_anthropic(prompt)
            else:
                raise ValueError(f"不支持的provider: {self.provider}")

            compressed_content = response["content"]
            input_tokens = response["input_tokens"]
            output_tokens = response["output_tokens"]
            cost = response["cost"]

            # 计算实际压缩率
            compressed_tokens = count_tokens(compressed_content)
            actual_ratio = 1 - (compressed_tokens / original_tokens) if original_tokens > 0 else 0

            # 创建压缩消息
            compressed_message = {
                "role": "system",
                "content": compressed_content,
                "timestamp": time.time(),
                "compressed": True,
                "llm_compressed": True,
                "original_count": len(messages),
                "tokens": compressed_tokens,
                "model": self.model
            }

            elapsed_time = time.time() - start_time

            # 更新统计
            self.stats["compressions"] += 1
            self.stats["total_input_tokens"] += input_tokens
            self.stats["total_output_tokens"] += output_tokens
            self.stats["total_cost"] += cost
            self.stats["total_time"] += elapsed_time

            print("━" * 60)
            print("✅ LLM压缩完成！")
            print("━" * 60 + "\n")

            print("📊 压缩效果:")
            print(f"  原始Tokens: {original_tokens:,}")
            print(f"  压缩后Tokens: {compressed_tokens:,}")
            print(f"  节省Tokens: {original_tokens - compressed_tokens:,} ({actual_ratio*100:.1f}%)")
            print(f"  输入Tokens: {input_tokens:,}")
            print(f"  输出Tokens: {output_tokens:,}")
            print(f"  成本: ${cost:.6f}")
            print(f"  耗时: {elapsed_time:.2f}秒\n")

            return {
                "compressed_message": compressed_message,
                "original_tokens": original_tokens,
                "compressed_tokens": compressed_tokens,
                "compression_ratio": actual_ratio,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
                "elapsed_time": elapsed_time,
                "model": self.model,
                "provider": self.provider
            }

        except Exception as e:
            print(f"\n❌ LLM压缩失败: {str(e)}\n")
            raise

    async def _compress_with_openai(self, prompt: str) -> Dict:
        """使用OpenAI API压缩"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        content = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        # 估算成本（根据模型）
        if "gpt-4o" in self.model:
            input_cost = input_tokens * 2.5 / 1_000_000
            output_cost = output_tokens * 10 / 1_000_000
        elif "gpt-4" in self.model:
            input_cost = input_tokens * 30 / 1_000_000
            output_cost = output_tokens * 60 / 1_000_000
        else:  # gpt-3.5-turbo
            input_cost = input_tokens * 0.5 / 1_000_000
            output_cost = output_tokens * 1.5 / 1_000_000

        cost = input_cost + output_cost

        return {
            "content": content,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        }

    async def _compress_with_anthropic(self, prompt: str) -> Dict:
        """使用Anthropic Claude API压缩"""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        content = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # 估算成本
        if "opus" in self.model:
            input_cost = input_tokens * 15 / 1_000_000
            output_cost = output_tokens * 75 / 1_000_000
        elif "sonnet" in self.model:
            input_cost = input_tokens * 3 / 1_000_000
            output_cost = output_tokens * 15 / 1_000_000
        else:  # haiku
            input_cost = input_tokens * 0.8 / 1_000_000
            output_cost = output_tokens * 4 / 1_000_000

        cost = input_cost + output_cost

        return {
            "content": content,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        }

    def get_stats(self) -> Dict:
        """获取统计信息"""
        avg_time = self.stats["total_time"] / self.stats["compressions"] if self.stats["compressions"] > 0 else 0
        avg_cost = self.stats["total_cost"] / self.stats["compressions"] if self.stats["compressions"] > 0 else 0

        return {
            "compressions": self.stats["compressions"],
            "total_input_tokens": self.stats["total_input_tokens"],
            "total_output_tokens": self.stats["total_output_tokens"],
            "total_cost": self.stats["total_cost"],
            "total_time": self.stats["total_time"],
            "avg_time_per_compression": avg_time,
            "avg_cost_per_compression": avg_cost,
            "model": self.model,
            "provider": self.provider
        }


if __name__ == "__main__":
    import asyncio

    async def test_llm_compressor():
        """测试LLM压缩器"""
        print("🧪 测试LLM压缩器...\n")

        # 测试消息
        test_messages = [
            {
                "role": "user",
                "content": "我想创建一个Python数据分析项目，处理CSV文件",
                "timestamp": time.time() - 1000,
                "tokens": 20
            },
            {
                "role": "assistant",
                "content": """好的！我可以帮你创建。首先定义一个DataProcessor类：

```python
import pandas as pd

class DataProcessor:
    def __init__(self, filename):
        self.filename = filename
        self.data = None

    def load_data(self):
        try:
            self.data = pd.read_csv(self.filename)
            return True
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return False
```""",
                "timestamp": time.time() - 900,
                "tokens": 150
            },
            {
                "role": "user",
                "content": "好的，继续添加数据清洗功能",
                "timestamp": time.time() - 800,
                "tokens": 15
            },
            {
                "role": "assistant",
                "content": """添加clean_data方法处理缺失值和异常值：

```python
def clean_data(self):
    # 删除缺失值
    self.data = self.data.dropna()

    # 处理异常值
    for column in self.data.select_dtypes(include=['float64', 'int64']).columns:
        Q1 = self.data[column].quantile(0.25)
        Q3 = self.data[column].quantile(0.75)
        IQR = Q3 - Q1
        self.data = self.data[
            (self.data[column] >= Q1 - 1.5 * IQR) &
            (self.data[column] <= Q3 + 1.5 * IQR)
        ]
```""",
                "timestamp": time.time() - 700,
                "tokens": 120
            }
        ]

        # 创建压缩器
        compressor = LLMCompressor(
            provider="openai",  # 或 "anthropic"
            model="gpt-4o-mini"
        )

        # 执行压缩
        result = await compressor.compress(test_messages, target_ratio=0.7)

        print("\n📋 压缩结果:")
        print(result["compressed_message"]["content"])

        print("\n📈 统计信息:")
        stats = compressor.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

    # 运行测试
    asyncio.run(test_llm_compressor())
