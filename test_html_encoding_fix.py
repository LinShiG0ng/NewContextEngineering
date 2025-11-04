#!/usr/bin/env python3
"""
测试HTML实体编码修复

验证前端是否能正确解码HTML实体
"""

import asyncio
import time
from context_manager import ContextManager


async def test_html_entities_in_context():
    """测试包含特殊字符的上下文"""

    print("=" * 70)
    print("🧪 测试HTML实体编码修复")
    print("=" * 70)
    print()

    # 创建上下文管理器
    manager = ContextManager(max_tokens=10000)

    # 添加包含XML/HTML标签的消息（模拟渗透测试场景）
    test_messages = [
        {
            "role": "system",
            "content": "You are a security testing assistant."
        },
        {
            "role": "user",
            "content": "帮我分析这个SQL注入测试流程"
        },
        {
            "role": "assistant",
            "content": """好的，这是SQL注入测试的详细流程：

<step>
<id>S1</id>
<goal>识别注入点</goal>
<tool>burpsuite</tool>
<reason>拦截HTTP请求，分析参数</reason>
<proposed_command>burpsuite -i proxy</proposed_command>
<done>true</done>
</step>

<step>
<id>S2</id>
<goal>测试基本注入</goal>
<tool>sqlmap</tool>
<reason>使用自动化工具进行初步测试</reason>
<proposed_command>sqlmap -u "http://target.com/page?id=1" --batch</proposed_command>
<done>true</done>
</step>

<step>
<id>S3</id>
<goal>枚举数据库</goal>
<tool>sqlmap</tool>
<reason>获取数据库结构信息</reason>
<proposed_command>sqlmap -u "http://target.com/page?id=1" --dbs</proposed_command>
<done>false</done>
</step>

测试payload示例：
- ' OR '1'='1
- " OR "1"="1
- 1' UNION SELECT NULL,NULL--
- 1" UNION SELECT NULL,NULL--
"""
        }
    ]

    # 添加所有消息
    for msg in test_messages:
        await manager.add_message(msg["role"], msg["content"])
        print(f"✅ 添加消息: {msg['role']}")

    print()

    # 获取完整上下文
    context = await manager.get_context()

    print(f"📊 上下文统计:")
    print(f"   消息数: {len(context)}")
    print()

    # 检查内容中的特殊字符
    print("🔍 检查特殊字符:")
    for i, msg in enumerate(context, 1):
        content = msg.get("content", "")

        # 检查是否包含<>等字符
        has_angle_brackets = "<" in content and ">" in content
        has_quotes = '"' in content

        if has_angle_brackets or has_quotes:
            print(f"\n消息 #{i} ({msg.get('role', 'unknown')}):")
            print(f"   包含 < >: {has_angle_brackets}")
            print(f"   包含引号: {has_quotes}")

            # 显示一小段内容作为示例
            lines = content.split('\n')
            for line in lines[:5]:
                if '<' in line or '>' in line:
                    print(f"   示例: {line[:80]}")
                    break

    print()

    # 模拟JSON序列化（就像API返回的那样）
    import json

    print("🔄 模拟JSON序列化:")
    json_str = json.dumps(context[0], ensure_ascii=False)

    # 检查JSON中是否包含原始的<>字符（不应该被转义）
    print(f"   JSON长度: {len(json_str)}")

    if "&lt;" in json_str or "&gt;" in json_str:
        print("   ❌ 发现HTML实体编码（&lt; &gt;）")
    else:
        print("   ✅ 未发现HTML实体编码")

    if '"<step>"' in json_str or "'<step>'" in json_str:
        print("   ✅ 原始<>字符保留在JSON中")
    else:
        print("   ⚠️  未找到<step>标签")

    print()

    print("=" * 70)
    print("💡 说明:")
    print("   1. 后端返回的JSON应该包含原始的 < > 字符")
    print("   2. 前端JavaScript使用decodeHTMLEntities()解码")
    print("   3. 浏览器显示时会正确显示 < > 而不是 &lt; &gt;")
    print("=" * 70)

    print()
    print("✅ 测试完成！")
    print()
    print("🌐 启动web服务器测试:")
    print("   python web_server.py")
    print("   然后访问 http://localhost:8000")
    print("   点击'查看完整上下文'按钮验证解码效果")


if __name__ == "__main__":
    asyncio.run(test_html_entities_in_context())
