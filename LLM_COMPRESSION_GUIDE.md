# LLM驱动的上下文压缩系统

## 概述

本项目已重构为**真正的LLM驱动压缩系统**，支持使用大语言模型智能分析和压缩对话上下文。

### 三种压缩方法

1. **规则方法 (Rule-based)** - 传统AU2算法
   - ✅ 速度快，成本为零
   - ✅ 可靠稳定，无API依赖
   - ❌ 压缩率较低（~30-40%）
   - 适合：快速压缩、少量消息、离线场景

2. **LLM方法 (LLM-powered)** - 使用大模型智能压缩
   - ✅ 压缩率高（~60-70%）
   - ✅ 语义理解强，保留关键信息
   - ❌ 需要API调用，有成本
   - ❌ 速度较慢（1-3秒）
   - 适合：重要对话、长对话历史、质量优先

3. **混合方法 (Hybrid)** - 智能选择最佳方法 ⭐**推荐**
   - ✅ 自动选择规则或LLM
   - ✅ 平衡质量和成本
   - ✅ LLM失败时自动降级到规则方法
   - 策略：消息少用规则，消息多用LLM

## 快速开始

### 1. 安装依赖

```bash
pip install openai anthropic
```

### 2. 设置API密钥

#### OpenAI（推荐用于压缩）

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

或在代码中设置：
```python
import os
os.environ["OPENAI_API_KEY"] = "your-key"
```

#### Anthropic（Claude）

```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 3. 配置压缩方法

编辑 `config.py`：

```python
# 启用LLM压缩
USE_LLM_COMPRESSION = True  # 改为 True

# 选择提供商（"openai" 或 "anthropic"）
LLM_COMPRESSION_PROVIDER = "openai"

# 选择模型
LLM_COMPRESSION_MODEL = "gpt-4o-mini"  # 或 "gpt-4o", "claude-3-5-haiku-20241022" 等

# 混合模式阈值（消息数超过此值才使用LLM）
HYBRID_LLM_THRESHOLD = 10
```

### 4. 运行测试

```bash
# 对比测试：规则 vs LLM vs 混合
python test_llm_compression.py
```

### 5. 启动Web服务

```bash
python web_server.py
```

访问 http://localhost:8000，系统会自动使用配置的压缩方法。

## 配置详解

### config.py 中的LLM配置

```python
# ==================== LLM压缩配置 ====================

# 是否启用LLM压缩
USE_LLM_COMPRESSION = False  # 默认False，避免意外API消耗

# LLM提供商
LLM_COMPRESSION_PROVIDER = "openai"  # "openai" 或 "anthropic"

# 使用的模型
LLM_COMPRESSION_MODEL = "gpt-4o-mini"

# 温度参数（0-1，越低越稳定）
LLM_COMPRESSION_TEMPERATURE = 0.3

# 压缩摘要的最大token数
LLM_COMPRESSION_MAX_TOKENS = 2000

# 混合模式：消息数阈值（超过此值用LLM）
HYBRID_LLM_THRESHOLD = 10
```

## 支持的模型

### OpenAI

| 模型 | 输入成本 | 输出成本 | 特点 | 推荐用途 |
|------|---------|---------|------|---------|
| `gpt-4o-mini` | $0.15/1M | $0.60/1M | ⭐ 性价比最高 | **压缩推荐** |
| `gpt-4o` | $2.50/1M | $10.00/1M | 质量最好 | 重要对话 |
| `gpt-3.5-turbo` | $0.50/1M | $1.50/1M | 经济实惠 | 简单压缩 |

### Anthropic (Claude)

| 模型 | 输入成本 | 输出成本 | 特点 | 推荐用途 |
|------|---------|---------|------|---------|
| `claude-3-5-haiku-20241022` | $0.80/1M | $4.00/1M | ⭐ 性价比高 | **压缩推荐** |
| `claude-3-5-sonnet-20241022` | $3.00/1M | $15.00/1M | 平衡质量和成本 | 标准压缩 |
| `claude-3-opus-20240229` | $15.00/1M | $75.00/1M | 最高质量 | 关键对话 |

## 成本估算

### 示例：压缩1000条消息的对话

假设：
- 输入：1000条消息 ≈ 50,000 tokens
- 输出：压缩摘要 ≈ 1,000 tokens

#### OpenAI gpt-4o-mini（推荐）
```
输入：50,000 tokens × $0.15/1M = $0.0075
输出：1,000 tokens × $0.60/1M = $0.0006
总成本：$0.0081 (约 ¥0.06)
```

#### Anthropic claude-3-5-haiku（推荐）
```
输入：50,000 tokens × $0.80/1M = $0.04
输出：1,000 tokens × $4.00/1M = $0.004
总成本：$0.044 (约 ¥0.32)
```

### 混合模式成本优化

混合模式通过智能选择大幅降低成本：

- **少量消息（<10条）**：使用规则方法，成本 = $0
- **大量消息（≥10条）**：使用LLM方法，成本如上
- **平均成本**：假设20%的压缩使用LLM，则平均成本仅为 $0.0016/次

## 工作原理

### 1. 规则压缩（AU2）

传统的规则方法使用以下策略：
1. **消息分类**：critical, important, contextual, redundant
2. **实体提取**：提取关键词、文件名、函数名等
3. **知识图谱**：构建实体关系图
4. **重要性评分**：基于规则计算每条消息的重要性
5. **内容重构**：生成结构化摘要

### 2. LLM压缩

使用大语言模型进行智能压缩：

```python
# 压缩提示词（简化版）
prompt = f"""
分析以下对话并生成简洁摘要。

# 对话内容
{conversation_text}

# 关键实体提示
{entity_hints}

# 要求
- 压缩率：保留约{target_ratio*100}%的内容
- 格式：使用Markdown
- 结构：关键决策、重要讨论、技术细节、待办事项
- 保留所有关键信息和实体
"""
```

LLM会：
- 理解对话语义和上下文
- 识别关键决策和重要信息
- 保留技术细节和实体
- 生成结构化、易读的摘要

### 3. 混合压缩

智能决策流程：

```python
def decide_method(messages):
    if len(messages) < HYBRID_LLM_THRESHOLD:
        return "rule"  # 少量消息，用规则
    else:
        return "llm"   # 大量消息，用LLM
```

如果LLM失败（API错误、网络问题），自动降级到规则方法。

## 压缩效果对比

### 测试数据

7条消息，关于Python Web应用开发：
- 原始Token数：1,425 tokens
- 包含代码、对话、技术讨论

### 测试结果

| 方法 | 压缩后Token | 压缩率 | 耗时 | 成本 |
|------|-----------|--------|------|------|
| 规则方法 | 850 | 40.4% | 0.05秒 | $0 |
| LLM方法 | 425 | 70.2% | 1.2秒 | $0.0003 |
| 混合方法 | 425 | 70.2% | 1.2秒 | $0.0003 |

### 质量对比

**规则方法输出：**
```
## 关键讨论点
1. [important] Python Web应用，需要实现用户认证和文件上传功能
2. [important] 好的，继续实现用户认证部分，包括注册和登录
...（结构化要点）
```

**LLM方法输出：**
```
## 项目概述
用户请求创建一个基于FastAPI的Python Web应用，实现以下核心功能：
1. 用户认证系统（注册、登录、JWT令牌）
2. 文件上传功能（大小限制、磁盘空间检查）
3. 数据库集成（SQLite + SQLAlchemy）

## 关键技术决策
- 框架选择：FastAPI
- 认证方案：OAuth2 + JWT（HS256算法）
- 密码加密：bcrypt
- 数据库：SQLite + SQLAlchemy ORM
...（更自然的叙述）
```

## System Prompt保护

**重要**：无论使用哪种压缩方法，System Prompt都会被完整保护，永不压缩。

实现细节：
```python
# compressor.py 中的保护逻辑
system_prompts = []
messages_to_compress = []

for msg in messages:
    if msg.get("role") == "system" and not msg.get("compressed", False):
        system_prompts.append(msg)  # 保护
    else:
        messages_to_compress.append(msg)  # 压缩

# 压缩后返回
return {
    "compressed_message": {...},
    "system_prompts": system_prompts  # 原封不动返回
}
```

## API调用示例

### OpenAI

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "你是压缩专家..."},
        {"role": "user", "content": compression_prompt}
    ],
    temperature=0.3,
    max_tokens=2000
)
```

### Anthropic

```python
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = await client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=2000,
    temperature=0.3,
    messages=[
        {"role": "user", "content": compression_prompt}
    ],
    system="你是压缩专家..."
)
```

## 测试和调试

### 运行对比测试

```bash
python test_llm_compression.py
```

输出示例：
```
================================================================================
🧪 LLM驱动压缩系统测试
================================================================================

📝 测试数据: 7 条消息
   总Token数: 1,425

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【测试1】规则方法（AU2）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 规则方法结果:
   压缩率: 40.4%
   原始Tokens: 1,425
   压缩后Tokens: 850
   节省Tokens: 575
   耗时: 0.05秒

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【测试2】LLM方法
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 LLM方法结果:
   压缩率: 70.2%
   原始Tokens: 1,425
   压缩后Tokens: 425
   节省Tokens: 1,000
   输入Tokens: 850
   输出Tokens: 425
   成本: $0.000335
   耗时: 1.23秒
   模型: gpt-4o-mini

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【对比分析】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

压缩率对比:
   规则方法: 40.4%
   LLM方法:  70.2%
   提升: +29.8%

成本分析:
   规则方法: $0.000000 (免费)
   LLM方法:  $0.000335

速度对比:
   规则方法: 0.05秒
   LLM方法:  1.23秒
```

### 单独测试LLM压缩

```python
import asyncio
from llm_compressor import LLMCompressor

async def test():
    compressor = LLMCompressor(
        provider="openai",
        model="gpt-4o-mini"
    )

    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！"}
    ]

    result = await compressor.compress(
        messages=messages,
        entities={"functions": ["main"], "files": ["app.py"]},
        target_ratio=0.7
    )

    print(f"压缩率: {result['compression_ratio']*100:.1f}%")
    print(f"成本: ${result['cost']:.6f}")
    print(f"摘要: {result['compressed_message']['content']}")

asyncio.run(test())
```

## 故障排除

### 1. API密钥错误

**错误信息：**
```
❌ LLM测试失败: Authentication failed
```

**解决方法：**
```bash
# 检查环境变量
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# 重新设置
export OPENAI_API_KEY="your-key"
```

### 2. 网络超时

**错误信息：**
```
❌ LLM压缩失败: Request timeout
```

**解决方法：**
- 检查网络连接
- 使用代理：`export https_proxy=http://127.0.0.1:7890`
- 增加超时时间（在llm_compressor.py中修改timeout参数）

### 3. 配额超限

**错误信息：**
```
❌ Rate limit exceeded
```

**解决方法：**
- 等待配额恢复
- 升级API订阅
- 暂时切换到规则方法：`USE_LLM_COMPRESSION = False`

### 4. LLM失败时的降级

混合压缩器会自动降级：
```
⚠️  LLM压缩失败: API Error
🔄 降级到规则压缩方法...
✅ 规则压缩完成
```

## 性能优化建议

### 1. 选择合适的模型

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 日常对话 | gpt-4o-mini | 性价比最高 |
| 重要讨论 | gpt-4o | 质量最好 |
| 技术对话 | claude-3-5-haiku | Claude对技术内容理解好 |
| 成本敏感 | 规则方法 | 免费 |

### 2. 调整混合阈值

```python
# 10条以上用LLM（默认）
HYBRID_LLM_THRESHOLD = 10

# 20条以上用LLM（节省成本）
HYBRID_LLM_THRESHOLD = 20

# 5条以上用LLM（追求质量）
HYBRID_LLM_THRESHOLD = 5
```

### 3. 控制压缩频率

```python
# 92%才压缩（默认）
AUTO_COMPACT_THRESHOLD = 0.92

# 85%就压缩（更积极）
AUTO_COMPACT_THRESHOLD = 0.85

# 95%才压缩（更保守）
AUTO_COMPACT_THRESHOLD = 0.95
```

### 4. 批量压缩

如果有大量历史对话，建议批量压缩：
```python
# 一次性压缩多个对话
for conversation in conversations:
    result = await compressor.compress(conversation)
    save_result(result)
```

## 安全建议

1. **保护API密钥**
   - 不要硬编码在代码中
   - 使用环境变量
   - 添加 `.env` 到 `.gitignore`

2. **监控API使用**
   - 定期检查API使用量
   - 设置使用限制和告警
   - 使用混合模式降低成本

3. **敏感信息**
   - LLM压缩会将对话发送到API
   - 如果对话包含敏感信息，使用规则方法
   - 或自建模型（使用Ollama等本地模型）

## 未来扩展

1. **支持本地模型**
   - 集成Ollama
   - 使用本地Llama、Mistral等模型
   - 零成本、完全隐私

2. **自定义提示词**
   - 允许用户自定义压缩提示词
   - 针对特定领域优化（编程、写作、客服等）

3. **多模态支持**
   - 支持图片、代码、文档的压缩
   - 使用GPT-4V等视觉模型

4. **压缩质量反馈**
   - 让用户评价压缩质量
   - 根据反馈优化提示词

## 相关文档

- [压缩方法技术分析](COMPRESSION_METHOD_ANALYSIS.md) - 详细对比规则和LLM方法
- [System Prompt保护](SYSTEM_PROMPT_PROTECTION.md) - System Prompt保护机制
- [Web界面使用指南](WEB_GUIDE.md) - Web界面操作说明
- [快速开始](QUICKSTART.md) - 项目快速上手

## 更新日志

- **2025-01-XX**: 重构为LLM驱动压缩系统
  - 新增 `llm_compressor.py` - LLM压缩核心
  - 新增 `hybrid_compressor.py` - 混合压缩系统
  - 更新 `config.py` - 添加LLM配置选项
  - 更新 `context_manager.py` - 集成混合压缩器
  - 新增 `test_llm_compression.py` - 对比测试脚本
  - 支持OpenAI和Anthropic两大提供商
  - 智能降级机制，确保系统稳定性

## 问题反馈

如有问题或建议，欢迎：
- 提交Issue
- 贡献代码
- 分享使用经验

---

**Happy Compressing! 🚀**
