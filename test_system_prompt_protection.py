#!/usr/bin/env python3
"""
测试System Prompt保护功能

验证：
1. System prompt被正确识别
2. System prompt不被压缩
3. System prompt始终在上下文最前面
"""

import asyncio
import time
from compressor import AU2Compressor
from context_manager import ContextManager


async def test_system_prompt_protection():
    """测试system prompt保护功能"""

    print("=" * 70)
    print("🧪 测试System Prompt保护功能")
    print("=" * 70)
    print()

    # 测试1: 直接压缩带system prompt的消息
    print("【测试1】直接压缩带有System Prompt的消息列表")
    print("-" * 70)

    test_messages = [
        {
            "role": "system",
            "content": """You are an advanced AI assistant specialized in cybersecurity and penetration testing.

Your capabilities include:
- Network reconnaissance and scanning
- Vulnerability assessment
- Exploit development
- Security testing automation
- Detailed reporting

You must always prioritize ethical hacking practices and obtain proper authorization.""",
            "timestamp": time.time() - 1000,
            "tokens": 50
        },
        {
            "role": "user",
            "content": "我需要对目标服务器192.168.1.100进行渗透测试",
            "timestamp": time.time() - 900,
            "tokens": 20
        },
        {
            "role": "assistant",
            "content": "好的，让我们开始渗透测试。首先使用nmap扫描端口：nmap -sV -sC -p- 192.168.1.100",
            "timestamp": time.time() - 800,
            "tokens": 30
        },
        {
            "role": "user",
            "content": "扫描发现开放端口：22 (SSH), 80 (HTTP), 443 (HTTPS), 3306 (MySQL)",
            "timestamp": time.time() - 700,
            "tokens": 25
        },
        {
            "role": "assistant",
            "content": "很好！接下来我们使用burpsuite拦截HTTP请求，寻找潜在的SQL注入点...",
            "timestamp": time.time() - 600,
            "tokens": 35
        }
    ]

    compressor = AU2Compressor()
    result = await compressor.compress(test_messages)

    print(f"\n✅ 压缩完成")
    print(f"原始消息数: {len(test_messages)}")
    print(f"原始Tokens: {result['original_tokens']}")
    print(f"压缩后Tokens: {result['compressed_tokens']}")
    print(f"压缩率: {result['compression_ratio']*100:.1f}%")

    if result.get('system_prompt'):
        print(f"\n🔒 System Prompt已保护:")
        print(f"   角色: {result['system_prompt']['role']}")
        print(f"   Tokens: {result['system_prompt'].get('tokens', 0)}")
        print(f"   内容预览: {result['system_prompt']['content'][:100]}...")
    else:
        print("\n❌ 未检测到System Prompt")

    print()

    # 测试2: 在ContextManager中测试
    print("\n【测试2】在ContextManager中测试System Prompt保护")
    print("-" * 70)

    manager = ContextManager(max_tokens=500)  # 设置较低的限制以触发压缩

    # 添加带system prompt的消息
    await manager.add_message(
        "system",
        """You are a security testing expert with deep knowledge of:
- Penetration testing methodologies
- Vulnerability assessment
- Exploit development
- Security automation

Always maintain ethical standards."""
    )

    # 添加一些对话消息
    conversations = [
        ("user", "我想测试一个web应用的安全性"),
        ("assistant", "好的，我会帮你进行安全测试。首先使用nmap扫描目标..." + "详细的扫描结果" * 20),
        ("user", "发现了SQL注入漏洞"),
        ("assistant", "让我们使用sqlmap进行详细测试..." + "详细的测试过程" * 20),
    ]

    for role, content in conversations:
        await manager.add_message(role, content)
        await asyncio.sleep(0.1)

    # 强制触发压缩
    print("\n强制触发压缩...")
    compression_result = await manager.compress_if_needed(force=True)

    if compression_result.get("compressed"):
        print(f"✅ 压缩成功")
        print(f"   节省Tokens: {compression_result['saved_tokens']}")
        print(f"   压缩率: {compression_result['compression_ratio']*100:.1f}%")

    # 获取完整上下文
    print("\n获取完整上下文...")
    context = await manager.get_context()

    print(f"上下文消息数: {len(context)}")
    for i, msg in enumerate(context, 1):
        role = msg.get("role", "unknown")
        tokens = msg.get("tokens", 0)
        compressed = msg.get("compressed", False)
        content_preview = msg.get("content", "")[:60] + "..."

        tags = []
        if compressed:
            tags.append("压缩")
        if role == "system" and not compressed:
            tags.append("保护")

        tag_str = f" [{', '.join(tags)}]" if tags else ""
        print(f"  {i}. {role}{tag_str}: {tokens} tokens")
        print(f"     内容: {content_preview}")

    # 验证system prompt在最前面
    if context and context[0].get("role") == "system":
        if "security testing expert" in context[0].get("content", ""):
            print("\n✅ System Prompt正确保护且位于上下文最前面！")
        else:
            print("\n⚠️  System Prompt内容可能被修改")
    else:
        print("\n❌ System Prompt不在最前面或丢失")

    print()

    # 测试3: 只有system prompt的情况
    print("\n【测试3】只有System Prompt的情况（无需压缩）")
    print("-" * 70)

    single_message = [
        {
            "role": "system",
            "content": "You are a helpful assistant.",
            "timestamp": time.time(),
            "tokens": 10
        }
    ]

    result = await compressor.compress(single_message)

    print(f"原始Tokens: {result['original_tokens']}")
    print(f"压缩后Tokens: {result['compressed_tokens']}")
    print(f"压缩率: {result['compression_ratio']}")

    if result.get('system_prompt'):
        print("✅ System Prompt被正确保留")
    else:
        print("❌ System Prompt丢失")

    print()
    print("=" * 70)
    print("✅ 所有测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_system_prompt_protection())
