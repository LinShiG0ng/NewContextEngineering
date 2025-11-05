"""
上下文管理器模块

核心协调器，整合所有组件:
- 三层存储系统 (storage.py)
- AU2压缩算法 (compressor.py)
- 动态上下文注入 (injector.py)
- 长期知识库 (knowledge_base.py)

负责:
1. Token使用率实时监控
2. 自动触发压缩机制
3. 构建完整上下文
4. 性能统计
"""

import time
from typing import Dict, List, Optional
import asyncio

from storage import LayeredStorage
from compressor import AU2Compressor
from hybrid_compressor import HybridCompressor
from injector import ContextInjector
from knowledge_base import KnowledgeBase
from utils import count_tokens, count_messages_tokens, format_message
from config import (
    MAX_TOKENS,
    WARNING_THRESHOLD,
    ERROR_THRESHOLD,
    AUTO_COMPACT_THRESHOLD,
    WORKSPACE_DIR,
    USE_LLM_COMPRESSION,
    LLM_COMPRESSION_PROVIDER,
    LLM_COMPRESSION_MODEL,
    HYBRID_LLM_THRESHOLD
)


class ContextManager:
    """
    上下文管理器

    协调所有上下文工程组件，提供统一的接口
    """

    def __init__(self,
                 max_tokens: int = MAX_TOKENS,
                 warning_threshold: float = WARNING_THRESHOLD,
                 error_threshold: float = ERROR_THRESHOLD,
                 auto_compact_threshold: float = AUTO_COMPACT_THRESHOLD,
                 workspace: str = WORKSPACE_DIR):
        """
        初始化上下文管理器

        Args:
            max_tokens: 最大token限制
            warning_threshold: 警告阈值 (0.6 = 60%)
            error_threshold: 错误阈值 (0.8 = 80%)
            auto_compact_threshold: 自动压缩阈值 (0.92 = 92%)
            workspace: 工作空间目录
        """
        self.max_tokens = max_tokens
        self.warning_threshold = warning_threshold
        self.error_threshold = error_threshold
        self.auto_compact_threshold = auto_compact_threshold

        # 初始化各组件
        self.storage = LayeredStorage(workspace=workspace)

        # 根据配置选择压缩器
        if USE_LLM_COMPRESSION:
            self.compressor = HybridCompressor(
                use_llm=True,
                llm_provider=LLM_COMPRESSION_PROVIDER,
                llm_model=LLM_COMPRESSION_MODEL,
                llm_threshold=HYBRID_LLM_THRESHOLD
            )
            print(f"🤖 使用混合压缩系统 (LLM: {LLM_COMPRESSION_PROVIDER}/{LLM_COMPRESSION_MODEL})")
        else:
            self.compressor = AU2Compressor()
            print("📊 使用规则压缩系统 (AU2)")

        self.injector = ContextInjector()
        self.knowledge_base = KnowledgeBase()

        # 统计信息
        self.stats = {
            "total_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "system_messages": 0,
            "compressions": 0,
            "total_tokens_saved": 0,
            "avg_compression_ratio": 0.0,
            "injections": 0
        }

        # 系统消息（知识库）
        self.system_context = None
        self._load_system_context()

        # 保留的system prompts（来自压缩，永不压缩）
        self.preserved_system_prompts = []

    def _load_system_context(self):
        """
        加载系统上下文（从知识库）
        """
        try:
            self.system_context = self.knowledge_base.to_context_message(max_items=3)
        except Exception as e:
            print(f"⚠️  加载系统上下文失败: {e}")
            self.system_context = None

    async def add_message(self, role: str, content: str) -> Dict:
        """
        添加新消息到上下文

        自动检查是否需要压缩

        Args:
            role: 消息角色 (user/assistant/system)
            content: 消息内容

        Returns:
            操作结果字典
        """
        # 格式化消息
        message = format_message(role, content)

        # 添加到存储
        self.storage.add_to_short_term(message)

        # 更新统计
        self.stats["total_messages"] += 1
        if role == "user":
            self.stats["user_messages"] += 1
        elif role == "assistant":
            self.stats["assistant_messages"] += 1
        elif role == "system":
            self.stats["system_messages"] += 1

        # 计算当前使用率
        usage = self.calculate_usage()

        result = {
            "success": True,
            "message": message,
            "usage": usage,
            "compressed": False
        }

        # 检查是否需要自动压缩
        if usage >= self.auto_compact_threshold:
            print(f"\n⚠️  Token使用率达到 {usage*100:.0f}%，触发自动压缩！\n")
            compression_result = await self.compress_if_needed()
            result["compressed"] = True
            result["compression"] = compression_result

        return result

    def calculate_usage(self) -> float:
        """
        计算当前token使用率

        Returns:
            使用率 (0-1)
        """
        total_tokens = self.storage.get_total_tokens()

        # 加上系统上下文
        if self.system_context:
            total_tokens += self.system_context.get("tokens", 0)

        usage = total_tokens / self.max_tokens if self.max_tokens > 0 else 0
        return min(usage, 1.0)

    async def compress_if_needed(self, force: bool = False) -> Dict:
        """
        检查并执行压缩（如果需要）

        Args:
            force: 是否强制压缩

        Returns:
            压缩结果字典
        """
        usage = self.calculate_usage()

        # 判断是否需要压缩
        if not force and usage < self.auto_compact_threshold:
            return {
                "compressed": False,
                "reason": "未达到压缩阈值",
                "usage": usage
            }

        # 获取所有消息
        all_messages = self.storage.get_all_messages()

        if len(all_messages) < 3:
            return {
                "compressed": False,
                "reason": "消息数量太少",
                "message_count": len(all_messages)
            }

        # 执行压缩
        compression_result = await self.compressor.compress(all_messages)

        # 保存system prompts（如果存在）
        if compression_result.get("system_prompts"):
            self.preserved_system_prompts = compression_result["system_prompts"]
            print(f"🔒 {len(self.preserved_system_prompts)} 个System Prompt已保护，不会被压缩\n")

        # 更新存储
        # 清空短期和中期存储
        self.storage.clear_short_term()
        self.storage.mid_term.clear()

        # 添加压缩后的消息到中期存储
        self.storage.add_compressed_to_mid_term(compression_result["compressed_message"])

        # 更新统计
        self.stats["compressions"] += 1
        self.stats["total_tokens_saved"] += (
            compression_result["original_tokens"] - compression_result["compressed_tokens"]
        )

        # 计算平均压缩率
        if self.stats["compressions"] > 0:
            self.stats["avg_compression_ratio"] = compression_result["compression_ratio"]

        # 更新知识库（保存关键实体）
        if compression_result.get("entities"):
            self.knowledge_base.update({
                "entities": compression_result["entities"]
            })

        return {
            "compressed": True,
            "original_tokens": compression_result["original_tokens"],
            "compressed_tokens": compression_result["compressed_tokens"],
            "saved_tokens": compression_result["original_tokens"] - compression_result["compressed_tokens"],
            "compression_ratio": compression_result["compression_ratio"],
            "quality": compression_result["quality"],
            "new_usage": self.calculate_usage()
        }

    async def get_context(self, current_query: Optional[str] = None) -> List[Dict]:
        """
        构建完整的上下文（用于发送给LLM）

        Args:
            current_query: 当前查询（用于动态注入）

        Returns:
            完整的消息列表
        """
        context = []

        # 0. 首先添加保留的system prompts（如果存在，永远在最前面）
        if self.preserved_system_prompts:
            context.extend(self.preserved_system_prompts)

        # 1. 添加系统上下文（知识库）
        if self.system_context:
            context.append(self.system_context)

        # 2. 添加中期存储（压缩后的历史）
        mid_term = self.storage.get_mid_term()
        context.extend(mid_term)

        # 3. 添加短期存储（最近的完整消息）
        short_term = self.storage.get_short_term()
        context.extend(short_term)

        # 4. 如果有当前查询，进行动态注入
        if current_query:
            # 获取完整历史用于检索
            full_history = self.storage.get_all_messages()

            # 动态注入相关上下文
            context = await self.injector.inject_context(
                query=current_query,
                base_context=context,
                full_history=full_history
            )

            # 更新统计
            self.stats["injections"] = self.injector.stats["injections"]

        return context

    def get_statistics(self) -> Dict:
        """
        获取完整的统计信息

        Returns:
            统计信息字典
        """
        current_usage = self.calculate_usage()
        current_tokens = self.storage.get_total_tokens()

        stats = {
            "💬 对话统计": {
                "总消息数": self.stats["total_messages"],
                "用户消息": self.stats["user_messages"],
                "助手消息": self.stats["assistant_messages"],
                "当前Token使用": f"{current_tokens:,} / {self.max_tokens:,} ({current_usage*100:.0f}%)"
            },
            "🔄 压缩统计": {
                "压缩次数": self.stats["compressions"],
                "总节省Tokens": f"{self.stats['total_tokens_saved']:,}",
                "平均压缩率": f"{self.stats['avg_compression_ratio']*100:.1f}%"
            },
            "🏗️ 存储结构": self.storage.get_statistics(),
            "💉 注入统计": self.injector.get_statistics() if self.stats["injections"] > 0 else {"注入次数": 0},
            "📚 知识库": self.knowledge_base.get_statistics()
        }

        return stats

    def reset(self):
        """
        重置上下文管理器（保留知识库）
        """
        self.storage.reset()

        self.stats = {
            "total_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "system_messages": 0,
            "compressions": 0,
            "total_tokens_saved": 0,
            "avg_compression_ratio": 0.0,
            "injections": 0
        }

        # 清除保留的system prompts
        self.preserved_system_prompts = []

        # 重新加载系统上下文
        self._load_system_context()

        print("✅ 上下文已重置")

    def export_history(self, output_path: Optional[str] = None) -> str:
        """
        导出对话历史

        Args:
            output_path: 输出路径

        Returns:
            导出的文件路径
        """
        return self.storage.export_history(output_path)

    def get_usage_status(self) -> Dict:
        """
        获取当前使用状态（用于显示）

        Returns:
            状态字典
        """
        usage = self.calculate_usage()

        if usage >= self.error_threshold:
            status = "error"
            emoji = "🔴"
            message = "警告"
        elif usage >= self.warning_threshold:
            status = "warning"
            emoji = "⚠️ "
            message = "警告"
        else:
            status = "normal"
            emoji = "✅"
            message = "正常"

        return {
            "usage": usage,
            "percentage": f"{usage*100:.0f}%",
            "status": status,
            "emoji": emoji,
            "message": message,
            "current_tokens": self.storage.get_total_tokens(),
            "max_tokens": self.max_tokens
        }


async def test_context_manager():
    """
    测试上下文管理器
    """
    print("🧪 测试上下文管理器...\n")

    # 创建管理器（使用较小的限制以快速测试）
    manager = ContextManager(max_tokens=2000)

    # 测试1: 添加消息
    print("=" * 60)
    print("测试1: 添加消息并监控使用率")
    print("=" * 60)

    test_messages = [
        ("user", "你好，我想创建一个Python项目"),
        ("assistant", "好的，我来帮你创建项目结构..."),
        ("user", "需要包含数据处理功能"),
        ("assistant", "明白，添加DataProcessor类..." + "这是一段很长的回复" * 20),
        ("user", "继续添加更多功能"),
        ("assistant", "好的，添加分析功能..." + "详细的实现代码" * 30),
    ]

    for i, (role, content) in enumerate(test_messages, 1):
        result = await manager.add_message(role, content)
        status = manager.get_usage_status()

        print(f"\n消息 {i}: {role}")
        print(f"  使用率: {status['percentage']} {status['emoji']} {status['message']}")
        print(f"  Token: {status['current_tokens']} / {status['max_tokens']}")

        if result.get("compressed"):
            print(f"  🔄 触发了自动压缩!")
            print(f"  节省: {result['compression']['saved_tokens']} tokens")

        # 添加延迟以便观察
        await asyncio.sleep(0.1)

    # 测试2: 获取上下文
    print("\n" + "=" * 60)
    print("测试2: 构建上下文")
    print("=" * 60)

    context = await manager.get_context("之前的DataProcessor怎么实现的？")
    print(f"上下文消息数: {len(context)}")

    for i, msg in enumerate(context, 1):
        role = msg.get("role", "unknown")
        tokens = msg.get("tokens", 0)
        compressed = msg.get("compressed", False)
        injected = msg.get("injected", False)

        tags = []
        if compressed:
            tags.append("压缩")
        if injected:
            tags.append("注入")

        tag_str = f" [{', '.join(tags)}]" if tags else ""
        print(f"{i}. {role}{tag_str}: {tokens} tokens")

    # 测试3: 统计信息
    print("\n" + "=" * 60)
    print("测试3: 统计信息")
    print("=" * 60)

    from utils import print_statistics
    stats = manager.get_statistics()
    print_statistics(stats)

    print("✅ 上下文管理器测试完成！")


if __name__ == "__main__":
    asyncio.run(test_context_manager())
