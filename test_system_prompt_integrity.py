#!/usr/bin/env python3
"""
测试System Prompt完整性保护

验证：
1. System prompt不被处理
2. System prompt内容不被截断
3. System prompt完整保留所有字符
"""

import asyncio
import time
from compressor import AU2Compressor
from context_manager import ContextManager


async def test_system_prompt_integrity():
    """测试system prompt的完整性"""

    print("=" * 80)
    print("🧪 测试System Prompt完整性保护")
    print("=" * 80)
    print()

    # 创建一个非常长的system prompt（超过150字符，会触发之前的截断bug）
    long_system_prompt = """You are an advanced AI assistant specialized in cybersecurity and penetration testing.

Your capabilities include:
- Network reconnaissance and scanning using tools like nmap, masscan, and rustscan
- Vulnerability assessment and exploitation using Metasploit, Burp Suite, and custom scripts
- Web application security testing including SQL injection, XSS, CSRF, and authentication bypass
- Binary exploitation and reverse engineering using IDA Pro, Ghidra, and GDB
- Detailed reporting and documentation of findings

Core principles:
1. Always prioritize ethical hacking practices
2. Obtain proper authorization before testing
3. Document all findings thoroughly
4. Follow responsible disclosure procedures
5. Maintain confidentiality of sensitive information

Testing methodology:
- Reconnaissance and information gathering
- Scanning and enumeration
- Vulnerability identification
- Exploitation and privilege escalation
- Post-exploitation and persistence
- Reporting and remediation

You must NEVER engage in unauthorized testing or malicious activities."""

    print(f"📏 System Prompt长度: {len(long_system_prompt)} 字符")
    print(f"   （超过150字符，之前会被截断）")
    print()

    # 测试1: 直接压缩
    print("【测试1】直接压缩（包含长System Prompt）")
    print("-" * 80)

    test_messages = [
        {
            "role": "system",
            "content": long_system_prompt,
            "timestamp": time.time() - 1000,
            "tokens": 100
        },
        {
            "role": "user",
            "content": "帮我测试这个目标服务器",
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
    result = await compressor.compress(test_messages)

    print(f"\n✅ 压缩完成")
    print(f"压缩率: {result['compression_ratio']*100:.1f}%")

    # 验证system prompt
    if result.get('system_prompt'):
        returned_prompt = result['system_prompt']['content']
        original_prompt = long_system_prompt

        print(f"\n🔍 System Prompt完整性检查:")
        print(f"   原始长度: {len(original_prompt)} 字符")
        print(f"   返回长度: {len(returned_prompt)} 字符")

        if returned_prompt == original_prompt:
            print(f"   ✅ 内容完全一致！")
        else:
            print(f"   ❌ 内容不一致！")
            print(f"   原始: {original_prompt[:100]}...")
            print(f"   返回: {returned_prompt[:100]}...")

            # 检查是否被截断
            if "..." in returned_prompt:
                print(f"   ⚠️  发现截断符号 '...'")

        # 验证所有关键短语都存在
        key_phrases = [
            "advanced AI assistant",
            "cybersecurity and penetration testing",
            "Network reconnaissance",
            "Binary exploitation",
            "ethical hacking practices",
            "unauthorized testing"
        ]

        print(f"\n   关键短语检查:")
        all_present = True
        for phrase in key_phrases:
            present = phrase in returned_prompt
            emoji = "✅" if present else "❌"
            print(f"   {emoji} '{phrase}'")
            if not present:
                all_present = False

        if all_present:
            print(f"\n   ✅ 所有关键短语都保留！")
        else:
            print(f"\n   ❌ 部分关键短语丢失！")
    else:
        print("\n❌ 未检测到System Prompt")

    print()

    # 测试2: 在ContextManager中测试
    print("\n【测试2】在ContextManager中测试完整性")
    print("-" * 80)

    manager = ContextManager(max_tokens=500)

    # 添加长system prompt
    await manager.add_message("system", long_system_prompt)

    # 添加对话
    await manager.add_message("user", "开始测试" + "填充内容" * 30)
    await manager.add_message("assistant", "正在执行" + "详细过程" * 30)

    # 强制压缩
    print("\n强制触发压缩...")
    compression_result = await manager.compress_if_needed(force=True)

    if compression_result.get("compressed"):
        print(f"✅ 压缩成功")

    # 获取上下文
    print("\n获取完整上下文...")
    context = await manager.get_context()

    # 找到system prompt
    system_msg = None
    for msg in context:
        if msg.get("role") == "system" and "advanced AI assistant" in msg.get("content", ""):
            system_msg = msg
            break

    if system_msg:
        returned_content = system_msg.get("content", "")

        print(f"\n🔍 上下文中的System Prompt检查:")
        print(f"   原始长度: {len(long_system_prompt)} 字符")
        print(f"   上下文长度: {len(returned_content)} 字符")

        if returned_content == long_system_prompt:
            print(f"   ✅ 内容完全一致！System Prompt被完整保护！")
        else:
            print(f"   ❌ 内容不一致！")

            # 显示差异
            if len(returned_content) < len(long_system_prompt):
                print(f"   ⚠️  内容被截断了 {len(long_system_prompt) - len(returned_content)} 个字符")

            if "..." in returned_content:
                print(f"   ⚠️  发现截断符号 '...'")
                # 找到截断位置
                ellipsis_pos = returned_content.find("...")
                print(f"   截断位置: {ellipsis_pos}")
                print(f"   截断前: ...{returned_content[max(0, ellipsis_pos-30):ellipsis_pos]}")
                print(f"   截断后: {returned_content[ellipsis_pos:min(len(returned_content), ellipsis_pos+30)]}...")
    else:
        print("\n❌ 在上下文中未找到System Prompt")

    print()
    print("=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_system_prompt_integrity())
