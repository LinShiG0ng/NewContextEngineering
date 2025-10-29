"""
主程序 - 交互式上下文工程演示

提供完整的命令行交互界面，支持:
- 真实LLM对话
- 实时token监控
- 自动压缩展示
- 压缩效果对比
- 统计信息查看
- 历史导出
"""

import asyncio
import sys
import os
from typing import Optional

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from context_manager import ContextManager
from llm_client import LLMClient, MockLLMClient
from config_loader import load_config
from utils import print_colored, print_progress_bar, print_statistics, estimate_cost


class InteractiveDemo:
    """
    交互式演示程序
    """

    def __init__(self, config: dict, use_mock: bool = False):
        """
        初始化演示程序

        Args:
            config: 配置字典
            use_mock: 是否使用模拟客户端
        """
        self.config = config
        self.use_mock = use_mock

        # 初始化组件
        self.manager = ContextManager(
            max_tokens=config.get("max_tokens", 8000)
        )

        # 初始化LLM客户端
        if use_mock:
            print("⚠️  使用模拟客户端（无需真实API）")
            self.client = MockLLMClient(config)
        else:
            self.client = LLMClient(config)

        # 运行统计
        self.session_stats = {
            "queries": 0,
            "api_calls": 0,
            "total_cost": 0.0
        }

    async def start(self):
        """
        启动交互式会话
        """
        # 显示欢迎信息
        self._print_welcome()

        # 测试API连接
        if not self.use_mock:
            connected = await self._test_connection()
            if not connected:
                print("\n⚠️  API连接失败，是否使用模拟模式？(y/n): ", end="")
                choice = input().strip().lower()
                if choice == 'y':
                    self.use_mock = True
                    self.client = MockLLMClient(self.config)
                else:
                    print("\n请检查配置后重试。退出程序...")
                    return

        print("\n" + "=" * 60)
        print("🎉 准备就绪！开始对话吧")
        print("=" * 60)
        print("\n💡 提示: 输入 /help 查看所有命令\n")

        # 主循环
        while True:
            try:
                # 显示使用率
                self._print_usage()

                # 获取用户输入
                print_colored("💬 用户> ", "cyan", bold=True)
                user_input = input().strip()

                if not user_input:
                    continue

                # 处理特殊命令
                if user_input.startswith("/"):
                    should_continue = await self._handle_command(user_input)
                    if not should_continue:
                        break
                    continue

                # 处理正常对话
                await self._handle_conversation(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 检测到中断信号...")
                confirm = input("确认退出？(y/n): ").strip().lower()
                if confirm == 'y':
                    break
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                print("继续对话或输入 /quit 退出\n")

        # 退出
        self._print_goodbye()

    def _print_welcome(self):
        """
        显示欢迎信息
        """
        print("\n" + "=" * 60)
        print_colored("🧠 上下文工程演示系统", "cyan", bold=True)
        print("=" * 60)

        model_info = self.client.get_model_info()
        print(f"当前模型: {model_info['model']}")
        print(f"提供商: {model_info['provider']}")
        print(f"Token限制: {self.config.get('max_tokens', 8000):,}")
        print(f"压缩阈值: {self.config.get('auto_compact_threshold', 0.92)*100:.0f}%")
        print("=" * 60)

    async def _test_connection(self) -> bool:
        """
        测试API连接

        Returns:
            是否成功
        """
        print("\n🔄 测试API连接...")
        try:
            success = await self.client.test_connection()
            if success:
                print("✅ API连接正常")
            return success
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    def _print_usage(self):
        """
        显示token使用率
        """
        status = self.manager.get_usage_status()
        usage = status["usage"]

        print()  # 空行
        print_progress_bar(
            usage,
            width=40,
            low_threshold=self.config.get("warning_threshold", 0.6),
            high_threshold=self.config.get("error_threshold", 0.8)
        )
        print()  # 空行

    async def _handle_conversation(self, user_input: str):
        """
        处理正常对话

        Args:
            user_input: 用户输入
        """
        self.session_stats["queries"] += 1

        # 1. 添加用户消息
        await self.manager.add_message("user", user_input)

        # 2. 构建上下文
        context = await self.manager.get_context(current_query=user_input)

        # 3. 调用LLM
        print_colored("🤖 助手> ", "green", bold=True)
        print("🔄 正在调用API...\n")

        try:
            # 计算输入token
            input_tokens = self.client.count_messages_tokens(context)

            # 调用API（流式输出）
            response = await self.client.chat_with_retry(
                messages=context,
                stream=True
            )

            # 计算成本
            output_tokens = self.client.count_tokens(response)
            cost = (
                estimate_cost(input_tokens, "input", self.client.model) +
                estimate_cost(output_tokens, "output", self.client.model)
            )

            self.session_stats["api_calls"] += 1
            self.session_stats["total_cost"] += cost

            # 4. 添加助手响应
            await self.manager.add_message("assistant", response)

            # 显示简要信息
            print(f"\n💰 本次成本: ${cost:.4f}")

        except Exception as e:
            print(f"\n❌ API调用失败: {e}")
            print("请重试或检查配置\n")

    async def _handle_command(self, command: str) -> bool:
        """
        处理特殊命令

        Args:
            command: 命令字符串

        Returns:
            是否继续运行
        """
        cmd = command.lower().split()[0]

        if cmd == "/help":
            self._show_help()

        elif cmd == "/stats":
            self._show_stats()

        elif cmd == "/history":
            self._show_history()

        elif cmd == "/compress":
            await self._manual_compress()

        elif cmd == "/reset":
            self._reset_conversation()

        elif cmd == "/config":
            self._show_config()

        elif cmd == "/test":
            await self._test_connection()

        elif cmd == "/compare":
            await self._compare_compression()

        elif cmd == "/export":
            self._export_history()

        elif cmd == "/view":
            await self._view_compressed()

        elif cmd == "/context":
            await self._show_current_context()

        elif cmd == "/quit" or cmd == "/exit":
            return False

        else:
            print(f"❌ 未知命令: {command}")
            print("输入 /help 查看所有命令")

        return True

    def _show_help(self):
        """
        显示帮助信息
        """
        print("\n" + "=" * 60)
        print_colored("📖 可用命令", "cyan", bold=True)
        print("=" * 60)

        commands = [
            ("/help", "显示此帮助信息"),
            ("/stats", "显示统计信息"),
            ("/history", "查看对话历史（简要）"),
            ("/view", "查看压缩后的完整内容"),
            ("/context", "查看当前发送给LLM的上下文"),
            ("/compress", "手动触发压缩"),
            ("/reset", "重置对话（保留知识库）"),
            ("/config", "查看当前配置"),
            ("/test", "测试API连接"),
            ("/compare", "对比压缩效果"),
            ("/export", "导出对话历史"),
            ("/quit", "退出程序"),
        ]

        for cmd, desc in commands:
            print(f"  {cmd:<15} - {desc}")

        print("=" * 60 + "\n")

    def _show_stats(self):
        """
        显示统计信息
        """
        stats = self.manager.get_statistics()

        # 添加会话统计
        stats["📡 API统计"] = {
            "总查询次数": self.session_stats["queries"],
            "API调用次数": self.session_stats["api_calls"],
            "预估总成本": f"${self.session_stats['total_cost']:.4f}"
        }

        print_statistics(stats)

    def _show_history(self):
        """
        显示对话历史
        """
        print("\n" + "=" * 60)
        print_colored("📜 对话历史", "cyan", bold=True)
        print("=" * 60 + "\n")

        all_messages = self.manager.storage.get_all_messages()

        if not all_messages:
            print("暂无对话历史\n")
            return

        for i, msg in enumerate(all_messages, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            compressed = msg.get("compressed", False)
            tokens = msg.get("tokens", 0)

            emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️ "}.get(role, "❓")
            tag = " [压缩]" if compressed else ""

            print(f"{i}. {emoji} {role}{tag} ({tokens} tokens)")

            # 截断长内容
            if len(content) > 200:
                content = content[:200] + "..."

            print(f"   {content}")
            print()

        print("=" * 60 + "\n")

    async def _manual_compress(self):
        """
        手动触发压缩
        """
        print("\n🔄 手动触发压缩...\n")

        result = await self.manager.compress_if_needed(force=True)

        if result.get("compressed"):
            print(f"\n✅ 压缩完成！")
            print(f"  节省Token: {result['saved_tokens']:,}")
            print(f"  压缩率: {result['compression_ratio']*100:.1f}%")
            print(f"  新使用率: {result['new_usage']*100:.0f}%\n")
        else:
            print(f"\n⚠️  {result.get('reason', '无法压缩')}\n")

    def _reset_conversation(self):
        """
        重置对话
        """
        print("\n⚠️  确认重置对话？(y/n): ", end="")
        confirm = input().strip().lower()

        if confirm == 'y':
            self.manager.reset()
            self.session_stats = {
                "queries": 0,
                "api_calls": 0,
                "total_cost": 0.0
            }
            print("\n✅ 对话已重置，开始新的会话\n")
        else:
            print("\n❌ 取消重置\n")

    def _show_config(self):
        """
        显示当前配置
        """
        print("\n" + "=" * 60)
        print_colored("⚙️  当前配置", "cyan", bold=True)
        print("=" * 60)

        config_display = {
            "提供商": self.config.get("provider", "unknown"),
            "模型": self.config.get("model", "unknown"),
            "最大Tokens": f"{self.config.get('max_tokens', 8000):,}",
            "温度": self.config.get("temperature", 0.7),
            "警告阈值": f"{self.config.get('warning_threshold', 0.6)*100:.0f}%",
            "错误阈值": f"{self.config.get('error_threshold', 0.8)*100:.0f}%",
            "压缩阈值": f"{self.config.get('auto_compact_threshold', 0.92)*100:.0f}%",
        }

        for key, value in config_display.items():
            print(f"  {key}: {value}")

        print("=" * 60 + "\n")

    async def _compare_compression(self):
        """
        对比压缩效果
        """
        print("\n" + "=" * 60)
        print_colored("📊 压缩效果对比测试", "cyan", bold=True)
        print("=" * 60 + "\n")

        # 获取当前消息
        all_messages = self.manager.storage.get_all_messages()

        if len(all_messages) < 3:
            print("❌ 消息数量太少，无法进行对比测试\n")
            return

        # 测试问题
        test_query = "总结一下我们之前讨论的要点"
        print(f"测试问题: \"{test_query}\"\n")

        try:
            # 【测试1: 使用当前上下文（可能包含压缩）】
            print("【当前上下文】")
            current_context = await self.manager.get_context(test_query)
            current_tokens = self.client.count_messages_tokens(current_context)

            print(f"🔄 正在调用API ({len(current_context)}条消息, {current_tokens:,} tokens)...\n")

            import time
            start_time = time.time()
            current_response = await self.client.chat(current_context + [
                {"role": "user", "content": test_query}
            ], stream=False)
            current_time = time.time() - start_time

            current_output_tokens = self.client.count_tokens(current_response)
            current_cost = (
                estimate_cost(current_tokens, "input", self.client.model) +
                estimate_cost(current_output_tokens, "output", self.client.model)
            )

            print(f"\n📊 响应质量: {'⭐' * min(5, len(current_response)//50)} ({len(current_response)}字符)")
            print(f"⏱️  响应时间: {current_time:.1f}秒")
            print(f"💰 成本估算: ${current_cost:.4f}")

            # 显示对比总结
            print("\n" + "=" * 60)
            print_colored("✅ 对比测试完成", "green", bold=True)
            print("=" * 60)

            print(f"\n当前系统已自动优化上下文：")
            print(f"  • Token使用: {current_tokens:,}")
            print(f"  • 响应时间: {current_time:.1f}秒")
            print(f"  • 估算成本: ${current_cost:.4f}")

            if self.manager.stats["compressions"] > 0:
                print(f"\n历史压缩统计:")
                print(f"  • 压缩次数: {self.manager.stats['compressions']}")
                print(f"  • 总节省: {self.manager.stats['total_tokens_saved']:,} tokens")
                print(f"  • 平均压缩率: {self.manager.stats['avg_compression_ratio']*100:.1f}%")

            print("\n" + "=" * 60 + "\n")

        except Exception as e:
            print(f"\n❌ 对比测试失败: {e}\n")

    def _export_history(self):
        """
        导出对话历史
        """
        print("\n📤 导出对话历史...")

        output_path = self.manager.export_history()

        if output_path:
            print(f"✅ 历史已导出: {output_path}")

            # 询问是否导出知识库
            export_kb = input("\n是否同时导出知识库？(y/n): ").strip().lower()
            if export_kb == 'y':
                kb_path = self.manager.knowledge_base.export_markdown()
                if kb_path:
                    print(f"✅ 知识库已导出: {kb_path}")

        print()

    async def _view_compressed(self):
        """
        查看压缩后的完整内容
        """
        print("\n" + "=" * 60)
        print_colored("📝 压缩后的上下文内容", "cyan", bold=True)
        print("=" * 60 + "\n")

        # 获取中期存储（压缩后的内容）
        mid_term = self.manager.storage.get_mid_term()

        if not mid_term:
            print("⚠️  暂无压缩内容\n")
            print("提示: 当Token使用率达到92%时会自动压缩")
            print("或使用 /compress 命令手动触发压缩\n")
            return

        print(f"找到 {len(mid_term)} 个压缩片段:\n")

        for i, msg in enumerate(mid_term, 1):
            print("─" * 60)
            print(f"压缩片段 #{i}")
            print("─" * 60)

            # 显示元数据
            compressed = msg.get("compressed", False)
            original_count = msg.get("original_count", "未知")
            tokens = msg.get("tokens", 0)
            timestamp = msg.get("timestamp", 0)

            print(f"📊 元数据:")
            print(f"  • 压缩状态: {'✅ 已压缩' if compressed else '❌ 未压缩'}")
            print(f"  • 原始消息数: {original_count}条")
            print(f"  • Token数: {tokens:,}")

            if timestamp:
                from utils import format_timestamp
                print(f"  • 创建时间: {format_timestamp(timestamp)}")

            print(f"\n📄 完整内容:\n")

            # 显示完整内容
            content = msg.get("content", "")
            print(content)
            print()

        print("=" * 60)
        print(f"💡 提示: 这些内容会在构建上下文时自动包含\n")

    async def _show_current_context(self):
        """
        显示当前将要发送给LLM的上下文
        """
        print("\n" + "=" * 60)
        print_colored("🔍 当前LLM上下文", "cyan", bold=True)
        print("=" * 60 + "\n")

        # 构建当前上下文（不包含用户查询）
        context = await self.manager.get_context(current_query=None)

        if not context:
            print("⚠️  当前上下文为空\n")
            return

        print(f"上下文包含 {len(context)} 条消息:\n")

        # 计算总token数
        total_tokens = self.client.count_messages_tokens(context)
        usage_percent = (total_tokens / self.manager.max_tokens) * 100

        for i, msg in enumerate(context, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            tokens = msg.get("tokens", 0)

            # 特殊标记
            compressed = msg.get("compressed", False)
            injected = msg.get("injected", False)
            from_kb = msg.get("from_knowledge_base", False)

            # 构建标签
            tags = []
            if compressed:
                tags.append("压缩")
            if injected:
                tags.append("动态注入")
            if from_kb:
                tags.append("知识库")

            tag_str = f" [{', '.join(tags)}]" if tags else ""

            emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️ "}.get(role, "❓")

            print(f"{i}. {emoji} {role}{tag_str}")
            print(f"   Token: {tokens:,}")

            # 显示内容预览或完整内容
            if len(content) > 300:
                print(f"   预览: {content[:300]}...")
                print(f"   [完整长度: {len(content)}字符]")
            else:
                print(f"   内容: {content}")

            print()

        print("─" * 60)
        print(f"📊 上下文统计:")
        print(f"  • 总Token数: {total_tokens:,} / {self.manager.max_tokens:,}")
        print(f"  • 使用率: {usage_percent:.1f}%")
        print(f"  • 剩余空间: {self.manager.max_tokens - total_tokens:,} tokens")

        # 显示颜色提示
        if usage_percent >= 80:
            status = "🔴 高 - 建议压缩"
        elif usage_percent >= 60:
            status = "🟡 中等"
        else:
            status = "🟢 正常"

        print(f"  • 状态: {status}")
        print("=" * 60 + "\n")

        # 提供查看完整内容的选项
        if any(len(msg.get("content", "")) > 300 for msg in context):
            show_full = input("是否显示所有消息的完整内容？(y/n): ").strip().lower()
            if show_full == 'y':
                print("\n" + "=" * 60)
                print_colored("📄 完整上下文内容", "cyan", bold=True)
                print("=" * 60 + "\n")

                for i, msg in enumerate(context, 1):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")

                    print(f"{'─' * 60}")
                    print(f"消息 #{i} - {role}")
                    print(f"{'─' * 60}")
                    print(content)
                    print()

                print("=" * 60 + "\n")

    def _print_goodbye(self):
        """
        显示退出信息
        """
        print("\n" + "=" * 60)
        print_colored("👋 感谢使用上下文工程演示系统！", "cyan", bold=True)
        print("=" * 60)

        # 显示最终统计
        print("\n📊 本次会话统计:")
        print(f"  • 查询次数: {self.session_stats['queries']}")
        print(f"  • API调用: {self.session_stats['api_calls']}")
        print(f"  • 总成本: ${self.session_stats['total_cost']:.4f}")
        print(f"  • 压缩次数: {self.manager.stats['compressions']}")
        print(f"  • 节省Token: {self.manager.stats['total_tokens_saved']:,}")

        print("\n" + "=" * 60 + "\n")


async def main():
    """
    主入口函数
    """
    # 解析命令行参数
    use_mock = "--mock" in sys.argv or "-m" in sys.argv
    interactive = "--interactive" in sys.argv or "-i" in sys.argv

    # 加载配置
    try:
        config = load_config(interactive=interactive)
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        print("请运行 python config_loader.py --interactive 配置系统")
        return

    # 创建并启动演示
    demo = InteractiveDemo(config, use_mock=use_mock)
    await demo.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()
