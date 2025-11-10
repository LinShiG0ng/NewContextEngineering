"""
测试系统提示词保护功能

验证system prompt在压缩过程中是否被正确保护
"""

import asyncio
import time
from context_manager import ContextManager


async def test_system_prompt_protection():
    """测试system prompt是否会被压缩"""
    print("=" * 60)
    print("🧪 测试System Prompt保护功能")
    print("=" * 60)
    print()

    # 创建上下文管理器（使用小容量以快速触发压缩）
    manager = ContextManager(max_tokens=1500)

    # 添加一个system prompt
    print("1️⃣  添加System Prompt")
    print("-" * 60)
    original_system_prompt = "You are a helpful coding assistant. Always provide clear explanations with code examples."
    await manager.add_message("system", original_system_prompt)
    print(f"✅ System Prompt: {original_system_prompt[:50]}...")
    print()

    # 添加一些对话，触发压缩
    print("2️⃣  添加对话消息以触发压缩")
    print("-" * 60)

    conversations = [
        ("user", "请帮我创建一个Python数据处理类"),
        ("assistant", "好的，我来创建DataProcessor类，包含加载、清洗和分析功能。" + "代码实现细节..." * 20),
        ("user", "添加数据可视化功能"),
        ("assistant", "添加plot_data方法，使用matplotlib进行可视化。" + "详细实现..." * 25),
        ("user", "还需要导出功能"),
        ("assistant", "添加export_to_csv和export_to_excel方法。" + "完整代码..." * 30),
    ]

    for i, (role, content) in enumerate(conversations, 1):
        result = await manager.add_message(role, content)
        usage = manager.get_usage_status()
        print(f"  消息 {i}: {role} - {usage['percentage']} {usage['emoji']}")

        if result.get("compressed"):
            print(f"  🔄 触发了压缩！")
            comp_result = result["compression"]
            print(f"     原始: {comp_result['original_tokens']} tokens")
            print(f"     压缩后: {comp_result['compressed_tokens']} tokens")
            print(f"     节省: {comp_result['saved_tokens']} tokens")
            print()

    print()

    # 获取完整上下文
    print("3️⃣  检查最终上下文")
    print("-" * 60)
    context = await manager.get_context()

    print(f"上下文消息数: {len(context)}")
    print()

    # 检查system prompt是否完整保留
    system_messages = [msg for msg in context if msg.get("role") == "system"]

    print("📋 System消息列表:")
    for i, msg in enumerate(system_messages, 1):
        is_compressed = msg.get("compressed", False)
        is_llm_compressed = msg.get("llm_compressed", False)
        content = msg.get("content", "")
        tokens = msg.get("tokens", 0)

        print(f"\n  {i}. System消息:")
        print(f"     压缩状态: {'✅ 已压缩' if is_compressed else '❌ 未压缩'}")
        print(f"     LLM压缩: {'✅ 是' if is_llm_compressed else '❌ 否'}")
        print(f"     Tokens: {tokens}")
        print(f"     内容预览: {content[:100]}...")

        # 检查是否是原始system prompt
        if content == original_system_prompt:
            print(f"     ✅ 这是原始System Prompt，完整保留！")
        elif original_system_prompt in content:
            print(f"     ⚠️  原始System Prompt在内容中，但可能被修改")
        else:
            print(f"     ❌ 这不是原始System Prompt，可能已被压缩！")

    print()
    print("=" * 60)

    # 判断测试结果
    original_prompt_found = any(
        msg.get("content") == original_system_prompt
        for msg in context
    )

    if original_prompt_found:
        print("✅ 测试通过：System Prompt被正确保护")
    else:
        print("❌ 测试失败：System Prompt被压缩或丢失")
        print()
        print("原始System Prompt:")
        print(f"  {original_system_prompt}")
        print()
        print("当前上下文中的所有消息:")
        for i, msg in enumerate(context, 1):
            role = msg.get("role")
            content = msg.get("content", "")[:80]
            compressed = "压缩" if msg.get("compressed") else "未压缩"
            print(f"  {i}. [{role}] ({compressed}) {content}...")

    print("=" * 60)
    print()

    return original_prompt_found


async def test_multiple_compressions():
    """测试多次压缩后system prompt是否仍然保护"""
    print("=" * 60)
    print("🧪 测试多次压缩的System Prompt保护")
    print("=" * 60)
    print()

    manager = ContextManager(max_tokens=1000)

    # 添加system prompt
    original_system_prompt = "You are an expert Python developer."
    await manager.add_message("system", original_system_prompt)
    print(f"✅ 添加System Prompt: {original_system_prompt}")
    print()

    # 进行多轮对话，触发多次压缩
    for round_num in range(3):
        print(f"📍 第 {round_num + 1} 轮对话")
        print("-" * 60)

        # 添加足够的消息触发压缩
        for i in range(4):
            await manager.add_message("user", f"第{round_num+1}轮问题{i+1}" + "详细内容" * 20)
            result = await manager.add_message("assistant", f"第{round_num+1}轮回答{i+1}" + "详细实现" * 25)

            if result.get("compressed"):
                print(f"  🔄 触发了第 {manager.stats['compressions']} 次压缩")

        # 检查system prompt
        context = await manager.get_context()
        original_found = any(
            msg.get("content") == original_system_prompt
            for msg in context
        )

        if original_found:
            print(f"  ✅ System Prompt仍然完整保留")
        else:
            print(f"  ❌ System Prompt已丢失或被压缩")
        print()

    # 最终检查
    print("4️⃣  最终检查")
    print("-" * 60)
    context = await manager.get_context()

    original_found = any(
        msg.get("content") == original_system_prompt
        for msg in context
    )

    print(f"总压缩次数: {manager.stats['compressions']}")
    print(f"System Prompt状态: {'✅ 完整保留' if original_found else '❌ 已丢失'}")
    print()
    print("=" * 60)
    print()

    return original_found


async def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "System Prompt 保护功能测试" + " " * 20 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    # 测试1: 基本保护
    test1_passed = await test_system_prompt_protection()

    print()
    await asyncio.sleep(1)

    # 测试2: 多次压缩保护
    test2_passed = await test_multiple_compressions()

    # 总结
    print("=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"测试1 (基本保护): {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"测试2 (多次压缩): {'✅ 通过' if test2_passed else '❌ 失败'}")
    print()

    if test1_passed and test2_passed:
        print("🎉 所有测试通过！System Prompt保护功能正常工作")
    else:
        print("⚠️  部分测试失败，System Prompt保护存在问题")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
