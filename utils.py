"""
工具函数模块

提供token计数、实体提取、格式化等辅助功能
"""

import re
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# 尝试导入tiktoken，如果失败则使用简单估算
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("⚠️  tiktoken未安装，使用简单token估算（安装: pip install tiktoken）")


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    计算文本的token数量

    Args:
        text: 要计算的文本
        model: 模型名称（用于选择正确的编码器）

    Returns:
        token数量
    """
    if TIKTOKEN_AVAILABLE:
        try:
            # 根据模型选择编码器
            if "gpt-4" in model:
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5" in model:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            elif "claude" in model:
                # Claude使用类似的编码，使用cl100k_base
                encoding = tiktoken.get_encoding("cl100k_base")
            else:
                encoding = tiktoken.get_encoding("cl100k_base")

            return len(encoding.encode(text))
        except Exception as e:
            # 如果编码失败，使用简单估算
            pass

    # 简单估算：平均每个token约4个字符（英文）或1.5个字符（中文）
    # 使用混合比例
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    other_chars = len(text) - chinese_chars

    estimated_tokens = int(chinese_chars / 1.5 + other_chars / 4)
    return max(estimated_tokens, 1)


def count_messages_tokens(messages: List[Dict], model: str = "gpt-3.5-turbo") -> int:
    """
    计算消息列表的总token数

    Args:
        messages: 消息列表
        model: 模型名称

    Returns:
        总token数
    """
    total = 0
    for msg in messages:
        # 消息格式的开销
        total += 4  # 每条消息的固定开销

        # 角色和内容
        total += count_tokens(msg.get("role", ""), model)
        total += count_tokens(msg.get("content", ""), model)

    total += 2  # 回复的固定开销
    return total


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    提取文本中的代码块

    Args:
        text: 包含代码块的文本

    Returns:
        代码块列表，每个包含language和code
    """
    # 匹配 ```language\ncode\n``` 格式
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)

    code_blocks = []
    for lang, code in matches:
        code_blocks.append({
            "language": lang or "text",
            "code": code.strip()
        })

    return code_blocks


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    提取文本中的关键实体

    Args:
        text: 要分析的文本

    Returns:
        实体字典，包含files, functions, variables, errors等
    """
    entities = {
        "files": [],
        "functions": [],
        "variables": [],
        "errors": [],
        "classes": [],
        "imports": []
    }

    # 文件路径: xxx.py, xxx.js, etc.
    file_pattern = r'\b[\w/\-\.]+\.(py|js|ts|java|cpp|c|h|json|yaml|yml|md|txt|sh)\b'
    entities["files"] = list(set(re.findall(file_pattern, text)))

    # 函数调用: function_name(
    func_pattern = r'\b([a-zA-Z_]\w*)\s*\('
    entities["functions"] = list(set(re.findall(func_pattern, text)))

    # 类定义: class ClassName
    class_pattern = r'class\s+([A-Z]\w*)'
    entities["classes"] = list(set(re.findall(class_pattern, text)))

    # 导入语句: import xxx, from xxx import
    import_pattern = r'(?:import|from)\s+([\w\.]+)'
    entities["imports"] = list(set(re.findall(import_pattern, text)))

    # 错误信息: Error, Exception, Failed
    error_pattern = r'(\w*(?:Error|Exception|Failed|Warning)\w*)'
    entities["errors"] = list(set(re.findall(error_pattern, text)))

    # 变量赋值: var_name =
    var_pattern = r'\b([a-z_]\w*)\s*='
    potential_vars = list(set(re.findall(var_pattern, text)))
    # 过滤掉常见的非变量词
    common_words = {'is', 'as', 'in', 'or', 'and', 'not', 'for', 'if', 'else'}
    entities["variables"] = [v for v in potential_vars if v not in common_words][:10]  # 限制数量

    return entities


def format_message(role: str, content: str, timestamp: Optional[float] = None) -> Dict:
    """
    格式化消息为标准格式

    Args:
        role: 消息角色 (user/assistant/system)
        content: 消息内容
        timestamp: 时间戳（可选）

    Returns:
        格式化的消息字典
    """
    return {
        "role": role,
        "content": content,
        "timestamp": timestamp or time.time(),
        "tokens": count_tokens(content)
    }


def format_timestamp(timestamp: float) -> str:
    """
    格式化时间戳为可读字符串

    Args:
        timestamp: Unix时间戳

    Returns:
        格式化的时间字符串
    """
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def calculate_time_distance(timestamp: float) -> str:
    """
    计算时间距离（多久之前）

    Args:
        timestamp: Unix时间戳

    Returns:
        人类可读的时间距离
    """
    distance = time.time() - timestamp

    if distance < 60:
        return f"{int(distance)}秒前"
    elif distance < 3600:
        return f"{int(distance/60)}分钟前"
    elif distance < 86400:
        return f"{int(distance/3600)}小时前"
    else:
        return f"{int(distance/86400)}天前"


def print_colored(text: str, color: str = "white", bold: bool = False):
    """
    打印彩色文本（使用ANSI转义码）

    Args:
        text: 要打印的文本
        color: 颜色名称
        bold: 是否加粗
    """
    colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m"
    }

    color_code = colors.get(color, colors["white"])
    bold_code = "\033[1m" if bold else ""
    reset_code = colors["reset"]

    print(f"{bold_code}{color_code}{text}{reset_code}")


def print_progress_bar(percentage: float, width: int = 40,
                       low_threshold: float = 0.6, high_threshold: float = 0.8):
    """
    打印进度条

    Args:
        percentage: 百分比 (0-1)
        width: 进度条宽度
        low_threshold: 低阈值（黄色警告）
        high_threshold: 高阈值（红色警告）
    """
    filled = int(width * percentage)
    bar = "▓" * filled + "░" * (width - filled)

    # 根据阈值选择颜色
    if percentage >= high_threshold:
        color = "red"
        status = "🔴 警告"
    elif percentage >= low_threshold:
        color = "yellow"
        status = "⚠️  警告"
    else:
        color = "green"
        status = "✅ 正常"

    print_colored(f"[Token使用率: {percentage*100:.0f}% {bar}] {status}", color)


def print_statistics(stats: Dict):
    """
    打印统计信息（格式化输出）

    Args:
        stats: 统计数据字典
    """
    print("\n" + "━" * 60)
    print_colored("📊 系统统计信息", "cyan", bold=True)
    print("━" * 60)

    for category, data in stats.items():
        print_colored(f"\n{category}:", "yellow", bold=True)
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  • {key}: {value}")
        else:
            print(f"  {data}")

    print("━" * 60 + "\n")


def estimate_cost(tokens: int, token_type: str = "input", model: str = "gpt-3.5-turbo") -> float:
    """
    估算API调用成本

    Args:
        tokens: token数量
        token_type: 类型 (input/output)
        model: 模型名称

    Returns:
        估算的成本（美元）
    """
    # 价格表（每1000 tokens的价格，单位：美元）
    prices = {
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
    }

    # 查找匹配的模型
    model_price = None
    for model_name, price in prices.items():
        if model_name in model.lower():
            model_price = price
            break

    # 如果没找到，使用默认价格
    if model_price is None:
        model_price = {"input": 0.002, "output": 0.003}

    price_per_token = model_price.get(token_type, 0.002) / 1000
    return tokens * price_per_token


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断长文本

    Args:
        text: 原文本
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两段文本的相似度（简单版本：基于共同词汇）

    Args:
        text1: 第一段文本
        text2: 第二段文本

    Returns:
        相似度分数 (0-1)
    """
    # 分词（简单版本：按空格和标点分割）
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))

    if not words1 or not words2:
        return 0.0

    # Jaccard相似度
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def format_number(num: int) -> str:
    """
    格式化数字（添加千位分隔符）

    Args:
        num: 数字

    Returns:
        格式化的字符串
    """
    return f"{num:,}"


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试工具函数...\n")

    # 测试token计数
    test_text = "Hello, this is a test message with some code: print('hello')"
    tokens = count_tokens(test_text)
    print(f"文本: {test_text}")
    print(f"Token数: {tokens}\n")

    # 测试实体提取
    test_code = """
    import numpy as np
    from sklearn import metrics

    class DataProcessor:
        def load_data(self, filename='data.csv'):
            try:
                data = pd.read_csv(filename)
            except FileNotFoundError as e:
                print(f"Error: {e}")
    """
    entities = extract_entities(test_code)
    print("提取的实体:")
    for key, values in entities.items():
        if values:
            print(f"  {key}: {values}")

    print("\n✅ 工具函数测试完成！")
