"""
默认配置参数模块

定义所有系统默认配置和阈值
"""

import os
from typing import Dict
from pathlib import Path

# ==================== 加载环境变量 ====================

def load_env():
    """
    从.env文件加载环境变量
    支持Windows和其他操作系统
    """
    env_file = Path(__file__).parent / ".env"

    if not env_file.exists():
        return

    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith("#"):
                    continue

                # 解析键值对
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # 设置环境变量（如果尚未设置）
                    if key and not os.getenv(key):
                        os.environ[key] = value
    except Exception as e:
        print(f"⚠️  警告: 无法加载.env文件: {e}")

# 自动加载.env文件
load_env()

# ==================== Token限制配置 ====================

# 模拟的上下文窗口大小
MAX_TOKENS = 8000

# 警告阈值（60% - 黄色警告）
WARNING_THRESHOLD = 0.6

# 错误阈值（80% - 红色警告）
ERROR_THRESHOLD = 0.8

# 自动压缩阈值（92% - 触发自动压缩）
AUTO_COMPACT_THRESHOLD = 0.92


# ==================== 存储配置 ====================

# 短期记忆保留的消息数（最近的N条消息完整保留）
SHORT_TERM_SIZE = 5

# 中期记忆最大消息数（压缩后的历史）
MID_TERM_SIZE = 30

# 长期知识库文件路径
KNOWLEDGE_BASE_PATH = "./workspace/knowledge.json"

# 工作空间目录
WORKSPACE_DIR = "./workspace"


# ==================== 压缩配置 ====================

# 压缩方法 ("rule", "llm", "hybrid")
COMPRESSION_METHOD = "hybrid"  # 默认使用混合方法

# 目标压缩率（压缩后保留70%的信息）
TARGET_COMPRESSION_RATIO = 0.7

# 最低信息保留率（至少保留90%的关键信息）
MIN_QUALITY_RETENTION = 0.9

# LLM压缩相关配置
USE_LLM_COMPRESSION = False  # 默认关闭，避免意外消耗API
LLM_COMPRESSION_PROVIDER = "openai"  # "openai", "anthropic" 或 "qwen"
LLM_COMPRESSION_MODEL = "gpt-4o-mini"  # 压缩使用的模型
LLM_COMPRESSION_TEMPERATURE = 0.3  # 较低的温度确保稳定输出
LLM_COMPRESSION_MAX_TOKENS = 2000  # 压缩摘要的最大token数

# Qwen API配置（阿里云通义千问）
QWEN_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # Qwen API地址

# 混合压缩阈值（消息数超过此值才使用LLM）
HYBRID_LLM_THRESHOLD = 10

# 消息分类权重
MESSAGE_IMPORTANCE_WEIGHTS = {
    "critical": 1.0,      # 必须保留（错误、关键决策）
    "important": 0.7,     # 可以压缩（重要讨论、代码）
    "contextual": 0.4,    # 提取要点（一般对话）
    "redundant": 0.1      # 可以删除（重复内容）
}

# 实体重要性权重
ENTITY_IMPORTANCE_WEIGHTS = {
    "errors": 1.0,        # 错误信息最重要
    "files": 0.8,         # 文件路径
    "functions": 0.7,     # 函数名
    "classes": 0.7,       # 类名
    "variables": 0.5,     # 变量名
    "imports": 0.4        # 导入语句
}


# ==================== 注入配置 ====================

# 相关性阈值（低于此值的内容不会被注入）
RELEVANCE_THRESHOLD = 0.5

# 最多注入的片段数量
MAX_INJECTED_SEGMENTS = 3

# 意图分析关键词权重
INTENT_KEYWORD_WEIGHTS = {
    "high": 1.0,      # 强相关（错误、文件名、函数名）
    "medium": 0.6,    # 中等相关（类型、概念）
    "low": 0.3        # 弱相关（一般词汇）
}


# ==================== LLM API配置 ====================

# 默认API提供商
DEFAULT_PROVIDER = "openai"

# 默认模型
DEFAULT_MODELS = {
    "openai": "gpt-3.5-turbo",
    "anthropic": "claude-3-5-sonnet-20241022",
    "ollama": "qwen2.5:7b"
}

# API超时时间（秒）
API_TIMEOUT = 60

# 流式输出
DEFAULT_STREAM = True

# 重试次数
MAX_RETRIES = 3

# 重试延迟（秒）
RETRY_DELAY = 2

# 温度参数（控制输出随机性）
DEFAULT_TEMPERATURE = 0.7

# 最大生成tokens
DEFAULT_MAX_OUTPUT_TOKENS = 2000


# ==================== 显示配置 ====================

# 进度条宽度
PROGRESS_BAR_WIDTH = 40

# 统计信息刷新间隔（秒）
STATS_REFRESH_INTERVAL = 1.0

# 终端颜色主题
COLOR_THEME = {
    "primary": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "blue",
    "muted": "white"
}

# 消息角色显示
ROLE_DISPLAY = {
    "user": "💬 用户",
    "assistant": "🤖 助手",
    "system": "⚙️  系统"
}


# ==================== 性能配置 ====================

# 压缩操作最大耗时（秒）
MAX_COMPRESSION_TIME = 5.0

# 上下文注入最大延迟（秒）
MAX_INJECTION_DELAY = 0.5

# 最大内存使用（MB）- 用于监控
MAX_MEMORY_MB = 512


# ==================== 调试配置 ====================

# 是否启用调试模式
DEBUG_MODE = False

# 是否显示详细日志
VERBOSE = False

# 是否保存压缩历史
SAVE_COMPRESSION_HISTORY = True

# 压缩历史保存路径
COMPRESSION_HISTORY_PATH = "./workspace/compression_history.json"


# ==================== 配置验证 ====================

def validate_config(config: Dict) -> bool:
    """
    验证配置的有效性

    Args:
        config: 配置字典

    Returns:
        是否有效
    """
    try:
        # 检查必需的配置项
        required_keys = ["max_tokens", "warning_threshold", "error_threshold"]
        for key in required_keys:
            if key not in config:
                print(f"❌ 缺少必需配置: {key}")
                return False

        # 检查阈值范围
        if not (0 < config.get("warning_threshold", 0) < 1):
            print("❌ warning_threshold必须在0-1之间")
            return False

        if not (0 < config.get("error_threshold", 0) < 1):
            print("❌ error_threshold必须在0-1之间")
            return False

        # 检查阈值顺序
        if config.get("warning_threshold", 0) >= config.get("error_threshold", 1):
            print("❌ warning_threshold必须小于error_threshold")
            return False

        return True

    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False


def get_default_config() -> Dict:
    """
    获取默认配置

    Returns:
        默认配置字典
    """
    return {
        # Token配置
        "max_tokens": MAX_TOKENS,
        "warning_threshold": WARNING_THRESHOLD,
        "error_threshold": ERROR_THRESHOLD,
        "auto_compact_threshold": AUTO_COMPACT_THRESHOLD,

        # 存储配置
        "short_term_size": SHORT_TERM_SIZE,
        "mid_term_size": MID_TERM_SIZE,
        "workspace_dir": WORKSPACE_DIR,

        # 压缩配置
        "target_compression_ratio": TARGET_COMPRESSION_RATIO,
        "min_quality_retention": MIN_QUALITY_RETENTION,

        # 注入配置
        "relevance_threshold": RELEVANCE_THRESHOLD,
        "max_injected_segments": MAX_INJECTED_SEGMENTS,

        # API配置
        "provider": DEFAULT_PROVIDER,
        "model": DEFAULT_MODELS.get(DEFAULT_PROVIDER),
        "temperature": DEFAULT_TEMPERATURE,
        "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
        "stream": DEFAULT_STREAM,
        "timeout": API_TIMEOUT,

        # 显示配置
        "progress_bar_width": PROGRESS_BAR_WIDTH,
        "color_theme": COLOR_THEME,

        # 调试配置
        "debug": DEBUG_MODE,
        "verbose": VERBOSE
    }


if __name__ == "__main__":
    # 测试配置
    print("🧪 测试配置模块...\n")

    config = get_default_config()
    print("默认配置:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    print(f"\n验证结果: {'✅ 有效' if validate_config(config) else '❌ 无效'}")
