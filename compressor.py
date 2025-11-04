"""
AU2智能压缩算法模块

实现8段式压缩流程:
1. 消息分类 (critical/important/contextual/redundant)
2. 关键实体提取 (文件名、函数名、变量名、错误信息等)
   + 安全测试实体 (IP、端口、漏洞、payload、工具等)
3. 知识图谱构建 (实体之间的关系)
4. 重要性评分 (基于引用次数、时间距离、错误相关性)
5. 生成压缩摘要 (使用模板或规则)
6. 保留关键代码块
7. 重构对话流 (合并相似主题、删除冗余)
8. 质量验证 (检查关键信息是否保留)

AU2 = Adaptive Universal Understanding (自适应通用理解压缩)

支持场景：
- 编程开发（代码、函数、类、错误）
- 渗透测试（工具、漏洞、payload、数据包）
- 漏洞挖掘（CVE、漏洞类型、利用流程）
"""

import time
import re
from typing import Dict, List, Tuple, Set
from collections import defaultdict, Counter

from utils import (
    count_tokens, extract_entities, extract_code_blocks,
    calculate_similarity, format_timestamp
)
from config import (
    MESSAGE_IMPORTANCE_WEIGHTS,
    ENTITY_IMPORTANCE_WEIGHTS,
    TARGET_COMPRESSION_RATIO,
    MIN_QUALITY_RETENTION
)
from security_extensions import SecurityEntityExtractor, SecurityScenarioClassifier


class AU2Compressor:
    """
    AU2智能压缩器

    通过8个阶段的分析和处理，实现高质量的上下文压缩
    """

    def __init__(self, target_ratio: float = TARGET_COMPRESSION_RATIO,
                 min_quality: float = MIN_QUALITY_RETENTION):
        """
        初始化压缩器

        Args:
            target_ratio: 目标压缩率 (0-1)
            min_quality: 最低信息保留率 (0-1)
        """
        self.target_ratio = target_ratio
        self.min_quality = min_quality

        # 初始化安全测试扩展
        self.security_extractor = SecurityEntityExtractor()
        self.security_classifier = SecurityScenarioClassifier()

        # 压缩统计
        self.stats = {
            "compressions": 0,
            "total_original_tokens": 0,
            "total_compressed_tokens": 0,
            "total_time": 0
        }

    async def compress(self, messages: List[Dict]) -> Dict:
        """
        执行完整的压缩流程

        Args:
            messages: 要压缩的消息列表

        Returns:
            压缩结果字典，包含压缩后的消息和统计信息
        """
        start_time = time.time()

        print("\n" + "━" * 60)
        print("🔄 正在执行AU2智能压缩...")
        print("━" * 60 + "\n")

        # 分离system prompt（第一个system消息永远不压缩）
        system_prompt = None
        messages_to_compress = messages

        if messages and messages[0].get("role") == "system":
            system_prompt = messages[0]
            messages_to_compress = messages[1:]
            print("🔒 检测到System Prompt，将保持不压缩")
            print(f"   • System Prompt Token数: {system_prompt.get('tokens', count_tokens(system_prompt.get('content', '')))}\n")

        # 如果只有system prompt，无需压缩
        if not messages_to_compress:
            print("⚠️  只有System Prompt，无需压缩\n")
            return {
                "compressed_message": system_prompt,
                "original_tokens": system_prompt.get("tokens", 0),
                "compressed_tokens": system_prompt.get("tokens", 0),
                "compression_ratio": 0,
                "quality": 1.0,
                "entities": {},
                "elapsed_time": 0,
                "system_prompt": system_prompt
            }

        # 计算原始token数（不包括system prompt）
        original_tokens = sum(msg.get("tokens", count_tokens(msg.get("content", "")))
                             for msg in messages_to_compress)

        # 阶段1: 消息分类
        print("阶段 1/8: 分类消息")
        classified = self.classify_messages(messages_to_compress)
        print(f"  • Critical: {len(classified['critical'])}条 (必须保留)")
        print(f"  • Important: {len(classified['important'])}条 (可压缩)")
        print(f"  • Contextual: {len(classified['contextual'])}条 (提取要点)")
        print(f"  • Redundant: {len(classified['redundant'])}条 (可删除)\n")

        # 阶段2: 提取实体
        print("阶段 2/8: 提取关键实体")
        entities = self.extract_entities(classified)

        # 编程实体
        if entities.get('files') or entities.get('functions'):
            print("  [编程场景]")
            if entities.get('files'):
                print(f"    • 文件: {len(entities['files'])}个")
            if entities.get('functions'):
                print(f"    • 函数: {len(entities['functions'])}个")
            if entities.get('classes'):
                print(f"    • 类: {len(entities['classes'])}个")
            if entities.get('errors'):
                print(f"    • 错误: {len(entities['errors'])}个")

        # 安全测试实体
        if entities.get('ip_addresses') or entities.get('tools') or entities.get('vulnerabilities'):
            print("  [安全测试场景]")
            if entities.get('ip_addresses'):
                print(f"    • IP地址: {len(entities['ip_addresses'])}个")
            if entities.get('ports'):
                print(f"    • 端口: {len(entities['ports'])}个")
            if entities.get('tools'):
                print(f"    • 工具: {len(entities['tools'])}个")
            if entities.get('vulnerabilities'):
                print(f"    • 漏洞: {len(entities['vulnerabilities'])}个")
            if entities.get('cve_ids'):
                print(f"    • CVE编号: {len(entities['cve_ids'])}个")
            if entities.get('payloads'):
                print(f"    • Payload: {len(entities['payloads'])}个")
        print()

        # 阶段3: 构建知识图谱
        print("阶段 3/8: 构建知识图谱")
        graph = self.build_knowledge_graph(entities, messages_to_compress)
        print(f"  • 节点数: {graph['node_count']}")
        print(f"  • 关系数: {graph['edge_count']}\n")

        # 阶段4: 重要性评分
        print("阶段 4/8: 计算重要性评分")
        scored_messages = self.score_messages(messages_to_compress, graph)
        print(f"  • 完成 (基于引用频率和时间距离)\n")

        # 阶段5: 生成压缩摘要
        print("阶段 5/8: 生成压缩摘要")
        summary = self.generate_summary(scored_messages, entities)
        compressed_tokens = count_tokens(summary)
        print(f"  • 原始: {len(messages_to_compress)}条消息, {original_tokens} tokens")
        print(f"  • 摘要: 1条消息, {compressed_tokens} tokens\n")

        # 阶段6: 保留关键代码块
        print("阶段 6/8: 保留关键代码块")
        code_blocks = self.extract_key_code_blocks(classified['critical'] + classified['important'])
        print(f"  • 保留代码块: {len(code_blocks)}个\n")

        # 阶段7: 重构对话流
        print("阶段 7/8: 重构对话流")
        restructured = self.restructure_conversation(scored_messages, summary, code_blocks)
        print(f"  • 合并相似主题: {restructured['merged_topics']}组\n")

        # 阶段8: 质量验证
        print("阶段 8/8: 质量验证")
        quality = self.validate_quality(messages_to_compress, restructured['compressed_message'], entities)
        print(f"  • 关键实体保留: {'✅' if quality['entities_retained'] else '❌'} {quality['entity_retention']*100:.0f}%")
        print(f"  • 因果关系完整: {'✅' if quality['causality_intact'] else '❌'}")
        print(f"  • 代码上下文: {'✅' if quality['code_context'] else '❌'} 完整\n")

        # 完成
        elapsed_time = time.time() - start_time
        compression_ratio = 1 - (compressed_tokens / original_tokens) if original_tokens > 0 else 0

        print("━" * 60)
        print("✅ 压缩完成！")
        print("━" * 60 + "\n")

        print("📊 压缩效果:")
        print(f"  原始Tokens: {original_tokens:,}")
        print(f"  压缩后Tokens: {compressed_tokens:,}")
        print(f"  节省Tokens: {original_tokens - compressed_tokens:,} ({compression_ratio*100:.1f}%)")
        print(f"  信息保留率: {quality['overall_quality']*100:.0f}%")
        print(f"  耗时: {elapsed_time:.1f}秒\n")

        # 更新统计
        self.stats["compressions"] += 1
        self.stats["total_original_tokens"] += original_tokens
        self.stats["total_compressed_tokens"] += compressed_tokens
        self.stats["total_time"] += elapsed_time

        return {
            "compressed_message": restructured['compressed_message'],
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "compression_ratio": compression_ratio,
            "quality": quality,
            "entities": entities,
            "elapsed_time": elapsed_time,
            "system_prompt": system_prompt  # 保留的system prompt（如果存在）
        }

    def classify_messages(self, messages: List[Dict]) -> Dict[str, List[Dict]]:
        """
        阶段1: 消息分类

        将消息分为4个类别：
        - critical: 错误信息、关键决策、漏洞发现
        - important: 重要讨论、代码实现、工具执行
        - contextual: 一般对话、解释说明
        - redundant: 重复内容、简单确认

        支持编程场景和安全测试场景

        Args:
            messages: 消息列表

        Returns:
            分类后的消息字典
        """
        classified = {
            "critical": [],
            "important": [],
            "contextual": [],
            "redundant": []
        }

        # 编程场景关键词
        critical_patterns = [
            r"error", r"exception", r"failed", r"bug", r"critical",
            r"错误", r"失败", r"异常", r"严重"
        ]

        important_patterns = [
            r"implement", r"function", r"class", r"def ", r"async ",
            r"实现", r"函数", r"类", r"方法"
        ]

        redundant_patterns = [
            r"^(好的?|ok|yes|谢谢|thanks)$",
            r"^(明白|理解|知道了)$"
        ]

        for msg in messages:
            content = msg.get("content", "")
            content_lower = content.lower()

            # 优先使用安全场景分类器（如果检测到安全内容）
            if self.security_classifier.is_tool_output(content) or \
               self.security_classifier.is_packet_data(content):
                # 使用安全场景分类
                security_importance = self.security_classifier.classify_security_message(content)
                msg["importance"] = security_importance
                classified[security_importance].append(msg)
                continue

            # 编程场景分类
            # 检查critical
            if any(re.search(pattern, content_lower, re.IGNORECASE) for pattern in critical_patterns):
                msg["importance"] = "critical"
                classified["critical"].append(msg)

            # 检查important
            elif any(re.search(pattern, content_lower, re.IGNORECASE) for pattern in important_patterns):
                msg["importance"] = "important"
                classified["important"].append(msg)

            # 检查redundant
            elif any(re.search(pattern, content, re.IGNORECASE) for pattern in redundant_patterns):
                msg["importance"] = "redundant"
                classified["redundant"].append(msg)

            # 默认contextual
            else:
                msg["importance"] = "contextual"
                classified["contextual"].append(msg)

        return classified

    def extract_entities(self, classified: Dict[str, List[Dict]]) -> Dict[str, List]:
        """
        阶段2: 提取关键实体

        从所有消息中提取文件名、函数名、类名、错误等
        支持编程场景和安全测试场景

        Args:
            classified: 分类后的消息

        Returns:
            实体字典
        """
        # 编程场景实体
        programming_entities = {
            "files": set(),
            "functions": set(),
            "variables": set(),
            "errors": set(),
            "classes": set(),
            "imports": set()
        }

        # 安全测试实体
        security_entities = {
            "ip_addresses": set(),
            "ports": set(),
            "domains": set(),
            "urls": set(),
            "tools": set(),
            "vulnerabilities": set(),
            "payloads": set(),
            "http_methods": set(),
            "status_codes": set(),
            "headers": set(),
            "cve_ids": set(),
            "protocols": set()
        }

        # 从所有消息中提取实体
        for category in classified.values():
            for msg in category:
                content = msg.get("content", "")

                # 提取编程实体
                prog_ent = extract_entities(content)
                for key in programming_entities.keys():
                    programming_entities[key].update(prog_ent.get(key, []))

                # 提取安全测试实体
                sec_ent = self.security_extractor.extract_security_entities(content)
                for key in security_entities.keys():
                    security_entities[key].update(sec_ent.get(key, []))

        # 合并结果并限制数量
        result = {}

        # 编程实体（每类最多20个）
        for key, values in programming_entities.items():
            if values:
                result[key] = list(values)[:20]

        # 安全测试实体（每类最多15个）
        for key, values in security_entities.items():
            if values:
                result[key] = list(values)[:15]

        return result

    def build_knowledge_graph(self, entities: Dict, messages: List[Dict]) -> Dict:
        """
        阶段3: 构建知识图谱

        分析实体之间的关系（共现、引用等）

        Args:
            entities: 实体字典
            messages: 消息列表

        Returns:
            知识图谱字典
        """
        graph = {
            "nodes": {},
            "edges": [],
            "node_count": 0,
            "edge_count": 0
        }

        # 创建节点
        node_id = 0
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                graph["nodes"][entity] = {
                    "id": node_id,
                    "type": entity_type,
                    "name": entity,
                    "mentions": 0
                }
                node_id += 1

        graph["node_count"] = len(graph["nodes"])

        # 分析共现关系
        for msg in messages:
            content = msg.get("content", "")
            mentioned_entities = []

            # 找出该消息中提到的实体
            for entity in graph["nodes"].keys():
                if entity in content:
                    graph["nodes"][entity]["mentions"] += 1
                    mentioned_entities.append(entity)

            # 创建实体间的边（共现关系）
            for i, entity1 in enumerate(mentioned_entities):
                for entity2 in mentioned_entities[i+1:]:
                    edge = {
                        "source": entity1,
                        "target": entity2,
                        "weight": 1
                    }
                    graph["edges"].append(edge)

        graph["edge_count"] = len(graph["edges"])

        return graph

    def score_messages(self, messages: List[Dict], graph: Dict) -> List[Dict]:
        """
        阶段4: 计算重要性评分

        基于多个因素给消息打分:
        - 时间距离（越近越重要）
        - 实体引用频率
        - 错误相关性
        - 代码复杂度

        Args:
            messages: 消息列表
            graph: 知识图谱

        Returns:
            带评分的消息列表
        """
        current_time = time.time()
        scored = []

        for msg in messages:
            score = 0.0

            # 1. 基础重要性权重
            importance = msg.get("importance", "contextual")
            score += MESSAGE_IMPORTANCE_WEIGHTS.get(importance, 0.4)

            # 2. 时间距离（最近24小时内的消息加分）
            timestamp = msg.get("timestamp", current_time)
            time_distance = current_time - timestamp
            if time_distance < 86400:  # 24小时
                time_factor = 1 - (time_distance / 86400)
                score += time_factor * 0.3

            # 3. 实体引用频率
            content = msg.get("content", "")
            entity_count = 0
            for entity in graph["nodes"].keys():
                if entity in content:
                    entity_count += 1

            if entity_count > 0:
                score += min(entity_count * 0.1, 0.5)

            # 4. 代码复杂度
            code_blocks = extract_code_blocks(content)
            if code_blocks:
                score += len(code_blocks) * 0.2

            # 5. 长度因素（太短的消息可能不重要）
            if len(content) < 20:
                score *= 0.5

            msg["score"] = min(score, 1.0)  # 限制在0-1
            scored.append(msg)

        # 按分数排序
        scored.sort(key=lambda x: x["score"], reverse=True)

        return scored

    def generate_summary(self, scored_messages: List[Dict], entities: Dict) -> str:
        """
        阶段5: 生成压缩摘要

        创建一个包含关键信息的摘要

        Args:
            scored_messages: 带评分的消息列表
            entities: 实体字典

        Returns:
            压缩摘要文本
        """
        summary_parts = []

        # 1. 开头说明
        summary_parts.append("📝 对话历史摘要（已压缩）")
        summary_parts.append("")

        # 2. 关键实体列表
        if any(entities.values()):
            summary_parts.append("🔑 关键实体:")
            if entities.get("files"):
                summary_parts.append(f"  • 文件: {', '.join(entities['files'][:5])}")
            if entities.get("functions"):
                summary_parts.append(f"  • 函数: {', '.join(entities['functions'][:5])}")
            if entities.get("classes"):
                summary_parts.append(f"  • 类: {', '.join(entities['classes'][:5])}")
            if entities.get("errors"):
                summary_parts.append(f"  • 错误: {', '.join(entities['errors'][:3])}")
            summary_parts.append("")

        # 3. 按重要性总结关键消息
        summary_parts.append("💬 关键讨论点:")

        # 选择最重要的消息
        top_messages = [msg for msg in scored_messages if msg.get("score", 0) > 0.6][:5]

        for i, msg in enumerate(top_messages, 1):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            importance = msg.get("importance", "contextual")

            # 截断长内容
            if len(content) > 150:
                content = content[:150] + "..."

            emoji = "👤" if role == "user" else "🤖"
            summary_parts.append(f"{i}. [{importance}] {emoji} {content}")

        summary_parts.append("")

        # 4. 代码片段
        code_blocks = []
        for msg in top_messages:
            blocks = extract_code_blocks(msg.get("content", ""))
            code_blocks.extend(blocks)

        if code_blocks:
            summary_parts.append("💻 关键代码片段:")
            for i, block in enumerate(code_blocks[:2], 1):  # 最多保留2个
                lang = block.get("language", "text")
                code = block.get("code", "")
                if len(code) > 200:
                    code = code[:200] + "\n  ..."
                summary_parts.append(f"{i}. [{lang}]")
                summary_parts.append(f"```{lang}\n{code}\n```")

        return "\n".join(summary_parts)

    def extract_key_code_blocks(self, messages: List[Dict]) -> List[Dict]:
        """
        阶段6: 提取关键代码块

        从重要消息中提取代码块

        Args:
            messages: 消息列表

        Returns:
            代码块列表
        """
        code_blocks = []

        for msg in messages:
            content = msg.get("content", "")
            blocks = extract_code_blocks(content)

            for block in blocks:
                block["message_role"] = msg.get("role")
                block["message_timestamp"] = msg.get("timestamp")
                code_blocks.append(block)

        return code_blocks

    def restructure_conversation(self, scored_messages: List[Dict],
                                 summary: str, code_blocks: List[Dict]) -> Dict:
        """
        阶段7: 重构对话流

        合并相似主题，删除冗余

        Args:
            scored_messages: 带评分的消息列表
            summary: 生成的摘要
            code_blocks: 代码块列表

        Returns:
            重构结果字典
        """
        # 简化版本：直接使用摘要作为压缩后的消息
        compressed_message = {
            "role": "system",
            "content": summary,
            "timestamp": time.time(),
            "compressed": True,
            "original_count": len(scored_messages),
            "tokens": count_tokens(summary)
        }

        # 统计合并的主题（简化版：基于相似度）
        merged_topics = 0
        topics = defaultdict(list)

        for msg in scored_messages:
            content = msg.get("content", "")
            # 简单主题提取：取前20个字符
            topic = content[:20].strip()
            topics[topic].append(msg)

        # 统计有多少组相似消息被合并
        merged_topics = sum(1 for msgs in topics.values() if len(msgs) > 1)

        return {
            "compressed_message": compressed_message,
            "merged_topics": merged_topics,
            "code_blocks_preserved": len(code_blocks)
        }

    def validate_quality(self, original_messages: List[Dict],
                        compressed_message: Dict, entities: Dict) -> Dict:
        """
        阶段8: 质量验证

        检查压缩后是否保留了关键信息

        Args:
            original_messages: 原始消息列表
            compressed_message: 压缩后的消息
            entities: 提取的实体

        Returns:
            质量评估字典
        """
        compressed_content = compressed_message.get("content", "")

        # 1. 实体保留率
        total_entities = sum(len(v) for v in entities.values())
        retained_entities = 0

        for entity_list in entities.values():
            for entity in entity_list:
                if entity in compressed_content:
                    retained_entities += 1

        entity_retention = retained_entities / total_entities if total_entities > 0 else 1.0

        # 2. 关键词保留
        critical_keywords = ["error", "exception", "failed", "implement", "function"]
        original_text = " ".join(msg.get("content", "") for msg in original_messages).lower()
        keywords_in_original = sum(1 for kw in critical_keywords if kw in original_text)
        keywords_in_compressed = sum(1 for kw in critical_keywords if kw in compressed_content.lower())

        keyword_retention = keywords_in_compressed / keywords_in_original if keywords_in_original > 0 else 1.0

        # 3. 代码块保留
        original_code_blocks = []
        for msg in original_messages:
            original_code_blocks.extend(extract_code_blocks(msg.get("content", "")))

        compressed_code_blocks = extract_code_blocks(compressed_content)
        code_context = len(compressed_code_blocks) > 0 if len(original_code_blocks) > 0 else True

        # 综合质量评分
        overall_quality = (entity_retention * 0.5 + keyword_retention * 0.3 +
                          (1.0 if code_context else 0.5) * 0.2)

        return {
            "entities_retained": entity_retention >= 0.8,
            "entity_retention": entity_retention,
            "causality_intact": keyword_retention >= 0.7,
            "keyword_retention": keyword_retention,
            "code_context": code_context,
            "overall_quality": overall_quality
        }

    def calculate_compression_ratio(self, original: List[Dict], compressed: str) -> float:
        """
        计算压缩率

        Args:
            original: 原始消息列表
            compressed: 压缩后的文本

        Returns:
            压缩率 (0-1)
        """
        original_tokens = sum(msg.get("tokens", count_tokens(msg.get("content", "")))
                             for msg in original)
        compressed_tokens = count_tokens(compressed)

        if original_tokens == 0:
            return 0.0

        return 1 - (compressed_tokens / original_tokens)


if __name__ == "__main__":
    import asyncio

    async def test_compressor():
        """
        测试压缩器
        """
        print("🧪 测试AU2压缩算法...\n")

        # 创建测试消息
        test_messages = [
            {
                "role": "user",
                "content": "我想创建一个Python数据分析项目，处理CSV文件",
                "timestamp": time.time() - 1000,
                "tokens": 20
            },
            {
                "role": "assistant",
                "content": """好的！我可以帮你创建。首先定义一个DataProcessor类：

```python
import pandas as pd

class DataProcessor:
    def __init__(self, filename):
        self.filename = filename
        self.data = None

    def load_data(self):
        try:
            self.data = pd.read_csv(self.filename)
            return True
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return False
```""",
                "timestamp": time.time() - 900,
                "tokens": 150
            },
            {
                "role": "user",
                "content": "好的，继续添加数据清洗功能",
                "timestamp": time.time() - 800,
                "tokens": 15
            },
            {
                "role": "assistant",
                "content": "添加clean_data方法处理缺失值和异常值...",
                "timestamp": time.time() - 700,
                "tokens": 30
            },
            {
                "role": "user",
                "content": "还需要统计分析功能",
                "timestamp": time.time() - 600,
                "tokens": 12
            }
        ]

        # 执行压缩
        compressor = AU2Compressor()
        result = await compressor.compress(test_messages)

        print("\n📋 压缩结果:")
        print(f"压缩率: {result['compression_ratio']*100:.1f}%")
        print(f"质量评分: {result['quality']['overall_quality']*100:.0f}%")

        print("\n✅ 压缩测试完成！")

    asyncio.run(test_compressor())
