"""
配置加载与管理模块

支持从多种来源加载配置:
1. 环境变量 (.env文件)
2. YAML配置文件 (config.yaml)
3. 命令行参数
4. 交互式配置向导（首次运行）

配置优先级: 命令行参数 > 环境变量 > 配置文件 > 默认值
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional
import json

# 尝试导入可选依赖
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("⚠️  pyyaml未安装，无法加载YAML配置（安装: pip install pyyaml）")

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  python-dotenv未安装，无法加载.env文件（安装: pip install python-dotenv）")

from config import get_default_config, validate_config


class ConfigLoader:
    """
    配置加载器

    支持多种配置来源，提供交互式配置向导
    """

    def __init__(self, config_path: str = "./config.yaml", env_path: str = "./.env"):
        """
        初始化配置加载器

        Args:
            config_path: YAML配置文件路径
            env_path: .env文件路径
        """
        self.config_path = config_path
        self.env_path = env_path
        self.config = get_default_config()

    def load_config(self, interactive: bool = False) -> Dict:
        """
        加载配置（按优先级合并所有来源）

        Args:
            interactive: 如果没有配置文件，是否启动交互式向导

        Returns:
            最终配置字典
        """
        # 1. 从默认配置开始
        config = get_default_config()

        # 2. 检查配置文件是否存在
        config_exists = os.path.exists(self.config_path)
        env_exists = os.path.exists(self.env_path)

        # 如果没有任何配置文件且允许交互，启动配置向导
        if not config_exists and not env_exists and interactive:
            print("\n🚀 检测到首次运行，启动配置向导...\n")
            config = self.interactive_setup()
            return config

        # 3. 加载配置文件（YAML）
        if config_exists:
            file_config = self._load_yaml_config()
            if file_config:
                config.update(file_config)
                print(f"✅ 已加载配置文件: {self.config_path}")

        # 4. 加载环境变量（.env）
        if env_exists:
            env_config = self._load_env_config()
            if env_config:
                config.update(env_config)
                print(f"✅ 已加载环境变量: {self.env_path}")

        # 5. 加载命令行参数（如果需要）
        # cli_config = self._load_cli_args()
        # config.update(cli_config)

        # 6. 验证配置
        if not validate_config(config):
            print("⚠️  配置验证失败，使用默认配置")
            config = get_default_config()

        self.config = config
        return config

    def _load_yaml_config(self) -> Optional[Dict]:
        """
        从YAML文件加载配置

        Returns:
            配置字典，失败返回None
        """
        if not YAML_AVAILABLE:
            print("⚠️  无法加载YAML配置文件（pyyaml未安装）")
            return None

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config if config else {}
        except Exception as e:
            print(f"⚠️  加载YAML配置失败: {e}")
            return None

    def _load_env_config(self) -> Dict:
        """
        从.env文件加载配置

        Returns:
            配置字典
        """
        config = {}

        if DOTENV_AVAILABLE:
            load_dotenv(self.env_path)

        # 读取环境变量
        if os.getenv("LLM_PROVIDER"):
            config["provider"] = os.getenv("LLM_PROVIDER")

        if os.getenv("LLM_API_KEY"):
            config["api_key"] = os.getenv("LLM_API_KEY")

        if os.getenv("LLM_BASE_URL"):
            config["base_url"] = os.getenv("LLM_BASE_URL")

        if os.getenv("LLM_MODEL"):
            config["model"] = os.getenv("LLM_MODEL")

        if os.getenv("LLM_MAX_TOKENS"):
            try:
                config["max_tokens"] = int(os.getenv("LLM_MAX_TOKENS"))
            except ValueError:
                pass

        if os.getenv("LLM_TEMPERATURE"):
            try:
                config["temperature"] = float(os.getenv("LLM_TEMPERATURE"))
            except ValueError:
                pass

        return config

    def interactive_setup(self) -> Dict:
        """
        交互式配置向导（首次运行时）

        Returns:
            用户配置的字典
        """
        print("=" * 60)
        print("🚀 欢迎使用上下文工程演示系统！")
        print("=" * 60)
        print()

        config = get_default_config()

        # 1. 选择API提供商
        print("1️⃣  选择API提供商:")
        print("   [1] OpenAI (GPT-3.5/4)")
        print("   [2] Anthropic (Claude)")
        print("   [3] Ollama (本地模型)")
        print("   [4] 自定义API")
        print()

        provider_choice = self._get_input("请选择 (1-4)", default="1")
        provider_map = {
            "1": "openai",
            "2": "anthropic",
            "3": "ollama",
            "4": "custom"
        }
        config["provider"] = provider_map.get(provider_choice, "openai")

        # 2. 根据提供商配置API
        if config["provider"] in ["openai", "anthropic"]:
            print(f"\n2️⃣  配置 {config['provider'].upper()} API:")
            api_key = self._get_input("API Key", password=True)
            if api_key:
                config["api_key"] = api_key

            # 选择模型
            if config["provider"] == "openai":
                print("\n3️⃣  选择模型:")
                print("   [1] gpt-3.5-turbo (推荐, 便宜)")
                print("   [2] gpt-4")
                print("   [3] gpt-4-turbo")
                model_choice = self._get_input("请选择 (1-3)", default="1")
                model_map = {
                    "1": "gpt-3.5-turbo",
                    "2": "gpt-4",
                    "3": "gpt-4-turbo"
                }
                config["model"] = model_map.get(model_choice, "gpt-3.5-turbo")
            else:  # anthropic
                print("\n3️⃣  选择模型:")
                print("   [1] claude-3-5-sonnet-20241022 (推荐)")
                print("   [2] claude-3-opus")
                model_choice = self._get_input("请选择 (1-2)", default="1")
                model_map = {
                    "1": "claude-3-5-sonnet-20241022",
                    "2": "claude-3-opus-20240229"
                }
                config["model"] = model_map.get(model_choice, "claude-3-5-sonnet-20241022")

        elif config["provider"] == "ollama":
            print("\n2️⃣  配置 Ollama:")
            base_url = self._get_input("Base URL", default="http://localhost:11434")
            config["base_url"] = base_url

            print("\n3️⃣  选择模型:")
            print("   [1] qwen2.5:7b (推荐)")
            print("   [2] llama3.1:8b")
            print("   [3] 自定义")
            model_choice = self._get_input("请选择 (1-3)", default="1")
            if model_choice == "3":
                model = self._get_input("模型名称")
                config["model"] = model
            else:
                model_map = {"1": "qwen2.5:7b", "2": "llama3.1:8b"}
                config["model"] = model_map.get(model_choice, "qwen2.5:7b")

        else:  # custom
            print("\n2️⃣  配置自定义API:")
            base_url = self._get_input("Base URL")
            config["base_url"] = base_url

            api_key = self._get_input("API Key (可选)", password=True)
            if api_key:
                config["api_key"] = api_key

            model = self._get_input("模型名称")
            config["model"] = model

        # 4. 设置Token限制
        print("\n4️⃣  设置Token限制:")
        max_tokens = self._get_input("最大Tokens (建议4000-8000)", default="8000")
        try:
            config["max_tokens"] = int(max_tokens)
        except ValueError:
            config["max_tokens"] = 8000

        # 5. 保存配置
        print("\n✅ 配置完成！")
        save_choice = self._get_input("\n是否保存配置到文件？(y/n)", default="y")
        if save_choice.lower() == "y":
            self.save_config(config)
            print(f"✅ 配置已保存到 {self.config_path}")

        # 6. 测试连接
        test_choice = self._get_input("\n是否现在测试连接？(y/n)", default="y")
        if test_choice.lower() == "y":
            self._test_connection(config)

        print("\n" + "=" * 60)
        print("🎉 设置完成！即将启动演示系统...")
        print("=" * 60 + "\n")

        return config

    def save_config(self, config: Dict, format: str = "yaml"):
        """
        保存配置到文件

        Args:
            config: 配置字典
            format: 保存格式 (yaml/json/env)
        """
        try:
            if format == "yaml" and YAML_AVAILABLE:
                # 过滤掉不需要保存的配置
                save_config = {
                    "provider": config.get("provider"),
                    "model": config.get("model"),
                    "max_tokens": config.get("max_tokens"),
                    "temperature": config.get("temperature"),
                    "stream": config.get("stream", True)
                }

                # 添加API配置（不包含敏感信息）
                if config.get("base_url"):
                    save_config["base_url"] = config["base_url"]

                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(save_config, f, default_flow_style=False, allow_unicode=True)

                # 保存敏感信息到.env
                if config.get("api_key"):
                    with open(self.env_path, 'w', encoding='utf-8') as f:
                        f.write(f"LLM_API_KEY={config['api_key']}\n")
                    print(f"✅ API Key已保存到 {self.env_path}")

            elif format == "json":
                with open(self.config_path.replace('.yaml', '.json'), 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"❌ 保存配置失败: {e}")

    def _get_input(self, prompt: str, default: str = "", password: bool = False) -> str:
        """
        获取用户输入

        Args:
            prompt: 提示文本
            default: 默认值
            password: 是否为密码（隐藏输入）

        Returns:
            用户输入
        """
        if default:
            prompt_text = f"{prompt} [{default}]: "
        else:
            prompt_text = f"{prompt}: "

        if password:
            import getpass
            value = getpass.getpass(prompt_text)
        else:
            value = input(prompt_text)

        return value.strip() if value.strip() else default

    def _test_connection(self, config: Dict):
        """
        测试API连接

        Args:
            config: 配置字典
        """
        print("\n🔄 测试API连接...")

        try:
            # 这里只做简单的配置检查，实际连接测试在llm_client中
            required = []
            if config["provider"] in ["openai", "anthropic"]:
                if not config.get("api_key"):
                    required.append("API Key")

            if config["provider"] == "custom" and not config.get("base_url"):
                required.append("Base URL")

            if required:
                print(f"⚠️  缺少必需配置: {', '.join(required)}")
                print("✅ 配置已保存，但需要补充上述信息才能使用")
            else:
                print("✅ 配置检查通过！")
                print("   (实际连接测试将在启动时进行)")

        except Exception as e:
            print(f"❌ 连接测试失败: {e}")

    def validate_config(self, config: Dict) -> bool:
        """
        验证配置完整性

        Args:
            config: 配置字典

        Returns:
            是否有效
        """
        return validate_config(config)

    def print_config(self, config: Optional[Dict] = None):
        """
        打印当前配置（隐藏敏感信息）

        Args:
            config: 配置字典，为None则使用当前配置
        """
        if config is None:
            config = self.config

        print("\n📋 当前配置:")
        print("-" * 40)

        safe_config = config.copy()
        # 隐藏敏感信息
        if "api_key" in safe_config and safe_config["api_key"]:
            key = safe_config["api_key"]
            safe_config["api_key"] = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"

        for key, value in safe_config.items():
            if not key.startswith("_"):
                print(f"  {key}: {value}")

        print("-" * 40 + "\n")


def load_config(interactive: bool = False) -> Dict:
    """
    快捷函数：加载配置

    Args:
        interactive: 是否启用交互式向导

    Returns:
        配置字典
    """
    loader = ConfigLoader()
    return loader.load_config(interactive=interactive)


if __name__ == "__main__":
    # 测试配置加载
    print("🧪 测试配置加载模块...\n")

    loader = ConfigLoader()

    # 测试加载配置
    if "--interactive" in sys.argv:
        config = loader.interactive_setup()
    else:
        config = loader.load_config()

    # 打印配置
    loader.print_config(config)

    print("✅ 配置加载测试完成！")
