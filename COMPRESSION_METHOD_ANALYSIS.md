# AU2压缩算法技术实现说明

## 核心问题：使用大模型还是规则方法？

**答案：当前完全基于规则方法，不调用大模型。**

## 详细技术实现

### 阶段1：消息分类

**方法：正则表达式 + 关键词匹配**

```python
# 定义关键词模式
critical_patterns = [
    r"error", r"exception", r"failed", r"bug", r"critical",
    r"错误", r"失败", r"异常", r"严重"
]

important_patterns = [
    r"implement", r"function", r"class", r"def ", r"async ",
    r"实现", r"函数", r"类", r"方法"
]

# 使用正则表达式匹配
if any(re.search(pattern, content_lower) for pattern in critical_patterns):
    msg["importance"] = "critical"
```

**分类逻辑：**
- 包含"error"、"exception" → Critical
- 包含"function"、"implement" → Important
- 包含"好的"、"ok" → Redundant
- 其他 → Contextual

### 阶段2：关键实体提取

**方法：正则表达式模式匹配**

```python
# 文件名提取
FILE_PATTERNS = [
    r'[\w\-]+\.\w+',  # 匹配 file.py, config.json
    r'[\w/\-]+/[\w\-]+\.\w+'  # 匹配 src/main.py
]

# 函数名提取
FUNCTION_PATTERNS = [
    r'def\s+(\w+)',  # Python: def function_name
    r'function\s+(\w+)',  # JavaScript: function name
    r'async\s+(?:def\s+)?(\w+)'  # async def/function
]

# 错误信息提取
ERROR_PATTERNS = [
    r'([\w\.]+Error)',  # Python errors
    r'Exception:\s*(.+)',
    r'Error:\s*(.+)'
]
```

**安全测试实体：**
```python
# IP地址提取
r'\b(?:\d{1,3}\.){3}\d{1,3}\b'

# 端口提取
r':(\d{2,5})\b'

# CVE编号提取
r'CVE-\d{4}-\d{4,7}'

# 工具识别（预定义集合）
PENTEST_TOOLS = {'nmap', 'sqlmap', 'burpsuite', 'metasploit', ...}
```

### 阶段3：知识图谱构建

**方法：共现分析（Co-occurrence Analysis）**

```python
# 分析实体在同一消息中的共现
for msg in messages:
    mentioned_entities = []

    # 找出该消息中提到的所有实体
    for entity in graph["nodes"].keys():
        if entity in content:
            mentioned_entities.append(entity)

    # 创建实体间的边（共现关系）
    for entity1 in mentioned_entities:
        for entity2 in mentioned_entities:
            if entity1 != entity2:
                create_edge(entity1, entity2)
```

**不使用：**
- ❌ NLP语义分析
- ❌ 依存句法分析
- ❌ 大模型理解

### 阶段4：重要性评分

**方法：启发式算法（Heuristic Scoring）**

```python
score = 0.0

# 1. 基础重要性权重
importance_weights = {
    "critical": 1.0,
    "important": 0.7,
    "contextual": 0.4,
    "redundant": 0.1
}
score += importance_weights[msg["importance"]]

# 2. 时间距离因子（越近越重要）
time_distance = current_time - msg["timestamp"]
if time_distance < 86400:  # 24小时内
    time_factor = 1 - (time_distance / 86400)
    score += time_factor * 0.3

# 3. 实体引用频率
entity_count = sum(1 for entity in entities if entity in content)
score += min(entity_count * 0.1, 0.5)

# 4. 代码复杂度
code_blocks = extract_code_blocks(content)
score += len(code_blocks) * 0.2

# 5. 长度因素
if len(content) < 20:
    score *= 0.5
```

**评分因素：**
- 消息重要性类别
- 时间新鲜度
- 实体密度
- 代码数量
- 消息长度

### 阶段5：生成压缩摘要

**方法：模板拼接（Template-based）**

```python
summary_parts = []

# 1. 固定开头
summary_parts.append("📝 对话历史摘要（已压缩）")

# 2. 列举关键实体（前N个）
summary_parts.append("🔑 关键实体:")
summary_parts.append(f"  • 文件: {', '.join(entities['files'][:5])}")
summary_parts.append(f"  • 函数: {', '.join(entities['functions'][:5])}")

# 3. 选择高分消息（score > 0.6的前5条）
top_messages = [msg for msg in scored_messages if msg.score > 0.6][:5]

summary_parts.append("💬 关键讨论点:")
for msg in top_messages:
    # 截断长内容
    content = msg["content"][:150] + "..."
    summary_parts.append(f"{i}. [{importance}] {emoji} {content}")

# 4. 拼接代码片段
summary_parts.append("💻 关键代码片段:")
summary_parts.append(f"```{lang}\n{code}\n```")

# 5. 简单字符串拼接
return "\n".join(summary_parts)
```

**不使用：**
- ❌ 大模型生成摘要
- ❌ 抽象式总结
- ❌ 语义理解
- ❌ 智能改写

### 阶段6-8：代码块保留、对话重构、质量验证

**方法：规则过滤 + 相似度计算**

```python
# 代码块提取：正则表达式
code_pattern = r'```(\w+)?\n(.*?)\n```'

# 主题合并：简单字符串比较
topic = content[:20].strip()  # 取前20个字符作为主题

# 质量验证：字符串包含检查
retained = sum(1 for entity in entities if entity in compressed_content)
entity_retention = retained / total_entities
```

## 当前方法的优缺点

### ✅ 优点

1. **速度快**
   - 无需等待API调用
   - 本地正则匹配，毫秒级响应
   - 适合实时压缩场景

2. **成本低**
   - 不消耗API tokens
   - 无需付费调用大模型
   - 可以频繁压缩

3. **可控性强**
   - 压缩逻辑透明可预测
   - 容易调试和优化
   - 不会产生幻觉内容

4. **隐私安全**
   - 数据不离开本地
   - 不发送到第三方API
   - 适合敏感数据处理

5. **离线可用**
   - 无需网络连接
   - 不依赖外部服务
   - 稳定性高

### ❌ 缺点

1. **理解能力有限**
   - 无法理解上下文语义
   - 只能基于关键词和模式
   - 可能误判重要性

2. **压缩质量一般**
   - 生成的摘要是拼接式的
   - 缺乏语义连贯性
   - 不够"自然"

3. **灵活性差**
   - 需要预定义规则
   - 难以适应新场景
   - 需要手动维护规则库

4. **语言理解弱**
   - 无法处理复杂语义
   - 同义词识别困难
   - 上下文推理能力弱

5. **压缩率受限**
   - 主要靠删除和截断
   - 无法真正"提炼"信息
   - 压缩率通常在50-70%

## 压缩率对比

### 当前规则方法

```
原始: 1000 tokens (10条消息)
压缩: 300-500 tokens (摘要)
压缩率: 50-70%
方法: 删除冗余 + 截断内容 + 提取实体
```

### 大模型方法（假设）

```
原始: 1000 tokens (10条消息)
压缩: 100-200 tokens (智能摘要)
压缩率: 80-90%
方法: 语义理解 + 信息提炼 + 智能改写
```

## 如果使用大模型应该如何改进？

### 方案1：混合方法（推荐）

```python
async def compress_with_llm(self, messages: List[Dict]) -> Dict:
    # 第一阶段：规则方法预处理
    classified = self.classify_messages(messages)  # 规则分类
    entities = self.extract_entities(classified)   # 正则提取
    scored = self.score_messages(messages, graph)  # 启发式评分

    # 第二阶段：大模型智能压缩
    top_messages = [msg for msg in scored if msg.score > 0.6][:10]

    prompt = f"""
请将以下对话压缩成简洁的摘要，保留关键信息：

关键实体：
- 文件: {entities['files']}
- 函数: {entities['functions']}
- 错误: {entities['errors']}

对话内容：
{format_messages(top_messages)}

要求：
1. 保留所有关键实体名称
2. 保留错误信息和解决方案
3. 保留重要的代码片段
4. 使用简洁的语言
"""

    # 调用大模型
    summary = await llm_client.generate(prompt)

    # 第三阶段：后处理验证
    quality = self.validate_quality(messages, summary, entities)

    return summary
```

**优点：**
- 结合规则的速度和大模型的理解能力
- 用规则预筛选，减少大模型token消耗
- 可以离线fallback到纯规则方法

### 方案2：纯大模型方法

```python
async def compress_with_pure_llm(self, messages: List[Dict]) -> Dict:
    # 直接将所有消息发送给大模型
    conversation = format_messages(messages)

    prompt = f"""
你是一个上下文压缩专家。请将以下对话压缩成简洁的摘要。

对话内容：
{conversation}

压缩要求：
1. 保留所有关键信息（文件名、函数名、错误信息）
2. 保留重要的代码片段
3. 保留决策过程和解决方案
4. 使用简洁、结构化的语言
5. 目标压缩率：70-80%

请生成压缩摘要：
"""

    summary = await llm_client.generate(prompt, max_tokens=500)
    return summary
```

**优点：**
- 压缩质量最高
- 语义理解最强
- 最接近"智能提炼"

**缺点：**
- 成本最高
- 速度最慢
- 需要网络

### 方案3：向量化 + 语义检索

```python
async def compress_with_embeddings(self, messages: List[Dict]) -> Dict:
    # 1. 将所有消息向量化
    embeddings = await embed_messages(messages)

    # 2. 聚类分析，找出主题
    clusters = kmeans_clustering(embeddings, n_clusters=3)

    # 3. 每个主题选择代表性消息
    representative_messages = []
    for cluster in clusters:
        # 选择最接近聚类中心的消息
        center = cluster.center
        closest_msg = find_closest_message(cluster.messages, center)
        representative_messages.append(closest_msg)

    # 4. 用大模型生成每个主题的摘要
    summaries = []
    for msg in representative_messages:
        summary = await llm_summarize(msg)
        summaries.append(summary)

    return "\n\n".join(summaries)
```

## 实现建议

如果要添加大模型支持，建议：

### 1. 保留现有规则方法作为基线

```python
class AU2Compressor:
    def __init__(self, use_llm: bool = False, llm_client = None):
        self.use_llm = use_llm
        self.llm_client = llm_client

    async def compress(self, messages):
        if self.use_llm and self.llm_client:
            return await self.compress_with_llm(messages)
        else:
            return await self.compress_with_rules(messages)
```

### 2. 提供配置选项

```python
# config.py
USE_LLM_COMPRESSION = os.getenv('USE_LLM', 'false').lower() == 'true'
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '500'))
```

### 3. 混合策略

```python
async def compress_hybrid(self, messages):
    # 规则方法预筛选
    important_messages = self.filter_by_rules(messages)

    # 如果消息少，直接用规则
    if len(important_messages) < 5:
        return self.compress_with_rules(messages)

    # 消息多，调用大模型
    return await self.compress_with_llm(important_messages)
```

## 总结

| 特性 | 规则方法（当前） | 大模型方法 | 混合方法 |
|-----|----------------|-----------|---------|
| 速度 | ⚡ 毫秒级 | 🐌 秒级 | ⚡ 快速 |
| 成本 | 💰 免费 | 💰💰💰 高 | 💰💰 中等 |
| 质量 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐⭐ 优秀 | ⭐⭐⭐⭐ 良好 |
| 离线 | ✅ 支持 | ❌ 需要网络 | ✅ 可降级 |
| 隐私 | ✅ 本地 | ⚠️ 发送API | ✅ 可选 |
| 可控 | ✅ 完全 | ⚠️ 黑盒 | ✅ 混合 |

**当前实现选择规则方法的原因：**
1. 零成本运行
2. 实时响应
3. 隐私安全
4. 可预测性
5. 适合频繁压缩的场景

**适合添加大模型的场景：**
1. 对压缩质量要求极高
2. 不在意成本和速度
3. 处理复杂语义理解任务
4. 长期对话的周期性压缩
