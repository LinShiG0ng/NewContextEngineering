# 配置指南

本指南帮助你快速配置LLM驱动的上下文压缩功能。

## 🚀 快速配置（推荐）

### 使用交互式配置向导 ⭐

这是最简单的方法，适用于所有操作系统（Windows/Mac/Linux）：

```bash
python scripts/setup_llm.py
```

向导会自动帮你：
- ✅ 创建 `.env` 文件并保存API密钥
- ✅ 更新 `config.py` 配置
- ✅ 设置所有必要的参数
- ✅ 无需手动编辑任何文件

## 📋 配置步骤详解

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 选择压缩方法

系统支持三种压缩方法：

| 方法 | 压缩率 | 速度 | 成本 | 适用场景 |
|------|--------|------|------|---------|
| **规则方法** | 30-40% | ⚡ 极快 | 免费 | 少量消息、离线 |
| **LLM方法** | 60-75% | 🐢 较慢 | ~$0.0003/次 | 重要对话、长历史 |
| **混合方法** ⭐ | 60-75% | ⚡ 智能 | ~$0.0002/次 | **推荐** |

### 3. 配置LLM压缩（可选）

#### 方法A: 使用配置向导

```bash
python scripts/setup_llm.py
```

按提示选择：
1. 是否启用LLM压缩
2. 提供商（OpenAI/Anthropic）
3. 输入API密钥
4. 选择模型
5. 配置阈值

#### 方法B: 手动配置

**步骤1：** 创建 `.env` 文件

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

编辑 `.env` 文件，添加API密钥：

```bash
# OpenAI（推荐，性价比最高）
OPENAI_API_KEY=sk-your-openai-api-key

# 或 Anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
```

**步骤2：** 编辑 `config.py`

```python
# 启用LLM压缩
USE_LLM_COMPRESSION = True

# 选择提供商
LLM_COMPRESSION_PROVIDER = "openai"  # 或 "anthropic"

# 选择模型
LLM_COMPRESSION_MODEL = "gpt-4o-mini"  # 推荐
```

### 4. 测试配置

```bash
# 运行压缩测试
python tests/test_compression.py
```

预期输出：
```
✅ LLM压缩成功！
📊 压缩率: 70.2%
💰 成本: $0.000335
```

### 5. 启动系统

```bash
# Web界面（推荐）
python web_server.py
# 访问 http://localhost:8000

# 或命令行界面
python main.py
```

## 🔑 获取API密钥

### OpenAI（推荐）

1. 访问：https://platform.openai.com/api-keys
2. 注册/登录账号
3. 点击 "Create new secret key"
4. 复制密钥（格式：`sk-xxxxxxx`）
5. 粘贴到 `.env` 文件

**推荐模型：** `gpt-4o-mini`
- 成本：$0.15/1M输入 + $0.60/1M输出
- 示例：压缩1000条消息约 $0.008（约¥0.06）

### Anthropic

1. 访问：https://console.anthropic.com/settings/keys
2. 注册/登录账号
3. 点击 "Create Key"
4. 复制密钥（格式：`sk-ant-xxxxxxx`）
5. 粘贴到 `.env` 文件

**推荐模型：** `claude-3-5-haiku-20241022`
- 成本：$0.80/1M输入 + $4.00/1M输出
- 示例：压缩1000条消息约 $0.044（约¥0.32）

## 🪟 Windows系统特别说明

### 环境变量设置

**不推荐**使用Windows系统环境变量，因为设置复杂。推荐使用 `.env` 文件。

如果必须使用环境变量：

**临时设置（当前窗口）：**
```cmd
# CMD
set OPENAI_API_KEY=your-api-key

# PowerShell
$env:OPENAI_API_KEY="your-api-key"
```

**永久设置（系统级）：**
1. 右键"此电脑" → "属性"
2. 高级系统设置 → 环境变量
3. 新建用户变量
4. 变量名：`OPENAI_API_KEY`
5. 变量值：你的API密钥
6. 确定并重启命令行

### 文件编辑

推荐使用以下编辑器：
- 记事本（Windows自带）
- Notepad++
- VS Code

**注意：** 确保文件编码为 UTF-8。

## ⚙️ 高级配置

### 调整压缩参数

编辑 `config.py`：

```python
# 压缩阈值
AUTO_COMPACT_THRESHOLD = 0.92  # 92%触发压缩

# 混合模式阈值
HYBRID_LLM_THRESHOLD = 10  # 消息数超过10条用LLM
```

### 选择不同模型

**OpenAI：**
```python
LLM_COMPRESSION_MODEL = "gpt-4o-mini"      # 推荐，性价比最高
LLM_COMPRESSION_MODEL = "gpt-4o"           # 质量最好
LLM_COMPRESSION_MODEL = "gpt-3.5-turbo"    # 经济实惠
```

**Anthropic：**
```python
LLM_COMPRESSION_MODEL = "claude-3-5-haiku-20241022"   # 推荐
LLM_COMPRESSION_MODEL = "claude-3-5-sonnet-20241022"  # 平衡
LLM_COMPRESSION_MODEL = "claude-3-opus-20240229"      # 最高质量
```

### 调整温度和输出长度

```python
LLM_COMPRESSION_TEMPERATURE = 0.3     # 0.1-0.5，越低越稳定
LLM_COMPRESSION_MAX_TOKENS = 2000     # 压缩摘要最大长度
```

## 💰 成本估算

### 使用示例

假设压缩包含1000条消息的对话（约50K tokens）：

**OpenAI gpt-4o-mini：**
```
输入：50,000 tokens × $0.15/1M = $0.0075
输出：1,000 tokens × $0.60/1M = $0.0006
总计：$0.0081（约¥0.06）
```

**Anthropic claude-3-5-haiku：**
```
输入：50,000 tokens × $0.80/1M = $0.04
输出：1,000 tokens × $4.00/1M = $0.004
总计：$0.044（约¥0.32）
```

**混合模式（推荐）：**
```
假设20%使用LLM，80%使用规则方法
平均成本：$0.0016/次
```

### 成本控制

1. **使用混合模式**（默认）
2. **提高阈值** - 设置更高的 `HYBRID_LLM_THRESHOLD`
3. **选择便宜的模型** - gpt-4o-mini或claude-haiku
4. **监控使用** - 定期检查API账单

## ❌ 常见问题

### Q1: 配置向导提示"找不到python命令"

**Windows用户：**
- 重新安装Python，勾选"Add Python to PATH"
- 或使用 `py` 命令代替 `python`

### Q2: API密钥验证失败

**可能原因：**
1. API密钥输入错误（检查空格、换行）
2. 密钥已过期或被撤销
3. 账户余额不足

**解决方法：**
- 检查 `.env` 文件中密钥是否完整
- 重新生成API密钥
- 检查账户余额

### Q3: "ModuleNotFoundError: No module named 'openai'"

**原因：** 未安装依赖

**解决：**
```bash
pip install -r requirements.txt
```

### Q4: 测试时提示"Rate limit exceeded"

**原因：** API调用频率超限

**解决：**
- 等待几分钟后重试
- 升级API订阅
- 暂时禁用LLM压缩

### Q5: 如何禁用LLM压缩？

**方法1：** 重新运行配置向导
```bash
python scripts/setup_llm.py
```
选择 "n" 不启用

**方法2：** 手动编辑 `config.py`
```python
USE_LLM_COMPRESSION = False
```

### Q6: 压缩后效果不好

**调整方法：**
1. **提高输出长度** - 增加 `LLM_COMPRESSION_MAX_TOKENS`
2. **降低温度** - 减小 `LLM_COMPRESSION_TEMPERATURE`
3. **使用更好的模型** - 换用gpt-4o或claude-sonnet
4. **禁用LLM** - 对某些场景规则方法可能更好

### Q7: System Prompt被压缩了

**答：** 不应该发生。System Prompt受到特殊保护，永远不会被压缩。

如果发生，请检查：
- System Prompt的 `role` 字段是否为 "system"
- 是否有 `compressed: true` 标记

## 🔒 安全建议

1. **保护API密钥**
   - 不要将 `.env` 提交到Git（已在.gitignore中）
   - 不要在公开场合分享密钥
   - 定期更换密钥

2. **监控API使用**
   - OpenAI: https://platform.openai.com/usage
   - Anthropic: https://console.anthropic.com/settings/billing
   - 设置使用限额和告警

3. **敏感信息**
   - LLM压缩会将对话发送到API
   - 如有敏感信息，使用规则方法
   - 或考虑自建本地模型

## 📚 相关资源

- [使用指南](GUIDE.md) - Web界面和功能说明
- [快速开始](QUICKSTART.md) - 最简上手指南
- [项目README](../README.md) - 项目概览

## 🆘 获取帮助

遇到问题？
1. 查看上述常见问题
2. 运行诊断测试
3. 检查项目GitHub Issues
4. 查看详细日志输出

---

**配置成功后，就可以开始使用了！** 🎉

下一步：查看 [使用指南](GUIDE.md) 了解如何使用系统。
