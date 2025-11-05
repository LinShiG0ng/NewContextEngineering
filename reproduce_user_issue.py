#!/usr/bin/env python3
"""
重现用户报告的System Prompt截断问题

模拟用户的实际使用场景：
1. 添加长的system prompt
2. 添加对话
3. 触发压缩
4. 查看上下文中的system prompt是否完整
"""

import asyncio
import json
from context_manager import ContextManager


async def reproduce_user_issue():
    """重现用户的问题"""

    print("=" * 80)
    print("🔍 重现用户报告的System Prompt截断问题")
    print("=" * 80)
    print()

    # 创建一个非常长的system prompt（模拟用户的实际使用）
    long_system_prompt = """You are an advanced AI assistant specialized in cybersecurity and penetration testing.

Your capabilities include:
- Network reconnaissance and scanning using tools like nmap, masscan, and rustscan
- Vulnerability assessment and exploitation using Metasploit, Burp Suite, and custom scripts
- Web application security testing including SQL injection, XSS, CSRF, and authentication bypass
- Binary exploitation and reverse engineering using IDA Pro, Ghidra, and GDB
- Network traffic analysis using Wireshark, tcpdump, and tshark
- Privilege escalation techniques on Linux and Windows systems
- Social engineering and phishing simulation
- Password cracking and hash analysis using John the Ripper and Hashcat
- Wireless security testing with aircrack-ng suite
- Mobile application security testing (Android and iOS)
- Container and cloud security assessment
- Detailed reporting and documentation of findings

Core principles:
1. Always prioritize ethical hacking practices and obtain proper authorization
2. Document all findings thoroughly with screenshots and evidence
3. Follow responsible disclosure procedures for discovered vulnerabilities
4. Maintain confidentiality of sensitive information
5. Provide actionable remediation recommendations

Testing methodology:
Phase 1: Reconnaissance and information gathering
Phase 2: Scanning and enumeration
Phase 3: Vulnerability identification and analysis
Phase 4: Exploitation and privilege escalation
Phase 5: Post-exploitation and persistence
Phase 6: Reporting and remediation

You must NEVER engage in unauthorized testing or malicious activities. All testing must be performed within the scope of authorized engagements only."""

    print(f"📏 创建的System Prompt长度: {len(long_system_prompt)} 字符")
    print()

    # 创建ContextManager
    manager = ContextManager(max_tokens=1000)  # 设置较低限制以触发压缩

    # 步骤1: 添加system prompt
    print("步骤1: 添加System Prompt")
    await manager.add_message("system", long_system_prompt)
    print(f"  ✅ 已添加 ({len(long_system_prompt)} 字符)")
    print()

    # 步骤2: 添加对话消息
    print("步骤2: 添加对话消息")
    conversations = [
        ("user", "请帮我测试目标服务器192.168.1.100的安全性" + "填充内容" * 20),
        ("assistant", "好的，我会进行专业的渗透测试。首先使用nmap扫描端口" + "详细过程" * 20),
        ("user", "发现开放了22, 80, 443端口" + "更多信息" * 15),
        ("assistant", "接下来测试web应用的安全性" + "测试步骤" * 20),
    ]

    for role, content in conversations:
        await manager.add_message(role, content)
        print(f"  ✅ 添加{role}消息")

    print()

    # 步骤3: 查看压缩前的上下文
    print("步骤3: 压缩前查看上下文")
    context_before = await manager.get_context()

    system_before = None
    for msg in context_before:
        if msg.get("role") == "system" and "advanced AI assistant" in msg.get("content", ""):
            system_before = msg
            break

    if system_before:
        content_before = system_before.get("content", "")
        print(f"  System Prompt长度: {len(content_before)} 字符")
        print(f"  内容完整: {'✅' if len(content_before) == len(long_system_prompt) else '❌'}")
        if "..." in content_before:
            print(f"  ⚠️  发现省略号！")
    else:
        print(f"  ❌ 未找到System Prompt")

    print()

    # 步骤4: 强制触发压缩
    print("步骤4: 触发压缩")
    compression_result = await manager.compress_if_needed(force=True)

    if compression_result.get("compressed"):
        print(f"  ✅ 压缩成功")
        print(f"  节省Token: {compression_result.get('saved_tokens', 0)}")
    else:
        print(f"  ⚠️  压缩未执行")

    print()

    # 步骤5: 查看压缩后的上下文（这是关键！）
    print("步骤5: 压缩后查看上下文（用户看到省略号的地方）")
    context_after = await manager.get_context()

    print(f"  上下文消息数: {len(context_after)}")
    print()

    # 查找system prompt
    system_after = None
    for i, msg in enumerate(context_after):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        compressed = msg.get("compressed", False)

        print(f"  消息#{i+1}: {role}")
        print(f"    压缩标志: {compressed}")
        print(f"    内容长度: {len(content)} 字符")
        print(f"    内容预览: {content[:100]}...")

        if "..." in content and not compressed:
            print(f"    ⚠️  发现省略号（非压缩消息）")

        # 检查是否是我们的system prompt
        if role == "system" and "advanced AI assistant" in content:
            system_after = msg
            print(f"    ✅ 这是我们的System Prompt")

        print()

    # 详细分析system prompt
    if system_after:
        content_after = system_after.get("content", "")

        print("=" * 80)
        print("📊 System Prompt详细分析")
        print("=" * 80)
        print(f"原始长度: {len(long_system_prompt)} 字符")
        print(f"当前长度: {len(content_after)} 字符")
        print()

        if len(content_after) == len(long_system_prompt):
            print("✅ 长度完全一致！")
        else:
            print(f"❌ 长度不一致！差异: {len(long_system_prompt) - len(content_after)} 字符")

        print()

        if content_after == long_system_prompt:
            print("✅ 内容完全一致！System Prompt被完整保护！")
        else:
            print("❌ 内容不一致！")

            # 查找差异
            if "..." in content_after:
                print("\n⚠️  发现省略号！")
                ellipsis_pos = content_after.find("...")
                print(f"省略号位置: {ellipsis_pos}")
                print(f"\n截断前50字符:")
                print(f"  {content_after[max(0, ellipsis_pos-50):ellipsis_pos]}")
                print(f"\n截断后50字符:")
                print(f"  {content_after[ellipsis_pos:min(len(content_after), ellipsis_pos+50)]}")

                # 对比原始内容
                if ellipsis_pos < len(long_system_prompt):
                    print(f"\n原始内容在此位置:")
                    print(f"  {long_system_prompt[ellipsis_pos:min(len(long_system_prompt), ellipsis_pos+100)]}")

            # 检查是否有截断
            if len(content_after) < len(long_system_prompt):
                print(f"\n⚠️  内容被截短了 {len(long_system_prompt) - len(content_after)} 字符")
                print(f"\n原始结尾:")
                print(f"  {long_system_prompt[-100:]}")
                print(f"\n当前结尾:")
                print(f"  {content_after[-100:]}")
    else:
        print("❌ 压缩后未找到System Prompt！")

    print()
    print("=" * 80)

    # 额外检查：检查preserved_system_prompt
    print("\n🔍 检查ContextManager内部状态")
    if manager.preserved_system_prompt:
        preserved_content = manager.preserved_system_prompt.get("content", "")
        print(f"  preserved_system_prompt存在")
        print(f"  长度: {len(preserved_content)} 字符")
        print(f"  是否完整: {'✅' if len(preserved_content) == len(long_system_prompt) else '❌'}")
        if "..." in preserved_content:
            print(f"  ⚠️  preserved_system_prompt中有省略号！")
    else:
        print(f"  ❌ preserved_system_prompt为空")

    # 检查storage中的消息
    print("\n🔍 检查Storage中的消息")
    all_messages = manager.storage.get_all_messages()
    print(f"  总消息数: {len(all_messages)}")
    for i, msg in enumerate(all_messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if role == "system" and "advanced AI assistant" in content:
            print(f"  消息#{i+1}: 发现System Prompt在storage中")
            print(f"    长度: {len(content)} 字符")
            if "..." in content:
                print(f"    ⚠️  Storage中的System Prompt有省略号！")


if __name__ == "__main__":
    asyncio.run(reproduce_user_issue())
