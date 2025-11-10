# 🚀 快速开始指南

## 5分钟上手

### 步骤1: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤2: 配置API（三选一）

#### 选项A: 交互式配置（推荐）

```bash
python main.py --interactive
```

跟随提示完成配置。

#### 选项B: 使用模拟模式（无需API）

```bash
python main.py --mock
```

适合测试系统功能。

#### 选项C: 手动配置

```bash
# 复制配置文件
cp .env.example .env

# 编辑.env，填入你的API密钥
# LLM_API_KEY=sk-your-key-here
```

### 步骤3: 启动演示

```bash
python main.py
```

## 基本使用

### 开始对话

```
💬 用户> 你好，请介绍一下Python
🤖 助手> Python是一种...
```

### 查看统计

```
💬 用户> /stats
```

### 手动压缩

```
💬 用户> /compress
```

### 对比效果

```
💬 用户> /compare
```

### 查看帮助

```
💬 用户> /help
```

## 配置示例

### OpenAI (GPT-3.5)

```bash
# .env
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-3.5-turbo
```

### Anthropic (Claude)

```bash
# .env
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-xxx
LLM_MODEL=claude-3-5-sonnet-20241022
```

### Ollama (本地)

```bash
# .env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
```

## 演示效果

系统会在Token使用率达到92%时自动压缩：

```
⚠️  Token使用率达到 94%，触发自动压缩！

🔄 正在执行AU2智能压缩...

✅ 压缩完成！
  节省Token: 5,264 (70.0%)
  信息保留率: 95%
```

## 常见问题

**Q: 我没有API密钥怎么办？**
A: 使用 `python main.py --mock` 模拟模式。

**Q: 如何调整压缩阈值？**
A: 编辑 `config.yaml` 文件中的 `auto_compact_threshold`。

**Q: 支持哪些模型？**
A: 支持所有OpenAI格式的API。

## 更多信息

详见 [README.md](README.md)
