"""
动态上下文注入器模块

根据当前查询智能恢复相关的历史上下文:
1. 意图分析 (识别用户意图和关键词)
2. 相关性评分 (计算历史片段与当前查询的相关性)
3. 智能片段检索 (找到最相关的历史片段)
4. 原始消息恢复 (当压缩信息不足时恢复原始消息)

这确保压缩不会影响对话的连贯性
"""

import re
import time
from typing import Dict, List, Optional, Tuple
from collections import Counter

from utils import extract_entities, calculate_similarity
from config import RELEVANCE_THRESHOLD, MAX_INJECTED_SEGMENTS, INTENT_KEYWORD_WEIGHTS


class ContextInjector:
    """
    动态上下文注入器

    根据当前查询智能注入相关的历史上下文
    """

    def __init__(self, relevance_threshold: float = RELEVANCE_THRESHOLD,
                 max_segments: int = MAX_INJECTED_SEGMENTS):
        """
        初始化注入器

        Args:
            relevance_threshold: 相关性阈值
            max_segments: 最多注入的片段数
        """
        self.relevance_threshold = relevance_threshold
        self.max_segments = max_segments

        # 统计信息
        self.stats = {
            "injections": 0,
            "total_segments_injected": 0
        }

    def analyze_intent(self, query: str) -> Dict:
        """
        分析用户意图

        识别查询的类型和关键信息:
        - 查询类型 (question/command/reference)
        - 关键实体
        - 关键词
        - 时间相关性

        Args:
            query: 用户查询

        Returns:
            意图分析结果
        """
        intent = {
            "query": query,
            "type": "question",  # question/command/reference
            "keywords": [],
            "entities": {},
            "temporal": False,  # 是否有时间相关
            "reference": False  # 是否引用之前的内容
        }

        # 1. 识别查询类型
        command_patterns = [
            r"请.*", r"帮我.*", r"创建.*", r"实现.*", r"修改.*",
            r"create", r"implement", r"modify", r"add"
        ]

        reference_patterns = [
            r"之前.*", r"刚才.*", r"上面.*", r"前面.*",
            r"previous", r"earlier", r"above"
        ]

        question_patterns = [
            r"什么.*", r"为什么.*", r"怎么.*", r"如何.*",
            r"what", r"why", r"how", r"when"
        ]

        query_lower = query.lower()

        if any(re.search(p, query, re.IGNORECASE) for p in command_patterns):
            intent["type"] = "command"
        elif any(re.search(p, query, re.IGNORECASE) for p in reference_patterns):
            intent["type"] = "reference"
            intent["reference"] = True
        elif any(re.search(p, query, re.IGNORECASE) for p in question_patterns):
            intent["type"] = "question"

        # 2. 提取实体
        intent["entities"] = extract_entities(query)

        # 3. 提取关键词
        intent["keywords"] = self._extract_keywords(query)

        # 4. 检查时间相关性
        temporal_patterns = [
            r"最近", r"刚才", r"之前", r"earlier", r"recent", r"last"
        ]
        intent["temporal"] = any(re.search(p, query, re.IGNORECASE) for p in temporal_patterns)

        return intent

    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词（去除停用词）

        Args:
            text: 文本

        Returns:
            关键词列表
        """
        # 停用词（简化版）
        stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            '请', '帮', '我', '你', '它', '这', '那', '什么', '怎么'
        }

        # 分词（简单版：按空格和标点分割）
        words = re.findall(r'\w+', text.lower())

        # 过滤停用词和短词
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # 返回出现频率最高的前10个
        word_freq = Counter(keywords)
        return [word for word, count in word_freq.most_common(10)]

    def find_relevant_segments(self, intent: Dict, history: List[Dict]) -> List[Dict]:
        """
        查找相关的历史片段

        Args:
            intent: 意图分析结果
            history: 历史消息列表

        Returns:
            相关片段列表（按相关性排序）
        """
        relevant_segments = []

        for msg in history:
            # 计算相关性分数
            relevance = self.calculate_relevance(intent, msg)

            if relevance >= self.relevance_threshold:
                segment = msg.copy()
                segment["relevance"] = relevance
                relevant_segments.append(segment)

        # 按相关性排序
        relevant_segments.sort(key=lambda x: x["relevance"], reverse=True)

        # 限制数量
        return relevant_segments[:self.max_segments]

    def calculate_relevance(self, intent: Dict, segment: Dict) -> float:
        """
        计算相关性分数

        考虑多个因素:
        1. 实体匹配度
        2. 关键词重叠度
        3. 语义相似度
        4. 时间距离
        5. 消息重要性

        Args:
            intent: 意图分析
            segment: 历史片段

        Returns:
            相关性分数 (0-1)
        """
        score = 0.0
        content = segment.get("content", "")

        # 1. 实体匹配 (权重: 0.3)
        entity_score = 0.0
        total_entities = 0

        for entity_type, entities in intent["entities"].items():
            for entity in entities:
                total_entities += 1
                if entity in content:
                    entity_score += 1

        if total_entities > 0:
            entity_score = entity_score / total_entities
            score += entity_score * 0.3

        # 2. 关键词重叠 (权重: 0.25)
        keyword_score = 0.0
        keywords = intent["keywords"]

        if keywords:
            matched_keywords = sum(1 for kw in keywords if kw in content.lower())
            keyword_score = matched_keywords / len(keywords)
            score += keyword_score * 0.25

        # 3. 语义相似度 (权重: 0.2)
        similarity = calculate_similarity(intent["query"], content)
        score += similarity * 0.2

        # 4. 时间距离 (权重: 0.15)
        if intent.get("temporal"):
            current_time = time.time()
            msg_time = segment.get("timestamp", current_time)
            time_distance = current_time - msg_time

            # 越近的消息分数越高
            if time_distance < 3600:  # 1小时内
                time_score = 1.0
            elif time_distance < 86400:  # 24小时内
                time_score = 0.5
            else:
                time_score = 0.2

            score += time_score * 0.15

        # 5. 消息重要性 (权重: 0.1)
        importance = segment.get("importance", "contextual")
        importance_weights = {
            "critical": 1.0,
            "important": 0.7,
            "contextual": 0.4,
            "redundant": 0.1
        }
        score += importance_weights.get(importance, 0.4) * 0.1

        return min(score, 1.0)

    async def inject_context(self, query: str, base_context: List[Dict],
                            full_history: Optional[List[Dict]] = None) -> List[Dict]:
        """
        动态注入相关上下文

        Args:
            query: 当前查询
            base_context: 基础上下文（通常是压缩后的）
            full_history: 完整历史（用于恢复原始消息）

        Returns:
            增强后的上下文
        """
        # 1. 分析意图
        intent = self.analyze_intent(query)

        # 2. 如果不需要注入（简单问候等），直接返回
        if not intent["keywords"] and not intent["entities"]:
            return base_context

        # 3. 查找相关片段
        relevant_segments = []

        # 从完整历史中查找
        if full_history:
            relevant_segments = self.find_relevant_segments(intent, full_history)

        # 4. 如果找到相关片段，注入到上下文
        if relevant_segments:
            self.stats["injections"] += 1
            self.stats["total_segments_injected"] += len(relevant_segments)

            # 构建增强上下文
            enhanced_context = base_context.copy()

            # 在基础上下文后、用户查询前插入相关片段
            injection_message = {
                "role": "system",
                "content": self._format_injected_context(relevant_segments),
                "injected": True,
                "timestamp": time.time()
            }

            enhanced_context.append(injection_message)

            return enhanced_context

        return base_context

    def _format_injected_context(self, segments: List[Dict]) -> str:
        """
        格式化注入的上下文

        Args:
            segments: 相关片段列表

        Returns:
            格式化的文本
        """
        lines = ["[相关历史上下文]", ""]

        for i, segment in enumerate(segments, 1):
            role = segment.get("role", "user")
            content = segment.get("content", "")
            relevance = segment.get("relevance", 0)

            # 截断长内容
            if len(content) > 200:
                content = content[:200] + "..."

            emoji = "👤" if role == "user" else "🤖"
            lines.append(f"{i}. {emoji} (相关度: {relevance:.0%})")
            lines.append(f"   {content}")
            lines.append("")

        return "\n".join(lines)

    def get_statistics(self) -> Dict:
        """
        获取注入统计信息

        Returns:
            统计字典
        """
        avg_segments = (self.stats["total_segments_injected"] / self.stats["injections"]
                       if self.stats["injections"] > 0 else 0)

        return {
            "注入次数": self.stats["injections"],
            "总注入片段数": self.stats["total_segments_injected"],
            "平均每次注入": f"{avg_segments:.1f}个片段"
        }


def test_injector():
    """
    测试注入器
    """
    print("🧪 测试动态上下文注入器...\n")

    # 创建注入器
    injector = ContextInjector()

    # 测试1: 意图分析
    print("=" * 60)
    print("测试1: 意图分析")
    print("=" * 60)

    test_queries = [
        "之前提到的DataProcessor类在哪个文件？",
        "帮我创建一个新的分析函数",
        "为什么会出现FileNotFoundError？"
    ]

    for query in test_queries:
        intent = injector.analyze_intent(query)
        print(f"\n查询: {query}")
        print(f"  类型: {intent['type']}")
        print(f"  关键词: {intent['keywords']}")
        print(f"  实体: {intent['entities']}")
        print(f"  引用: {intent['reference']}")

    # 测试2: 相关性计算
    print("\n" + "=" * 60)
    print("测试2: 相关性计算")
    print("=" * 60)

    intent = injector.analyze_intent("之前的DataProcessor类出错了")

    test_segments = [
        {
            "role": "assistant",
            "content": "创建DataProcessor类处理CSV文件...",
            "timestamp": time.time() - 1000,
            "importance": "important"
        },
        {
            "role": "user",
            "content": "好的谢谢",
            "timestamp": time.time() - 900,
            "importance": "redundant"
        },
        {
            "role": "user",
            "content": "运行时出现FileNotFoundError",
            "timestamp": time.time() - 800,
            "importance": "critical"
        }
    ]

    print(f"\n查询意图: {intent['query']}")
    print("\n相关性评分:")

    for i, segment in enumerate(test_segments, 1):
        relevance = injector.calculate_relevance(intent, segment)
        content = segment["content"][:50]
        print(f"{i}. [{segment['importance']}] {content}...")
        print(f"   相关性: {relevance:.2f}")

    # 测试3: 查找相关片段
    print("\n" + "=" * 60)
    print("测试3: 查找相关片段")
    print("=" * 60)

    relevant = injector.find_relevant_segments(intent, test_segments)
    print(f"\n找到{len(relevant)}个相关片段:")

    for segment in relevant:
        print(f"  • {segment['content'][:50]}... (相关度: {segment['relevance']:.2f})")

    print("\n✅ 注入器测试完成！")


if __name__ == "__main__":
    test_injector()
