#!/usr/bin/env python3
"""
LLM压缩配置向导 - Windows友好版本

帮助用户快速配置LLM驱动的上下文压缩功能
"""

import os
import sys
from pathlib import Path


def print_header():
    """打印欢迎头部"""
    print("=" * 70)
    print("🤖 LLM压缩配置向导 - Windows友好版本")
    print("=" * 70)
    print()
    print("本向导将帮助你配置LLM驱动的上下文压缩功能。")
    print()


def print_section(title):
    """打印章节标题"""
    print()
    print("─" * 70)
    print(f"📋 {title}")
    print("─" * 70)
    print()


def get_choice(prompt, choices, default=None):
    """获取用户选择"""
    while True:
        if default:
            user_input = input(f"{prompt} (默认: {default}): ").strip()
            if not user_input:
                return default
        else:
            user_input = input(f"{prompt}: ").strip()

        if user_input in choices:
            return user_input

        print(f"❌ 无效选择，请输入: {', '.join(choices)}")
        print()


def get_input(prompt, default=None, required=True):
    """获取用户输入"""
    while True:
        if default:
            user_input = input(f"{prompt} (默认: {default}): ").strip()
            if not user_input:
                return default
        else:
            user_input = input(f"{prompt}: ").strip()

        if user_input or not required:
            return user_input

        print("❌ 此项为必填项，请输入内容")
        print()


def main():
    """主配置流程"""
    print_header()

    # 步骤1: 是否启用LLM压缩
    print_section("步骤1: 是否启用LLM压缩？")
    print("LLM压缩可以将压缩率从30-40%提升至60-75%，但需要调用API（有小额成本）。")
    print()
    print("选项:")
    print("  y - 启用（推荐，如果你有OpenAI或Anthropic API密钥）")
    print("  n - 不启用（使用免费的规则压缩方法）")
    print()

    enable_llm = get_choice("是否启用LLM压缩？", ["y", "n"], default="n")

    if enable_llm == "n":
        print()
        print("✅ 将使用免费的规则压缩方法（AU2算法）")
        print("   压缩率: 30-40%，速度快，成本为零")
        print()

        # 只需要更新config.py
        config_content = """
# LLM压缩配置
USE_LLM_COMPRESSION = False
"""
        print("配置完成！系统将使用规则压缩方法。")
        return

    # 步骤2: 选择提供商
    print_section("步骤2: 选择LLM提供商")
    print("支持的提供商:")
    print()
    print("  1. OpenAI")
    print("     - 模型: gpt-4o-mini (性价比最高)")
    print("     - 成本: $0.15/1M输入 + $0.60/1M输出")
    print("     - 需要: OPENAI_API_KEY")
    print()
    print("  2. Anthropic")
    print("     - 模型: claude-3-5-haiku (性价比高)")
    print("     - 成本: $0.80/1M输入 + $4.00/1M输出")
    print("     - 需要: ANTHROPIC_API_KEY")
    print()
    print("  3. Qwen (阿里云通义千问，推荐国内用户)")
    print("     - 模型: qwen-plus-latest (性价比极高)")
    print("     - 成本: ¥0.004/1K输入 + ¥0.012/1K输出")
    print("     - 需要: DASHSCOPE_API_KEY")
    print()

    provider_choice = get_choice("选择提供商", ["1", "2", "3"], default="1")

    if provider_choice == "1":
        provider = "openai"
        default_model = "gpt-4o-mini"
        api_key_name = "OPENAI_API_KEY"
        print()
        print("✅ 已选择: OpenAI")
    elif provider_choice == "2":
        provider = "anthropic"
        default_model = "claude-3-5-haiku-20241022"
        api_key_name = "ANTHROPIC_API_KEY"
        print()
        print("✅ 已选择: Anthropic")
    else:
        provider = "qwen"
        default_model = "qwen-plus-latest"
        api_key_name = "DASHSCOPE_API_KEY"
        print()
        print("✅ 已选择: Qwen (通义千问)")

    # 步骤3: 输入API密钥
    print_section("步骤3: 输入API密钥")
    print(f"请输入你的 {api_key_name}")
    print()

    if provider == "openai":
        print("💡 获取方式: https://platform.openai.com/api-keys")
        print("   格式: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    elif provider == "anthropic":
        print("💡 获取方式: https://console.anthropic.com/settings/keys")
        print("   格式: sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    else:  # qwen
        print("💡 获取方式: https://dashscope.console.aliyun.com/apiKey")
        print("   格式: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        print("   (需要先注册阿里云账号并开通DashScope服务)")
    print()

    api_key = get_input(f"请输入 {api_key_name}", required=True)

    # 步骤4: 选择模型
    print_section("步骤4: 选择模型")

    if provider == "openai":
        print("可用模型:")
        print("  1. gpt-4o-mini (推荐，性价比最高)")
        print("  2. gpt-4o (质量最好，成本较高)")
        print("  3. gpt-3.5-turbo (经济实惠)")
        print()
        model_choice = get_choice("选择模型", ["1", "2", "3"], default="1")

        models = {
            "1": "gpt-4o-mini",
            "2": "gpt-4o",
            "3": "gpt-3.5-turbo"
        }
        model = models[model_choice]
    elif provider == "anthropic":
        print("可用模型:")
        print("  1. claude-3-5-haiku-20241022 (推荐，性价比高)")
        print("  2. claude-3-5-sonnet-20241022 (平衡质量和成本)")
        print("  3. claude-3-opus-20240229 (最高质量)")
        print()
        model_choice = get_choice("选择模型", ["1", "2", "3"], default="1")

        models = {
            "1": "claude-3-5-haiku-20241022",
            "2": "claude-3-5-sonnet-20241022",
            "3": "claude-3-opus-20240229"
        }
        model = models[model_choice]
    else:  # qwen
        print("可用模型:")
        print("  1. qwen-plus-latest (推荐，性价比极高)")
        print("  2. qwen-turbo-latest (更快，更便宜)")
        print("  3. qwen-max-latest (最高质量)")
        print()
        model_choice = get_choice("选择模型", ["1", "2", "3"], default="1")

        models = {
            "1": "qwen-plus-latest",
            "2": "qwen-turbo-latest",
            "3": "qwen-max-latest"
        }
        model = models[model_choice]

    print()
    print(f"✅ 已选择: {model}")

    # 步骤5: 混合模式阈值
    print_section("步骤5: 配置混合模式")
    print("混合模式会智能选择压缩方法:")
    print("  - 消息少: 使用规则方法（免费）")
    print("  - 消息多: 使用LLM方法（高质量）")
    print()
    print("请设置阈值（消息数超过此值才使用LLM）:")
    print("  - 推荐: 10（平衡质量和成本）")
    print("  - 节省: 20（更少使用LLM）")
    print("  - 质量优先: 5（更多使用LLM）")
    print()

    threshold = get_input("阈值", default="10")

    try:
        threshold = int(threshold)
        if threshold < 1:
            threshold = 10
    except:
        threshold = 10

    print()
    print(f"✅ 阈值设置为: {threshold}")

    # 步骤6: 保存配置
    print_section("步骤6: 保存配置")
    print("配置将保存到以下位置:")
    print("  1. .env 文件（存储API密钥）")
    print("  2. config.py 文件（存储配置选项）")
    print()

    confirm = get_choice("确认保存配置？", ["y", "n"], default="y")

    if confirm == "n":
        print()
        print("❌ 配置已取消")
        return

    # 创建或更新.env文件
    env_file = Path(".env")
    env_lines = []

    # 如果文件存在，读取现有内容
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            env_lines = f.readlines()

    # 更新或添加配置
    key_name = f"{provider.upper()}_API_KEY"
    key_found = False

    for i, line in enumerate(env_lines):
        if line.strip().startswith(f"{key_name}="):
            env_lines[i] = f"{key_name}={api_key}\n"
            key_found = True
            break

    if not key_found:
        if env_lines and not env_lines[-1].endswith("\n"):
            env_lines.append("\n")
        env_lines.append(f"\n# LLM压缩API密钥\n")
        env_lines.append(f"{key_name}={api_key}\n")

    # 保存.env文件
    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(env_lines)

    print()
    print(f"✅ API密钥已保存到 .env 文件")

    # 更新config.py
    config_file = Path("config.py")

    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            config_content = f.read()

        # 更新配置项
        config_updates = {
            "USE_LLM_COMPRESSION = False": "USE_LLM_COMPRESSION = True",
            f'LLM_COMPRESSION_PROVIDER = "openai"': f'LLM_COMPRESSION_PROVIDER = "{provider}"',
            f'LLM_COMPRESSION_MODEL = "gpt-4o-mini"': f'LLM_COMPRESSION_MODEL = "{model}"',
            f'HYBRID_LLM_THRESHOLD = 10': f'HYBRID_LLM_THRESHOLD = {threshold}'
        }

        for old, new in config_updates.items():
            # 更灵活的替换，支持不同的引号和值
            if "USE_LLM_COMPRESSION" in old:
                import re
                config_content = re.sub(
                    r'USE_LLM_COMPRESSION\s*=\s*False',
                    'USE_LLM_COMPRESSION = True',
                    config_content
                )
            elif "LLM_COMPRESSION_PROVIDER" in old:
                import re
                config_content = re.sub(
                    r'LLM_COMPRESSION_PROVIDER\s*=\s*["\'].*?["\']',
                    f'LLM_COMPRESSION_PROVIDER = "{provider}"',
                    config_content
                )
            elif "LLM_COMPRESSION_MODEL" in old:
                import re
                config_content = re.sub(
                    r'LLM_COMPRESSION_MODEL\s*=\s*["\'].*?["\']',
                    f'LLM_COMPRESSION_MODEL = "{model}"',
                    config_content
                )
            elif "HYBRID_LLM_THRESHOLD" in old:
                import re
                config_content = re.sub(
                    r'HYBRID_LLM_THRESHOLD\s*=\s*\d+',
                    f'HYBRID_LLM_THRESHOLD = {threshold}',
                    config_content
                )

        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

        print(f"✅ 配置已更新到 config.py 文件")

    # 完成
    print()
    print("=" * 70)
    print("🎉 配置完成！")
    print("=" * 70)
    print()
    print("📊 配置摘要:")
    print(f"  • LLM压缩: 已启用")
    print(f"  • 提供商: {provider}")
    print(f"  • 模型: {model}")
    print(f"  • 混合阈值: {threshold} 条消息")
    print()
    print("💡 接下来:")
    print()
    print("  1. 测试配置:")
    print("     python test_llm_compression.py")
    print()
    print("  2. 启动Web服务:")
    print("     python web_server.py")
    print()
    print("  3. 查看详细文档:")
    print("     LLM_COMPRESSION_GUIDE.md")
    print()
    print("📌 注意:")
    print("  • .env 文件包含你的API密钥，请勿提交到Git")
    print("  • 已自动添加到 .gitignore")
    print()

    # 更新.gitignore
    gitignore_file = Path(".gitignore")
    if gitignore_file.exists():
        with open(gitignore_file, "r", encoding="utf-8") as f:
            gitignore_content = f.read()

        if ".env" not in gitignore_content:
            with open(gitignore_file, "a", encoding="utf-8") as f:
                f.write("\n# 环境变量和API密钥\n")
                f.write(".env\n")
            print("✅ 已将 .env 添加到 .gitignore")

    print()
    print("祝使用愉快！ 🚀")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("❌ 配置已取消（用户中断）")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ 配置失败: {e}")
        sys.exit(1)
