"""
混合压缩模块

整合规则方法（AU2）和LLM方法，提供最佳的压缩效果
"""

import os
from typing import Dict, List, Optional

from compressor import AU2Compressor
from llm_compressor import LLMCompressor
from config import (
    TARGET_COMPRESSION_RATIO,
    USE_LLM_COMPRESSION,
    LLM_COMPRESSION_PROVIDER,
    LLM_COMPRESSION_MODEL,
    LLM_COMPRESSION_TEMPERATURE,
    LLM_COMPRESSION_MAX_TOKENS,
    HYBRID_LLM_THRESHOLD
)


class HybridCompressor:
    """
    混合压缩器

    根据场景智能选择使用规则方法或LLM方法：
    - 消息少：使用规则方法（快速、免费）
    - 消息多：使用LLM方法（质量高）
    - 可配置fallback策略
    """

    def __init__(
        self,
        use_llm: Optional[bool] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_threshold: int = HYBRID_LLM_THRESHOLD,
        fallback_on_error: bool = True
    ):
        """
        初始化混合压缩器

        Args:
            use_llm: 是否启用LLM（None则使用配置）
            llm_provider: LLM提供商
            llm_model: LLM模型
            llm_threshold: 使用LLM的消息数阈值
            fallback_on_error: LLM失败时是否回退到规则方法
        """
        # 读取配置
        self.use_llm = use_llm if use_llm is not None else USE_LLM_COMPRESSION
        self.llm_threshold = llm_threshold
        self.fallback_on_error = fallback_on_error

        # 初始化规则压缩器（始终可用）
        self.rule_compressor = AU2Compressor()

        # 初始化LLM压缩器（如果启用）
        self.llm_compressor = None
        if self.use_llm:
            try:
                provider = llm_provider or LLM_COMPRESSION_PROVIDER
                model = llm_model or LLM_COMPRESSION_MODEL

                # 检查API密钥
                if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
                    print("⚠️  警告: 未设置OPENAI_API_KEY，LLM压缩将不可用")
                    self.use_llm = False
                elif provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
                    print("⚠️  警告: 未设置ANTHROPIC_API_KEY，LLM压缩将不可用")
                    self.use_llm = False
                else:
                    self.llm_compressor = LLMCompressor(
                        provider=provider,
                        model=model,
                        temperature=LLM_COMPRESSION_TEMPERATURE,
                        max_tokens=LLM_COMPRESSION_MAX_TOKENS
                    )
                    print(f"✅ LLM压缩已启用: {provider}/{model}")
            except Exception as e:
                print(f"⚠️  LLM压缩器初始化失败: {e}")
                print("   将使用规则方法")
                self.use_llm = False

        # 统计信息
        self.stats = {
            "total_compressions": 0,
            "rule_compressions": 0,
            "llm_compressions": 0,
            "fallback_count": 0
        }

    async def compress(
        self,
        messages: List[Dict],
        target_ratio: float = TARGET_COMPRESSION_RATIO,
        force_method: Optional[str] = None
    ) -> Dict:
        """
        执行混合压缩

        Args:
            messages: 要压缩的消息列表
            target_ratio: 目标压缩率
            force_method: 强制使用的方法 ("rule" 或 "llm")

        Returns:
            压缩结果字典
        """
        self.stats["total_compressions"] += 1

        # 分离system prompts
        system_prompts = []
        messages_to_compress = []

        for msg in messages:
            if msg.get("role") == "system" and not msg.get("compressed", False):
                system_prompts.append(msg)
            else:
                messages_to_compress.append(msg)

        if not messages_to_compress:
            # 只有system prompts，无需压缩
            return {
                "compressed_message": system_prompts[0] if system_prompts else None,
                "original_tokens": sum(sp.get("tokens", 0) for sp in system_prompts),
                "compressed_tokens": sum(sp.get("tokens", 0) for sp in system_prompts),
                "compression_ratio": 0,
                "system_prompts": system_prompts,
                "method": "none"
            }

        # 决定使用哪种压缩方法
        method = self._decide_method(messages_to_compress, force_method)

        print(f"\n🔄 使用 {method.upper()} 方法进行压缩")

        try:
            if method == "llm":
                # 使用LLM方法
                result = await self._compress_with_llm(messages_to_compress, target_ratio)
                self.stats["llm_compressions"] += 1
            else:
                # 使用规则方法
                result = await self._compress_with_rule(messages_to_compress)
                self.stats["rule_compressions"] += 1

            # 添加system_prompts到结果
            result["system_prompts"] = system_prompts
            result["method"] = method

            return result

        except Exception as e:
            print(f"\n❌ {method.upper()}压缩失败: {e}")

            if method == "llm" and self.fallback_on_error:
                print("🔄 回退到规则方法...")
                self.stats["fallback_count"] += 1
                self.stats["rule_compressions"] += 1

                result = await self._compress_with_rule(messages_to_compress)
                result["system_prompts"] = system_prompts
                result["method"] = "rule_fallback"
                return result
            else:
                raise

    def _decide_method(self, messages: List[Dict], force_method: Optional[str]) -> str:
        """
        决定使用哪种压缩方法

        Args:
            messages: 消息列表
            force_method: 强制使用的方法

        Returns:
            "rule" 或 "llm"
        """
        if force_method:
            return force_method

        # 如果LLM未启用，使用规则方法
        if not self.use_llm or not self.llm_compressor:
            return "rule"

        # 根据消息数量决定
        if len(messages) < self.llm_threshold:
            return "rule"  # 消息少，规则方法足够
        else:
            return "llm"   # 消息多，LLM效果更好

    async def _compress_with_llm(
        self,
        messages: List[Dict],
        target_ratio: float
    ) -> Dict:
        """使用LLM方法压缩"""
        # 先用规则方法提取实体（帮助LLM理解）
        classified = self.rule_compressor.classify_messages(messages)
        entities = self.rule_compressor.extract_entities(classified)

        # 调用LLM压缩
        result = await self.llm_compressor.compress(
            messages,
            entities=entities,
            target_ratio=target_ratio
        )

        return result

    async def _compress_with_rule(self, messages: List[Dict]) -> Dict:
        """使用规则方法压缩"""
        result = await self.rule_compressor.compress(messages)
        return result

    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {
            "hybrid_stats": self.stats,
            "rule_compressor_stats": self.rule_compressor.stats
        }

        if self.llm_compressor:
            stats["llm_compressor_stats"] = self.llm_compressor.get_stats()

        return stats


if __name__ == "__main__":
    import asyncio
    import time

    async def test_hybrid_compressor():
        """测试混合压缩器"""
        print("🧪 测试混合压缩器...\n")

        # 创建测试消息
        test_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant.",
                "timestamp": time.time() - 2000,
                "tokens": 10
            },
            {
                "role": "user",
                "content": "我想创建一个Python数据分析项目",
                "timestamp": time.time() - 1000,
                "tokens": 20
            },
            {
                "role": "assistant",
                "content": "好的！让我帮你创建DataProcessor类...",
                "timestamp": time.time() - 900,
                "tokens": 150
            },
            {
                "role": "user",
                "content": "添加数据清洗功能",
                "timestamp": time.time() - 800,
                "tokens": 15
            },
            {
                "role": "assistant",
                "content": "添加clean_data方法处理缺失值...",
                "timestamp": time.time() - 700,
                "tokens": 120
            }
        ]

        # 测试1: 少量消息（应使用规则方法）
        print("=" * 60)
        print("测试1: 少量消息（3条）")
        print("=" * 60)

        compressor1 = HybridCompressor(use_llm=True, llm_threshold=5)
        result1 = await compressor1.compress(test_messages[:3])

        print(f"\n使用方法: {result1['method']}")
        print(f"压缩率: {result1['compression_ratio']*100:.1f}%")

        # 测试2: 大量消息（应使用LLM方法）
        print("\n" + "=" * 60)
        print("测试2: 大量消息（5条）")
        print("=" * 60)

        compressor2 = HybridCompressor(use_llm=True, llm_threshold=3)
        result2 = await compressor2.compress(test_messages)

        print(f"\n使用方法: {result2['method']}")
        print(f"压缩率: {result2['compression_ratio']*100:.1f}%")

        # 测试3: 强制使用规则方法
        print("\n" + "=" * 60)
        print("测试3: 强制使用规则方法")
        print("=" * 60)

        compressor3 = HybridCompressor(use_llm=True)
        result3 = await compressor3.compress(test_messages, force_method="rule")

        print(f"\n使用方法: {result3['method']}")
        print(f"压缩率: {result3['compression_ratio']*100:.1f}%")

        # 显示统计
        print("\n" + "=" * 60)
        print("统计信息")
        print("=" * 60)

        all_stats = compressor2.get_stats()
        print(f"\n混合压缩统计:")
        for key, value in all_stats["hybrid_stats"].items():
            print(f"  {key}: {value}")

    asyncio.run(test_hybrid_compressor())
