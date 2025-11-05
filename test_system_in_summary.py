#!/usr/bin/env python3
"""
测试System Prompt是否出现在压缩摘要中

重现用户报告的问题：
system prompt在压缩后被放在"关键讨论点"中并被截断
"""

import asyncio
import time
from compressor import AU2Compressor


async def test_system_prompt_in_summary():
    """测试system prompt是否出现在压缩摘要中"""

    print("=" * 80)
    print("🔍 测试System Prompt是否出现在压缩摘要的'关键讨论点'中")
    print("=" * 80)
    print()

    # 创建一个包含关键词的system prompt（可能被评为critical）
    system_prompt_with_keywords = """You are an advanced AI assistant specialized in cybersecurity and penetration testing.

CRITICAL REQUIREMENTS:
- Always obtain proper authorization before testing
- Document all errors and exceptions thoroughly
- Report critical vulnerabilities immediately
- Follow ethical hacking practices

Your capabilities include network reconnaissance, vulnerability assessment, and detailed reporting.

This is a very important system prompt that must never be compressed or truncated."""

    print(f"📏 System Prompt长度: {len(system_prompt_with_keywords)} 字符")
    print(f"包含关键词: critical, error, exception")
    print()

    # 测试场景1: System prompt是第一条消息
    print("【场景1】System Prompt是第一条消息")
    print("-" * 80)

    messages_scenario1 = [
        {
            "role": "system",
            "content": system_prompt_with_keywords,
            "timestamp": time.time() - 1000,
            "tokens": 100
        },
        {
            "role": "user",
            "content": "请帮我测试目标服务器",
            "timestamp": time.time() - 900,
            "tokens": 20
        },
        {
            "role": "assistant",
            "content": "好的，我会进行专业的渗透测试",
            "timestamp": time.time() - 800,
            "tokens": 30
        }
    ]

    compressor = AU2Compressor()
    result1 = await compressor.compress(messages_scenario1)

    print(f"\n压缩完成")
    print(f"压缩率: {result1['compression_ratio']*100:.1f}%")

    # 检查compressed_message的内容
    compressed_content = result1['compressed_message'].get('content', '')

    print(f"\n📊 分析压缩摘要内容:")
    print(f"摘要长度: {len(compressed_content)} 字符")
    print()

    # 检查system prompt是否出现在摘要中
    if "advanced AI assistant" in compressed_content:
        print("❌ 发现问题！System Prompt内容出现在压缩摘要中！")

        # 找到出现的位置
        if "关键讨论点" in compressed_content:
            print("⚠️  System Prompt出现在'关键讨论点'部分")

        # 检查是否被截断
        if "CRITICAL REQUIREMENTS" in compressed_content:
            print("✅ 完整内容存在")
        else:
            print("❌ 内容被截断了！")

        # 显示相关部分
        lines = compressed_content.split('\n')
        for i, line in enumerate(lines):
            if "advanced AI assistant" in line or "CRITICAL" in line:
                print(f"\n发现位置 (第{i+1}行):")
                start = max(0, i-2)
                end = min(len(lines), i+3)
                for j in range(start, end):
                    prefix = ">>>" if j == i else "   "
                    print(f"{prefix} {lines[j]}")
    else:
        print("✅ System Prompt内容未出现在压缩摘要中")

    # 检查system_prompts字段
    if result1.get('system_prompts'):
        print(f"\n✅ system_prompts字段存在")
        print(f"   数量: {len(result1['system_prompts'])}")
        print(f"   第一个长度: {len(result1['system_prompts'][0]['content'])} 字符")
    else:
        print(f"\n❌ system_prompts字段不存在")

    print()
    print()

    # 测试场景2: System prompt不是第一条消息
    print("【场景2】System Prompt不是第一条消息（常见错误场景）")
    print("-" * 80)

    messages_scenario2 = [
        {
            "role": "user",
            "content": "你好",
            "timestamp": time.time() - 1100,
            "tokens": 10
        },
        {
            "role": "system",  # System prompt在第二条
            "content": system_prompt_with_keywords,
            "timestamp": time.time() - 1000,
            "tokens": 100
        },
        {
            "role": "user",
            "content": "请帮我测试目标服务器",
            "timestamp": time.time() - 900,
            "tokens": 20
        },
        {
            "role": "assistant",
            "content": "好的，我会进行专业的渗透测试",
            "timestamp": time.time() - 800,
            "tokens": 30
        }
    ]

    result2 = await compressor.compress(messages_scenario2)

    print(f"\n压缩完成")
    print(f"压缩率: {result2['compression_ratio']*100:.1f}%")

    compressed_content2 = result2['compressed_message'].get('content', '')

    print(f"\n📊 分析压缩摘要内容:")
    print(f"摘要长度: {len(compressed_content2)} 字符")
    print()

    if "advanced AI assistant" in compressed_content2:
        print("❌❌ 严重问题！System Prompt出现在压缩摘要中！")
        print("   原因: System Prompt不是第一条消息，没有被正确识别")

        if "..." in compressed_content2 and "CRITICAL REQUIREMENTS" not in compressed_content2:
            print("❌ 并且被截断了！")
    else:
        print("✅ System Prompt内容未出现在压缩摘要中")

    if result2.get('system_prompts'):
        print(f"\n✅ system_prompts字段存在")
        print(f"   数量: {len(result2['system_prompts'])}")
        print(f"   第一个长度: {len(result2['system_prompts'][0]['content'])} 字符")
    else:
        print(f"\n❌ system_prompts字段不存在")

    print()
    print("=" * 80)
    print("📋 总结")
    print("=" * 80)
    print()
    print("当前实现只保护第一条role='system'的消息。")
    print("如果system prompt不是第一条消息，它会被当作普通消息压缩。")
    print()
    print("需要改进的地方：")
    print("1. 识别所有未压缩的system消息")
    print("2. 从压缩流程中排除它们")
    print("3. 在返回结果中单独保存它们")


if __name__ == "__main__":
    asyncio.run(test_system_prompt_in_summary())
