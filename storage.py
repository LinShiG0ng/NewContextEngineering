"""
三层存储系统模块

实现分层的上下文存储架构:
- 短期存储 (Short-term): 最近3-5条消息，完整保留
- 中期存储 (Mid-term): 6-30条压缩历史
- 长期存储 (Long-term): 持久化知识库

这种分层设计模拟了人类记忆系统，平衡了信息完整性和存储效率
"""

import os
import json
import time
from typing import Dict, List, Optional
from collections import deque
from pathlib import Path

from utils import count_tokens, format_timestamp
from config import SHORT_TERM_SIZE, MID_TERM_SIZE, WORKSPACE_DIR


class LayeredStorage:
    """
    分层存储系统

    管理三层记忆架构，自动进行层级提升和降级
    """

    def __init__(self, workspace: str = WORKSPACE_DIR,
                 short_term_size: int = SHORT_TERM_SIZE,
                 mid_term_size: int = MID_TERM_SIZE):
        """
        初始化分层存储

        Args:
            workspace: 工作空间目录
            short_term_size: 短期存储容量
            mid_term_size: 中期存储容量
        """
        self.workspace = workspace
        self.short_term_size = short_term_size
        self.mid_term_size = mid_term_size

        # 确保工作空间存在
        Path(workspace).mkdir(parents=True, exist_ok=True)

        # 三层存储
        self.short_term: deque = deque(maxlen=short_term_size)  # 固定大小的队列
        self.mid_term: List[Dict] = []  # 压缩后的消息列表
        self.long_term_path = os.path.join(workspace, "long_term.json")

        # 统计信息
        self.stats = {
            "short_term_count": 0,
            "mid_term_count": 0,
            "long_term_count": 0,
            "total_messages": 0,
            "promotions": 0  # 从短期提升到中期的次数
        }

        # 加载长期存储
        self._load_long_term()

    def add_to_short_term(self, message: Dict):
        """
        添加消息到短期存储

        当短期存储满时，自动提升最老的消息到中期存储

        Args:
            message: 消息字典
        """
        # 确保消息包含必要字段
        if "timestamp" not in message:
            message["timestamp"] = time.time()

        if "tokens" not in message:
            message["tokens"] = count_tokens(message.get("content", ""))

        # 如果短期存储已满，提升最老的消息到中期
        if len(self.short_term) >= self.short_term_size:
            old_message = self.short_term[0]  # 最老的消息
            self.promote_to_mid_term([old_message])

        # 添加到短期存储
        self.short_term.append(message)
        self.stats["short_term_count"] = len(self.short_term)
        self.stats["total_messages"] += 1

    def promote_to_mid_term(self, messages: List[Dict]):
        """
        将消息提升到中期存储（通常是压缩后的）

        Args:
            messages: 要提升的消息列表
        """
        for msg in messages:
            self.mid_term.append(msg)
            self.stats["promotions"] += 1

        # 如果中期存储超过限制，移除最老的消息
        while len(self.mid_term) > self.mid_term_size:
            removed = self.mid_term.pop(0)
            # 可选：将重要信息保存到长期存储
            # self._archive_to_long_term(removed)

        self.stats["mid_term_count"] = len(self.mid_term)

    def add_compressed_to_mid_term(self, compressed_message: Dict):
        """
        添加压缩后的消息摘要到中期存储

        Args:
            compressed_message: 压缩后的消息（通常包含多条消息的摘要）
        """
        compressed_message["compressed"] = True
        compressed_message["timestamp"] = time.time()

        self.mid_term.append(compressed_message)
        self.stats["mid_term_count"] = len(self.mid_term)

    def clear_short_term(self):
        """
        清空短期存储（压缩时使用）
        """
        self.short_term.clear()
        self.stats["short_term_count"] = 0

    def get_short_term(self) -> List[Dict]:
        """
        获取短期存储的所有消息

        Returns:
            消息列表
        """
        return list(self.short_term)

    def get_mid_term(self) -> List[Dict]:
        """
        获取中期存储的所有消息

        Returns:
            消息列表
        """
        return self.mid_term.copy()

    def get_all_messages(self) -> List[Dict]:
        """
        获取所有消息（中期 + 短期）

        Returns:
            完整的消息列表
        """
        return self.mid_term + list(self.short_term)

    def get_all_layers(self) -> Dict:
        """
        获取所有层的数据

        Returns:
            包含三层数据的字典
        """
        return {
            "short_term": list(self.short_term),
            "mid_term": self.mid_term,
            "long_term": self._load_long_term(),
            "stats": self.stats
        }

    def save_to_long_term(self, key: str, data: Dict):
        """
        保存数据到长期存储

        Args:
            key: 数据键
            data: 要保存的数据
        """
        long_term_data = self._load_long_term()
        long_term_data[key] = {
            "data": data,
            "timestamp": time.time()
        }

        try:
            with open(self.long_term_path, 'w', encoding='utf-8') as f:
                json.dump(long_term_data, f, indent=2, ensure_ascii=False)

            self.stats["long_term_count"] = len(long_term_data)

        except Exception as e:
            print(f"⚠️  保存长期存储失败: {e}")

    def _load_long_term(self) -> Dict:
        """
        加载长期存储数据

        Returns:
            长期存储的数据字典
        """
        if not os.path.exists(self.long_term_path):
            return {}

        try:
            with open(self.long_term_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.stats["long_term_count"] = len(data)
                return data
        except Exception as e:
            print(f"⚠️  加载长期存储失败: {e}")
            return {}

    def _archive_to_long_term(self, message: Dict):
        """
        归档消息到长期存储（用于重要信息）

        Args:
            message: 要归档的消息
        """
        # 提取关键信息
        key = f"message_{int(message.get('timestamp', time.time()))}"
        archive_data = {
            "role": message.get("role"),
            "summary": message.get("content", "")[:200],  # 保存摘要
            "importance": message.get("importance", "normal"),
            "timestamp": message.get("timestamp")
        }

        self.save_to_long_term(key, archive_data)

    def get_total_tokens(self) -> int:
        """
        计算当前存储的总token数

        Returns:
            总token数
        """
        total = 0

        # 短期存储
        for msg in self.short_term:
            total += msg.get("tokens", count_tokens(msg.get("content", "")))

        # 中期存储
        for msg in self.mid_term:
            total += msg.get("tokens", count_tokens(msg.get("content", "")))

        return total

    def get_statistics(self) -> Dict:
        """
        获取存储统计信息

        Returns:
            统计信息字典
        """
        return {
            "短期存储": f"{len(self.short_term)}/{self.short_term_size}条",
            "中期存储": f"{len(self.mid_term)}/{self.mid_term_size}条",
            "长期存储": f"{self.stats['long_term_count']}个项目",
            "总消息数": self.stats["total_messages"],
            "总Token数": self.get_total_tokens(),
            "提升次数": self.stats["promotions"]
        }

    def reset(self):
        """
        重置所有存储（保留长期存储）
        """
        self.short_term.clear()
        self.mid_term.clear()
        self.stats["short_term_count"] = 0
        self.stats["mid_term_count"] = 0
        self.stats["total_messages"] = 0
        self.stats["promotions"] = 0

    def export_history(self, output_path: Optional[str] = None) -> str:
        """
        导出完整对话历史

        Args:
            output_path: 输出文件路径

        Returns:
            导出的文件路径
        """
        if output_path is None:
            timestamp = int(time.time())
            output_path = os.path.join(self.workspace, f"history_{timestamp}.json")

        export_data = {
            "export_time": time.time(),
            "export_time_formatted": format_timestamp(time.time()),
            "statistics": self.get_statistics(),
            "messages": {
                "short_term": list(self.short_term),
                "mid_term": self.mid_term
            }
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            print(f"✅ 历史记录已导出到: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return ""

    def import_history(self, input_path: str) -> bool:
        """
        导入对话历史

        Args:
            input_path: 输入文件路径

        Returns:
            是否成功
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            messages = data.get("messages", {})

            # 导入中期存储
            self.mid_term = messages.get("mid_term", [])

            # 导入短期存储
            short_term_messages = messages.get("short_term", [])
            for msg in short_term_messages:
                self.short_term.append(msg)

            # 更新统计
            self.stats["mid_term_count"] = len(self.mid_term)
            self.stats["short_term_count"] = len(self.short_term)

            print(f"✅ 历史记录已导入: {input_path}")
            return True

        except Exception as e:
            print(f"❌ 导入失败: {e}")
            return False


def test_storage():
    """
    测试存储系统
    """
    print("🧪 测试三层存储系统...\n")

    # 创建存储实例
    storage = LayeredStorage(workspace="./test_workspace", short_term_size=3)

    # 测试添加消息到短期存储
    print("=" * 60)
    print("测试1: 添加消息到短期存储")
    print("=" * 60)

    for i in range(5):
        message = {
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"这是第{i+1}条测试消息",
            "timestamp": time.time()
        }
        storage.add_to_short_term(message)
        print(f"添加消息 {i+1}")
        time.sleep(0.1)

    print(f"\n短期存储: {len(storage.short_term)}条")
    print(f"中期存储: {len(storage.mid_term)}条")

    # 测试压缩消息添加到中期
    print("\n" + "=" * 60)
    print("测试2: 添加压缩消息到中期存储")
    print("=" * 60)

    compressed = {
        "role": "system",
        "content": "这是一条压缩摘要，包含了多条消息的要点...",
        "compressed": True,
        "original_count": 3
    }
    storage.add_compressed_to_mid_term(compressed)
    print("添加压缩摘要")
    print(f"中期存储: {len(storage.mid_term)}条")

    # 测试统计信息
    print("\n" + "=" * 60)
    print("测试3: 统计信息")
    print("=" * 60)

    stats = storage.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 测试导出
    print("\n" + "=" * 60)
    print("测试4: 导出历史")
    print("=" * 60)

    export_path = storage.export_history()
    if export_path:
        print(f"导出成功: {export_path}")

    # 清理测试文件
    import shutil
    if os.path.exists("./test_workspace"):
        shutil.rmtree("./test_workspace")
        print("\n✅ 测试完成，清理测试文件")


if __name__ == "__main__":
    test_storage()
