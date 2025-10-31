"""
对话导入器 - 支持多种平台的对话格式导入

支持的平台格式：
- OpenAI ChatGPT导出格式
- Anthropic Claude导出格式
- 通用对话格式（role + content）
- 自定义格式
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConversationImporter:
    """对话导入器"""

    def __init__(self):
        """初始化导入器"""
        self.supported_formats = [
            "chatgpt",
            "claude",
            "generic",
            "auto"
        ]

    def import_conversation(
        self,
        json_data: str,
        format_type: str = "auto"
    ) -> List[Dict[str, Any]]:
        """
        导入对话记录

        Args:
            json_data: JSON格式的对话数据
            format_type: 格式类型 (chatgpt/claude/generic/auto)

        Returns:
            标准化的消息列表 [{"role": "user/assistant", "content": "..."}]

        Raises:
            ValueError: 无效的JSON或不支持的格式
        """
        # 解析JSON
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"无效的JSON格式: {e}")

        # 自动检测格式
        if format_type == "auto":
            format_type = self._detect_format(data)

        # 根据格式解析
        if format_type == "chatgpt":
            return self._parse_chatgpt(data)
        elif format_type == "claude":
            return self._parse_claude(data)
        elif format_type == "generic":
            return self._parse_generic(data)
        else:
            raise ValueError(f"不支持的格式: {format_type}")

    def _detect_format(self, data: Any) -> str:
        """
        自动检测对话格式

        Args:
            data: 解析后的JSON数据

        Returns:
            格式类型
        """
        # ChatGPT格式检测
        if isinstance(data, list):
            # 标准消息列表格式
            if all(isinstance(msg, dict) and "role" in msg and "content" in msg for msg in data):
                return "generic"

            # ChatGPT导出格式（包含mapping字段）
            if any(isinstance(msg, dict) and "mapping" in msg for msg in data):
                return "chatgpt"

        elif isinstance(data, dict):
            # ChatGPT完整导出格式
            if "mapping" in data or "conversation_id" in data:
                return "chatgpt"

            # Claude格式
            if "messages" in data and isinstance(data["messages"], list):
                return "claude"

            # 通用格式（包含messages字段）
            if "conversation" in data or "chat_history" in data:
                return "generic"

        # 默认尝试通用格式
        return "generic"

    def _parse_chatgpt(self, data: Any) -> List[Dict[str, Any]]:
        """
        解析ChatGPT导出格式

        ChatGPT导出格式示例：
        {
          "mapping": {
            "uuid1": {
              "message": {
                "author": {"role": "user"},
                "content": {"parts": ["Hello"]}
              }
            },
            ...
          }
        }
        """
        messages = []

        # 处理完整导出格式
        if isinstance(data, dict) and "mapping" in data:
            mapping = data["mapping"]

            # 按创建时间排序
            sorted_nodes = sorted(
                mapping.values(),
                key=lambda x: x.get("message", {}).get("create_time", 0) if x.get("message") else 0
            )

            for node in sorted_nodes:
                if not node.get("message"):
                    continue

                message = node["message"]
                author = message.get("author", {})
                role = author.get("role", "unknown")

                # 跳过系统消息
                if role == "system":
                    continue

                # 提取内容
                content_data = message.get("content", {})
                if isinstance(content_data, dict):
                    parts = content_data.get("parts", [])
                    content = "\n".join(str(p) for p in parts if p)
                else:
                    content = str(content_data)

                if content and content.strip():
                    messages.append({
                        "role": "assistant" if role == "assistant" else "user",
                        "content": content.strip()
                    })

        # 处理简化格式
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "message" in item:
                    msg = item["message"]
                    role = msg.get("author", {}).get("role", "user")
                    content = msg.get("content", {}).get("parts", [""])[0]

                    if content and content.strip():
                        messages.append({
                            "role": "assistant" if role == "assistant" else "user",
                            "content": str(content).strip()
                        })

        return messages

    def _parse_claude(self, data: Any) -> List[Dict[str, Any]]:
        """
        解析Claude导出格式

        Claude格式示例：
        {
          "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
          ]
        }
        """
        messages = []

        if isinstance(data, dict):
            # 提取messages字段
            msg_list = data.get("messages", [])
        elif isinstance(data, list):
            msg_list = data
        else:
            raise ValueError("无法解析Claude格式")

        for msg in msg_list:
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Claude的content可能是列表格式
            if isinstance(content, list):
                # 提取文本内容
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        text_parts.append(part)
                content = "\n".join(text_parts)

            if content and str(content).strip():
                messages.append({
                    "role": "assistant" if role == "assistant" else "user",
                    "content": str(content).strip()
                })

        return messages

    def _parse_generic(self, data: Any) -> List[Dict[str, Any]]:
        """
        解析通用格式

        通用格式示例：
        [
          {"role": "user", "content": "Hello"},
          {"role": "assistant", "content": "Hi!"}
        ]

        或：
        {
          "conversation": [
            {"role": "user", "content": "Hello"},
            ...
          ]
        }
        """
        messages = []

        # 提取消息列表
        if isinstance(data, list):
            msg_list = data
        elif isinstance(data, dict):
            msg_list = (
                data.get("messages") or
                data.get("conversation") or
                data.get("chat_history") or
                data.get("history") or
                []
            )
        else:
            raise ValueError("无法解析通用格式")

        for msg in msg_list:
            if not isinstance(msg, dict):
                continue

            # 尝试多种字段名
            role = (
                msg.get("role") or
                msg.get("sender") or
                msg.get("author") or
                "user"
            )

            content = (
                msg.get("content") or
                msg.get("message") or
                msg.get("text") or
                ""
            )

            # 标准化角色名
            if role.lower() in ["user", "human", "person"]:
                role = "user"
            elif role.lower() in ["assistant", "ai", "bot", "system"]:
                role = "assistant"
            else:
                role = "user"

            if content and str(content).strip():
                messages.append({
                    "role": role,
                    "content": str(content).strip()
                })

        return messages

    def validate_messages(self, messages: List[Dict[str, Any]]) -> bool:
        """
        验证消息格式是否有效

        Args:
            messages: 消息列表

        Returns:
            是否有效
        """
        if not messages:
            return False

        for msg in messages:
            if not isinstance(msg, dict):
                return False
            if "role" not in msg or "content" not in msg:
                return False
            if msg["role"] not in ["user", "assistant"]:
                return False
            if not msg["content"] or not msg["content"].strip():
                return False

        return True

    def get_import_statistics(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取导入统计信息

        Args:
            messages: 消息列表

        Returns:
            统计信息
        """
        user_count = sum(1 for msg in messages if msg["role"] == "user")
        assistant_count = sum(1 for msg in messages if msg["role"] == "assistant")
        total_chars = sum(len(msg["content"]) for msg in messages)

        return {
            "total_messages": len(messages),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "total_characters": total_chars,
            "avg_message_length": total_chars // len(messages) if messages else 0
        }


def create_sample_formats() -> Dict[str, str]:
    """
    创建示例格式（用于文档）

    Returns:
        格式名称到示例JSON的字典
    """
    samples = {
        "chatgpt": json.dumps({
            "mapping": {
                "abc123": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["Hello, how are you?"]},
                        "create_time": 1234567890
                    }
                },
                "def456": {
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"parts": ["I'm doing well, thank you!"]},
                        "create_time": 1234567891
                    }
                }
            }
        }, indent=2),

        "claude": json.dumps({
            "messages": [
                {"role": "user", "content": "Hello, how are you?"},
                {"role": "assistant", "content": "I'm doing well, thank you!"}
            ]
        }, indent=2),

        "generic": json.dumps([
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"}
        ], indent=2)
    }

    return samples


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("对话导入器测试")
    print("=" * 60)

    importer = ConversationImporter()

    # 测试通用格式
    print("\n【测试1: 通用格式】")
    generic_data = json.dumps([
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
        {"role": "user", "content": "告诉我关于Python的信息"}
    ])

    try:
        messages = importer.import_conversation(generic_data, format_type="auto")
        print(f"✅ 成功导入 {len(messages)} 条消息")
        for i, msg in enumerate(messages, 1):
            print(f"  {i}. [{msg['role']}] {msg['content'][:50]}...")

        stats = importer.get_import_statistics(messages)
        print(f"\n统计信息: {stats}")

    except Exception as e:
        print(f"❌ 导入失败: {e}")

    # 显示示例格式
    print("\n" + "=" * 60)
    print("支持的格式示例")
    print("=" * 60)

    samples = create_sample_formats()
    for format_name, sample_json in samples.items():
        print(f"\n【{format_name.upper()}格式】")
        print(sample_json)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
