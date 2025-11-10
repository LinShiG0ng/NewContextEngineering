# 🧠 智能上下文工程系统

一个完整的Python演示项目，展示类似Claude Code的智能上下文管理机制，支持LLM驱动的智能压缩、分层存储和动态注入。

## ✨ 核心特性

- 🤖 **LLM驱动压缩** - 使用GPT/Claude智能分析和压缩对话，压缩率高达70%+
- 🔀 **混合压缩系统** - 智能选择规则或LLM方法，平衡质量和成本
- 📊 **实时Token监控** - 可视化Token使用率，自动触发压缩
- 🗄️ **三层存储架构** - 短期/中期/长期分层管理
- 💉 **动态上下文注入** - 根据查询智能恢复相关历史
- 🌐 **现代化Web界面** - 实时查看压缩过程和统计数据
- 🔌 **多LLM支持** - OpenAI、Anthropic、Ollama等

## 🚀 快速开始

### 1. 安装依赖

```bash
git clone https://github.com/your-repo/NewContextEngineering.git
cd NewContextEngineering
pip install -r requirements.txt
```

### 2. 配置系统

**使用配置向导（推荐）：**
```bash
python scripts/setup_llm.py
```

向导会帮你：
- 选择压缩方法（规则/LLM/混合）
- 配置API密钥
- 选择模型
- 无需手动编辑文件

**或手动配置：**
```bash
# 复制配置文件
cp .env.example .env

# 编辑.env添加API密钥
OPENAI_API_KEY=sk-your-api-key
```

详细配置说明：[配置指南](docs/SETUP.md)

### 3. 启动系统

**Web界面（推荐）：**
```bash
python web_server.py
# 访问 http://localhost:8000
```

**命令行界面：**
```bash
python main.py
```

**测试压缩：**
```bash
python tests/test_compression.py
```

## 📁 项目结构

```
NewContextEngineering/
├── docs/                      # 📚 文档
│   ├── SETUP.md              # 配置指南
│   ├── GUIDE.md              # 使用指南
│   └── QUICKSTART.md         # 快速开始
│
├── tests/                     # 🧪 测试
│   └── test_compression.py   # 压缩测试
│
├── scripts/                   # 🔧 工具脚本
│   └── setup_llm.py          # 配置向导
│
├── web/                       # 🌐 Web前端
│   └── index.html
│
├── workspace/                 # 💾 运行时数据
├── examples/                  # 📋 示例数据
│
├── config.py                 # ⚙️ 配置
├── utils.py                  # 🛠️ 工具
├── storage.py                # 💿 存储
├── compressor.py             # 📦 规则压缩
├── llm_compressor.py        # 🤖 LLM压缩
├── hybrid_compressor.py     # 🔀 混合压缩
├── injector.py              # 💉 动态注入
├── knowledge_base.py        # 📚 知识库
├── context_manager.py       # 🎛️ 上下文管理
├── llm_client.py            # 🔌 LLM客户端
├── conversation_importer.py # 📥 对话导入
├── security_extensions.py   # 🔒 安全扩展
├── main.py                  # 🚀 CLI入口
└── web_server.py            # 🌐 Web入口
```

## 💡 使用示例

### Web界面

```bash
python web_server.py
```

功能：
- 💬 实时对话交互
- 📊 Token使用率可视化
- 🔄 查看压缩过程
- 📈 统计数据分析
- 📥 导入/导出对话

### 命令行

```bash
python main.py

# 基本命令
/help       # 帮助
/stats      # 统计信息
/compress   # 手动压缩
/view       # 查看压缩内容
/export     # 导出历史
```

### 编程接口

```python
from context_manager import ContextManager
import asyncio

async def main():
    # 初始化管理器
    manager = ContextManager()

    # 添加消息
    await manager.add_message("user", "你好，创建一个Python项目")

    # 获取上下文（自动压缩）
    context = await manager.get_context()

    # 查看统计
    stats = manager.get_statistics()
    print(stats)

asyncio.run(main())
```

## 📊 压缩方法对比

| 方法 | 压缩率 | 速度 | 成本 | 推荐场景 |
|------|--------|------|------|---------|
| **规则** | 30-40% | ⚡ 极快 | 免费 | 少量消息、离线 |
| **LLM** | 60-75% | 🐢 较慢 | ~$0.0003/次 | 重要对话、长历史 |
| **混合** ⭐ | 60-75% | ⚡ 智能 | ~$0.0002/次 | **日常使用** |

**成本示例：**
- 压缩1000条消息（~50K tokens）
- 使用gpt-4o-mini: ~$0.008（约¥0.06）
- 混合模式平均: ~$0.002/次

## 🔧 配置选项

### 压缩方法

编辑 `config.py`：

```python
# 启用LLM压缩（默认False）
USE_LLM_COMPRESSION = True

# 提供商和模型
LLM_COMPRESSION_PROVIDER = "openai"  # 或 "anthropic"
LLM_COMPRESSION_MODEL = "gpt-4o-mini"  # 性价比最高

# 混合模式阈值（消息数超过此值用LLM）
HYBRID_LLM_THRESHOLD = 10
```

### API密钥

编辑 `.env` 文件：

```bash
# OpenAI
OPENAI_API_KEY=sk-your-api-key

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-api-key
```

### 推荐模型

**OpenAI：**
- `gpt-4o-mini` ⭐ 性价比最高
- `gpt-4o` 质量最好
- `gpt-3.5-turbo` 经济实惠

**Anthropic：**
- `claude-3-5-haiku-20241022` ⭐ 性价比高
- `claude-3-5-sonnet-20241022` 平衡
- `claude-3-opus-20240229` 最高质量

**Qwen/通义千问（推荐国内用户）：**
- `qwen-plus-latest` ⭐ 性价比极高
- `qwen-turbo-latest` 更快更便宜
- `qwen-max-latest` 最高质量

## 📚 文档

- **[快速开始](docs/QUICKSTART.md)** - 5分钟快速上手
- **[配置指南](docs/SETUP.md)** - 详细配置说明（含Windows）
- **[使用指南](docs/GUIDE.md)** - 完整功能说明

## 🎯 核心算法

### 混合压缩系统

```python
if len(messages) < HYBRID_LLM_THRESHOLD:
    # 使用规则方法（免费、快速）
    return rule_based_compress(messages)
else:
    # 使用LLM方法（高质量）
    try:
        return llm_compress(messages)
    except:
        # LLM失败时降级到规则方法
        return rule_based_compress(messages)
```

### AU2规则压缩（8段式）

1. 消息分类 - Critical/Important/Contextual/Redundant
2. 实体提取 - 文件名、函数名、错误等
3. 知识图谱 - 构建实体关系网络
4. 重要性评分 - 多因素计算
5. 生成摘要 - 结构化压缩
6. 保留代码 - 提取关键代码块
7. 重构对话 - 合并相似主题
8. 质量验证 - 确保信息完整

### LLM智能压缩

使用大语言模型进行语义理解和信息提炼：
- 理解对话上下文和语义
- 识别关键决策和重要信息
- 保留技术细节和实体
- 生成结构化、易读的摘要

## 🌟 高级功能

### 对话导入

支持导入Claude Web界面导出的对话历史：

```python
from conversation_importer import ConversationImporter

importer = ConversationImporter()
result = importer.import_from_file("conversation.json")
```

### 安全测试场景

支持渗透测试和安全研究场景：

```python
from security_extensions import SecurityExtensions

security = SecurityExtensions()
security.add_pentest_context(
    target="目标系统",
    findings=["发现列表"]
)
```

自动识别和保护：
- 🔍 漏洞信息（CVE编号）
- 🎯 目标信息（IP、域名）
- 🔧 工具命令（nmap、burp等）
- 💉 Payload和注入语句

### 动态注入

根据当前查询智能恢复相关历史：

```python
# 自动检索相关上下文
context = await manager.get_context("之前的DataProcessor怎么实现的？")
# 会自动注入包含DataProcessor的历史片段
```

## ❓ 常见问题

**Q: 为什么需要上下文工程？**

A: 大模型的上下文窗口有限，长对话会超出限制。上下文工程通过智能压缩和管理，让你能进行几乎无限长的对话，同时节省成本。

**Q: LLM压缩会很贵吗？**

A: 不会。使用gpt-4o-mini，压缩1000条消息只需约$0.008（¥0.06）。混合模式平均成本更低。

**Q: System Prompt会被压缩吗？**

A: 不会。System Prompt受到特殊保护，永远不会被压缩，始终完整保留。

**Q: Windows系统如何配置？**

A: 使用配置向导最简单：`python scripts/setup_llm.py`。详见[配置指南](docs/SETUP.md)。

**Q: 支持哪些LLM？**

A: 支持OpenAI（GPT系列）、Anthropic（Claude）、Ollama（本地模型）及所有兼容OpenAI格式的API。

**Q: 可以用于生产环境吗？**

A: 这是一个演示项目，展示核心概念。用于生产需要更完善的错误处理、持久化存储、并发控制等。

## 📈 性能指标

基于实际测试：

| 指标 | 规则方法 | LLM方法 | 混合方法 |
|------|---------|---------|---------|
| 压缩率 | 30-40% | 60-75% | 60-75% |
| 信息保留率 | >85% | >95% | >95% |
| 压缩耗时 | <0.1秒 | 1-3秒 | 智能 |
| 成本 | $0 | ~$0.0003 | ~$0.0002 |

## 🤝 贡献

欢迎贡献代码、报告问题或提出改进建议！

## 📄 许可证

MIT License

## 🙏 致谢

感谢Claude Code团队提供的灵感，以及OpenAI、Anthropic提供的优秀工具。

---

**🎉 开始你的上下文工程之旅！**

```bash
# 快速开始
python scripts/setup_llm.py  # 配置
python web_server.py         # 启动
```

有问题？查看[文档](docs/)或提交Issue。
