"""
长期知识库管理模块

持久化存储项目的关键信息:
- 项目元数据 (技术栈、目标等)
- 决策记录 (重要决定和原因)
- 代码片段 (关键实现)
- 常见问题 (FAQ)
- 最佳实践

模拟Claude Code的CLAUDE.md文件
"""

import os
import json
import time
from typing import Dict, List, Optional
from pathlib import Path

from utils import extract_entities, count_tokens, format_timestamp
from config import KNOWLEDGE_BASE_PATH


class KnowledgeBase:
    """
    长期知识库

    持久化存储和检索项目知识
    """

    def __init__(self, kb_path: str = KNOWLEDGE_BASE_PATH):
        """
        初始化知识库

        Args:
            kb_path: 知识库文件路径
        """
        self.kb_path = kb_path
        self.data = {}

        # 确保目录存在
        os.makedirs(os.path.dirname(kb_path), exist_ok=True)

        # 加载现有知识库
        self.load()

    def load(self) -> Dict:
        """
        从文件加载知识库

        Returns:
            知识库数据
        """
        if os.path.exists(self.kb_path):
            try:
                with open(self.kb_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                    print(f"✅ 加载知识库: {len(self.data)}个条目")
            except Exception as e:
                print(f"⚠️  加载知识库失败: {e}")
                self.data = self._init_default_structure()
        else:
            self.data = self._init_default_structure()

        return self.data

    def _init_default_structure(self) -> Dict:
        """
        初始化默认知识库结构

        Returns:
            默认结构字典
        """
        return {
            "metadata": {
                "created_at": time.time(),
                "updated_at": time.time(),
                "version": "1.0"
            },
            "project_info": {
                "name": "",
                "description": "",
                "tech_stack": [],
                "goals": []
            },
            "decisions": [],
            "code_snippets": [],
            "faq": [],
            "best_practices": [],
            "entities": {
                "files": [],
                "functions": [],
                "classes": [],
                "concepts": []
            }
        }

    def save(self, data: Optional[Dict] = None):
        """
        保存知识库到文件

        Args:
            data: 要保存的数据（为None则保存当前数据）
        """
        if data is not None:
            self.data = data

        # 更新时间戳
        self.data["metadata"]["updated_at"] = time.time()

        try:
            with open(self.kb_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 保存知识库失败: {e}")

    def update(self, new_info: Dict):
        """
        增量更新知识库

        Args:
            new_info: 新信息字典
        """
        # 更新项目信息
        if "project_info" in new_info:
            for key, value in new_info["project_info"].items():
                if isinstance(value, list):
                    # 列表类型：合并去重
                    existing = self.data["project_info"].get(key, [])
                    self.data["project_info"][key] = list(set(existing + value))
                else:
                    # 其他类型：直接更新
                    self.data["project_info"][key] = value

        # 添加决策记录
        if "decision" in new_info:
            decision = {
                "timestamp": time.time(),
                "title": new_info["decision"].get("title", ""),
                "description": new_info["decision"].get("description", ""),
                "reason": new_info["decision"].get("reason", ""),
                "alternatives": new_info["decision"].get("alternatives", [])
            }
            self.data["decisions"].append(decision)

        # 添加代码片段
        if "code_snippet" in new_info:
            snippet = {
                "timestamp": time.time(),
                "title": new_info["code_snippet"].get("title", ""),
                "language": new_info["code_snippet"].get("language", "python"),
                "code": new_info["code_snippet"].get("code", ""),
                "description": new_info["code_snippet"].get("description", "")
            }
            self.data["code_snippets"].append(snippet)

        # 添加FAQ
        if "faq" in new_info:
            faq = {
                "timestamp": time.time(),
                "question": new_info["faq"].get("question", ""),
                "answer": new_info["faq"].get("answer", "")
            }
            self.data["faq"].append(faq)

        # 添加最佳实践
        if "best_practice" in new_info:
            practice = {
                "timestamp": time.time(),
                "title": new_info["best_practice"].get("title", ""),
                "description": new_info["best_practice"].get("description", ""),
                "example": new_info["best_practice"].get("example", "")
            }
            self.data["best_practices"].append(practice)

        # 更新实体
        if "entities" in new_info:
            for entity_type, entities in new_info["entities"].items():
                if entity_type in self.data["entities"]:
                    existing = set(self.data["entities"][entity_type])
                    existing.update(entities)
                    self.data["entities"][entity_type] = list(existing)

        # 保存更新
        self.save()

    def query(self, keywords: List[str]) -> List[Dict]:
        """
        根据关键词搜索知识库

        Args:
            keywords: 关键词列表

        Returns:
            匹配的条目列表
        """
        results = []
        keywords_lower = [kw.lower() for kw in keywords]

        # 搜索决策记录
        for decision in self.data.get("decisions", []):
            text = f"{decision.get('title', '')} {decision.get('description', '')}".lower()
            if any(kw in text for kw in keywords_lower):
                results.append({
                    "type": "decision",
                    "data": decision,
                    "relevance": sum(1 for kw in keywords_lower if kw in text)
                })

        # 搜索代码片段
        for snippet in self.data.get("code_snippets", []):
            text = f"{snippet.get('title', '')} {snippet.get('description', '')} {snippet.get('code', '')}".lower()
            if any(kw in text for kw in keywords_lower):
                results.append({
                    "type": "code_snippet",
                    "data": snippet,
                    "relevance": sum(1 for kw in keywords_lower if kw in text)
                })

        # 搜索FAQ
        for faq in self.data.get("faq", []):
            text = f"{faq.get('question', '')} {faq.get('answer', '')}".lower()
            if any(kw in text for kw in keywords_lower):
                results.append({
                    "type": "faq",
                    "data": faq,
                    "relevance": sum(1 for kw in keywords_lower if kw in text)
                })

        # 按相关性排序
        results.sort(key=lambda x: x["relevance"], reverse=True)

        return results

    def to_context_message(self, max_items: int = 5) -> Dict:
        """
        将知识库转换为上下文消息

        Args:
            max_items: 每个类别最多包含的条目数

        Returns:
            格式化的消息字典
        """
        lines = ["📚 长期知识库", ""]

        # 项目信息
        project_info = self.data.get("project_info", {})
        if project_info.get("name"):
            lines.append(f"## 项目: {project_info['name']}")
            if project_info.get("description"):
                lines.append(f"{project_info['description']}")
            if project_info.get("tech_stack"):
                lines.append(f"技术栈: {', '.join(project_info['tech_stack'])}")
            lines.append("")

        # 最近决策
        decisions = self.data.get("decisions", [])
        if decisions:
            lines.append("## 重要决策")
            for decision in decisions[-max_items:]:
                lines.append(f"• {decision.get('title', '未命名')}")
                lines.append(f"  {decision.get('description', '')[:100]}")
            lines.append("")

        # 关键代码片段
        snippets = self.data.get("code_snippets", [])
        if snippets:
            lines.append("## 关键代码")
            for snippet in snippets[-max_items:]:
                lines.append(f"• {snippet.get('title', '未命名')} [{snippet.get('language', 'text')}]")
            lines.append("")

        # FAQ
        faq = self.data.get("faq", [])
        if faq:
            lines.append("## 常见问题")
            for item in faq[-max_items:]:
                lines.append(f"Q: {item.get('question', '')}")
                lines.append(f"A: {item.get('answer', '')[:100]}")
            lines.append("")

        content = "\n".join(lines)

        return {
            "role": "system",
            "content": content,
            "timestamp": time.time(),
            "tokens": count_tokens(content),
            "from_knowledge_base": True
        }

    def export_markdown(self, output_path: Optional[str] = None) -> str:
        """
        导出知识库为Markdown文件（类似CLAUDE.md）

        Args:
            output_path: 输出路径

        Returns:
            导出的文件路径
        """
        if output_path is None:
            output_path = self.kb_path.replace('.json', '.md')

        lines = ["# 项目知识库", ""]

        # 元数据
        metadata = self.data.get("metadata", {})
        lines.append(f"创建时间: {format_timestamp(metadata.get('created_at', time.time()))}")
        lines.append(f"更新时间: {format_timestamp(metadata.get('updated_at', time.time()))}")
        lines.append(f"版本: {metadata.get('version', '1.0')}")
        lines.append("")

        # 项目信息
        lines.append("## 项目信息")
        lines.append("")
        project_info = self.data.get("project_info", {})

        if project_info.get("name"):
            lines.append(f"**项目名称**: {project_info['name']}")
        if project_info.get("description"):
            lines.append(f"**描述**: {project_info['description']}")
        if project_info.get("tech_stack"):
            lines.append(f"**技术栈**: {', '.join(project_info['tech_stack'])}")
        if project_info.get("goals"):
            lines.append(f"**目标**:")
            for goal in project_info["goals"]:
                lines.append(f"- {goal}")
        lines.append("")

        # 决策记录
        lines.append("## 决策记录")
        lines.append("")
        for i, decision in enumerate(self.data.get("decisions", []), 1):
            lines.append(f"### {i}. {decision.get('title', '未命名')}")
            lines.append(f"*{format_timestamp(decision.get('timestamp', time.time()))}*")
            lines.append("")
            lines.append(f"**描述**: {decision.get('description', '')}")
            lines.append(f"**原因**: {decision.get('reason', '')}")
            if decision.get("alternatives"):
                lines.append(f"**备选方案**: {', '.join(decision['alternatives'])}")
            lines.append("")

        # 代码片段
        lines.append("## 关键代码片段")
        lines.append("")
        for i, snippet in enumerate(self.data.get("code_snippets", []), 1):
            lines.append(f"### {i}. {snippet.get('title', '未命名')}")
            lines.append(f"*{format_timestamp(snippet.get('timestamp', time.time()))}*")
            lines.append("")
            if snippet.get("description"):
                lines.append(snippet["description"])
                lines.append("")
            lang = snippet.get("language", "text")
            code = snippet.get("code", "")
            lines.append(f"```{lang}")
            lines.append(code)
            lines.append("```")
            lines.append("")

        # FAQ
        lines.append("## 常见问题")
        lines.append("")
        for i, faq in enumerate(self.data.get("faq", []), 1):
            lines.append(f"### Q{i}: {faq.get('question', '')}")
            lines.append(f"**A**: {faq.get('answer', '')}")
            lines.append("")

        # 最佳实践
        lines.append("## 最佳实践")
        lines.append("")
        for i, practice in enumerate(self.data.get("best_practices", []), 1):
            lines.append(f"### {i}. {practice.get('title', '未命名')}")
            lines.append(f"{practice.get('description', '')}")
            if practice.get("example"):
                lines.append("")
                lines.append("示例:")
                lines.append(f"```")
                lines.append(practice["example"])
                lines.append("```")
            lines.append("")

        # 写入文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            print(f"✅ 知识库已导出到: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return ""

    def get_statistics(self) -> Dict:
        """
        获取知识库统计信息

        Returns:
            统计字典
        """
        return {
            "决策记录": len(self.data.get("decisions", [])),
            "代码片段": len(self.data.get("code_snippets", [])),
            "FAQ": len(self.data.get("faq", [])),
            "最佳实践": len(self.data.get("best_practices", [])),
            "实体数": sum(len(v) for v in self.data.get("entities", {}).values())
        }


def test_knowledge_base():
    """
    测试知识库
    """
    print("🧪 测试长期知识库...\n")

    # 创建知识库
    kb = KnowledgeBase(kb_path="./workspace/test_kb.json")

    # 测试1: 更新项目信息
    print("=" * 60)
    print("测试1: 更新项目信息")
    print("=" * 60)

    kb.update({
        "project_info": {
            "name": "上下文工程Demo",
            "description": "演示智能上下文管理",
            "tech_stack": ["Python", "OpenAI API"],
            "goals": ["展示压缩算法", "验证效果"]
        }
    })
    print("✅ 项目信息已更新")

    # 测试2: 添加决策记录
    print("\n" + "=" * 60)
    print("测试2: 添加决策记录")
    print("=" * 60)

    kb.update({
        "decision": {
            "title": "选择AU2压缩算法",
            "description": "采用8段式压缩流程",
            "reason": "平衡压缩率和信息保留",
            "alternatives": ["简单截断", "LLM总结"]
        }
    })
    print("✅ 决策记录已添加")

    # 测试3: 添加代码片段
    print("\n" + "=" * 60)
    print("测试3: 添加代码片段")
    print("=" * 60)

    kb.update({
        "code_snippet": {
            "title": "消息分类函数",
            "language": "python",
            "code": "def classify_messages(messages):\n    # 分类逻辑\n    pass",
            "description": "将消息分为critical/important/contextual/redundant"
        }
    })
    print("✅ 代码片段已添加")

    # 测试4: 查询
    print("\n" + "=" * 60)
    print("测试4: 关键词查询")
    print("=" * 60)

    results = kb.query(["压缩", "算法"])
    print(f"找到{len(results)}个相关结果:")
    for result in results:
        print(f"  • [{result['type']}] 相关度: {result['relevance']}")

    # 测试5: 转换为上下文消息
    print("\n" + "=" * 60)
    print("测试5: 转换为上下文消息")
    print("=" * 60)

    msg = kb.to_context_message()
    print(f"生成的上下文消息 ({msg['tokens']} tokens):")
    print(msg["content"][:200] + "...")

    # 测试6: 导出Markdown
    print("\n" + "=" * 60)
    print("测试6: 导出Markdown")
    print("=" * 60)

    kb.export_markdown("./workspace/test_kb.md")

    # 统计信息
    print("\n" + "=" * 60)
    print("统计信息")
    print("=" * 60)

    stats = kb.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ 知识库测试完成！")


if __name__ == "__main__":
    test_knowledge_base()
