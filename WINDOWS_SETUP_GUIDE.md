# Windows系统配置指南 - LLM压缩功能

本指南专门为Windows用户提供简单易懂的LLM压缩配置步骤。

## 🎯 快速配置（推荐）

### 方法1: 使用交互式配置向导 ⭐ 最简单

1. **打开命令提示符或PowerShell**
   - 按 `Win + R`，输入 `cmd` 或 `powershell`
   - 或在项目文件夹中，按住 `Shift` + 右键，选择"在此处打开PowerShell窗口"

2. **运行配置向导**
   ```bash
   python setup_llm_compression.py
   ```

3. **按照提示操作**
   - 选择是否启用LLM压缩（y/n）
   - 选择提供商（OpenAI 或 Anthropic）
   - 输入API密钥
   - 选择模型
   - 配置阈值

4. **完成！**
   - 配置会自动保存到 `.env` 和 `config.py` 文件
   - 无需手动编辑任何文件

**示例截图：**
```
================================================================================
🤖 LLM压缩配置向导 - Windows友好版本
================================================================================

本向导将帮助你配置LLM驱动的上下文压缩功能。

─────────────────────────────────────────────────────────────────────
📋 步骤1: 是否启用LLM压缩？
─────────────────────────────────────────────────────────────────────

LLM压缩可以将压缩率从30-40%提升至60-75%，但需要调用API（有小额成本）。

选项:
  y - 启用（推荐，如果你有OpenAI或Anthropic API密钥）
  n - 不启用（使用免费的规则压缩方法）

是否启用LLM压缩？ (默认: n): y

─────────────────────────────────────────────────────────────────────
📋 步骤2: 选择LLM提供商
─────────────────────────────────────────────────────────────────────

...
```

---

## 📝 手动配置

如果你想手动配置，请按照以下步骤操作。

### 步骤1: 创建 .env 文件

1. **打开项目文件夹**
   - 找到项目所在的文件夹

2. **复制示例文件**
   - 找到 `.env.example` 文件
   - 复制一份并重命名为 `.env`

   或在命令行中执行：
   ```bash
   copy .env.example .env
   ```

3. **编辑 .env 文件**
   - 用记事本或其他文本编辑器打开 `.env` 文件
   - 找到以下行：

   ```bash
   # OpenAI API密钥（用于LLM压缩）
   OPENAI_API_KEY=your-openai-api-key

   # Anthropic API密钥（用于LLM压缩）
   ANTHROPIC_API_KEY=your-anthropic-api-key
   ```

4. **填入你的API密钥**

   如果使用OpenAI：
   ```bash
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

   如果使用Anthropic：
   ```bash
   ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

5. **保存文件**

### 步骤2: 编辑 config.py 文件

1. **用文本编辑器打开 config.py**
   - 可以使用记事本、VS Code、Notepad++等

2. **找到以下配置项并修改：**

   ```python
   # ==================== LLM压缩配置 ====================

   # 压缩方法 ("rule", "llm", "hybrid")
   COMPRESSION_METHOD = "hybrid"  # 默认使用混合方法

   # LLM压缩相关配置
   USE_LLM_COMPRESSION = True  # 改为 True（启用LLM压缩）
   LLM_COMPRESSION_PROVIDER = "openai"  # 或 "anthropic"
   LLM_COMPRESSION_MODEL = "gpt-4o-mini"  # 推荐使用性价比高的模型
   LLM_COMPRESSION_TEMPERATURE = 0.3
   LLM_COMPRESSION_MAX_TOKENS = 2000

   # 混合压缩阈值（消息数超过此值才使用LLM）
   HYBRID_LLM_THRESHOLD = 10
   ```

3. **根据你的选择修改：**

   **使用OpenAI gpt-4o-mini（推荐）：**
   ```python
   USE_LLM_COMPRESSION = True
   LLM_COMPRESSION_PROVIDER = "openai"
   LLM_COMPRESSION_MODEL = "gpt-4o-mini"
   ```

   **使用Anthropic Claude Haiku：**
   ```python
   USE_LLM_COMPRESSION = True
   LLM_COMPRESSION_PROVIDER = "anthropic"
   LLM_COMPRESSION_MODEL = "claude-3-5-haiku-20241022"
   ```

4. **保存文件**

---

## 🔑 如何获取API密钥

### OpenAI API密钥

1. 访问：https://platform.openai.com/
2. 登录或注册账号
3. 进入 API Keys 页面：https://platform.openai.com/api-keys
4. 点击 "Create new secret key"
5. 复制生成的密钥（格式：`sk-xxxxxxxxx`）
6. **重要**：立即保存密钥，离开页面后无法再次查看

**费用说明：**
- gpt-4o-mini: $0.15/1M输入 + $0.60/1M输出
- 示例：压缩1000条消息约花费 $0.008（约¥0.06）

### Anthropic API密钥

1. 访问：https://console.anthropic.com/
2. 登录或注册账号
3. 进入 Settings → API Keys
4. 点击 "Create Key"
5. 复制生成的密钥（格式：`sk-ant-xxxxxxxxx`）
6. **重要**：立即保存密钥

**费用说明：**
- claude-3-5-haiku: $0.80/1M输入 + $4.00/1M输出
- 示例：压缩1000条消息约花费 $0.044（约¥0.32）

---

## ✅ 测试配置

配置完成后，测试是否正常工作：

```bash
# 运行对比测试
python test_llm_compression.py
```

**预期输出：**
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

✅ LLM压缩成功！

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
```

如果看到 `✅ LLM压缩成功！`，说明配置正确！

---

## 🚀 启动系统

配置完成后，启动Web服务：

```bash
python web_server.py
```

然后在浏览器访问：http://localhost:8000

---

## ❌ 常见问题

### Q1: 运行配置向导时提示"找不到python命令"

**原因：** Python未添加到系统PATH

**解决方法：**
1. 重新安装Python，勾选"Add Python to PATH"
2. 或手动添加Python到系统环境变量

### Q2: API密钥配置后仍提示"Authentication failed"

**可能原因：**
1. API密钥输入错误（多余空格、换行）
2. API密钥已过期或被撤销
3. 账户余额不足

**解决方法：**
1. 检查 `.env` 文件中密钥是否完整、无多余字符
2. 重新生成API密钥
3. 检查账户余额：https://platform.openai.com/usage

### Q3: 提示"ModuleNotFoundError: No module named 'openai'"

**原因：** 未安装依赖包

**解决方法：**
```bash
pip install openai anthropic
```

或安装所有依赖：
```bash
pip install -r requirements.txt
```

### Q4: 在Windows中如何设置环境变量？

**不推荐**：Windows环境变量设置复杂，建议使用 `.env` 文件

**如果必须使用环境变量：**

1. **临时设置（当前命令行窗口有效）：**
   ```cmd
   # CMD
   set OPENAI_API_KEY=your-api-key

   # PowerShell
   $env:OPENAI_API_KEY="your-api-key"
   ```

2. **永久设置（系统级）：**
   - 右键"此电脑" → "属性"
   - 点击"高级系统设置"
   - 点击"环境变量"
   - 在"用户变量"中点击"新建"
   - 变量名：`OPENAI_API_KEY`
   - 变量值：你的API密钥
   - 点击"确定"
   - **重启命令行窗口**

### Q5: 如何禁用LLM压缩，改回规则压缩？

**方法1：重新运行配置向导**
```bash
python setup_llm_compression.py
```
选择 `n` 不启用LLM压缩

**方法2：手动修改config.py**
```python
USE_LLM_COMPRESSION = False  # 改为 False
```

### Q6: 测试时提示"Rate limit exceeded"

**原因：** API调用频率超限

**解决方法：**
- 等待几分钟后重试
- 升级API订阅计划
- 使用混合模式减少API调用

### Q7: 成本会不会很高？

**答：** 成本非常低

- **规则方法**：完全免费
- **混合方法**（推荐）：平均 ~$0.002/次
- **LLM方法**：~$0.0003-0.001/次

**示例：**
- 每天压缩10次对话：约 $0.02/天（¥0.15）
- 每月：约 $0.60（¥4.3）

**建议：**
- 启用混合模式（自动选择最优方法）
- 设置较高的阈值（如20条消息）

---

## 📚 进阶配置

### 调整混合模式阈值

在 `config.py` 中：

```python
# 消息数少于此值使用规则方法，大于等于此值使用LLM方法
HYBRID_LLM_THRESHOLD = 10  # 默认

# 节省成本：更少使用LLM
HYBRID_LLM_THRESHOLD = 20

# 追求质量：更多使用LLM
HYBRID_LLM_THRESHOLD = 5
```

### 选择不同的模型

**OpenAI模型：**
```python
LLM_COMPRESSION_MODEL = "gpt-4o-mini"      # 推荐，性价比最高
LLM_COMPRESSION_MODEL = "gpt-4o"           # 质量最好，成本较高
LLM_COMPRESSION_MODEL = "gpt-3.5-turbo"    # 经济实惠
```

**Anthropic模型：**
```python
LLM_COMPRESSION_MODEL = "claude-3-5-haiku-20241022"   # 推荐，性价比高
LLM_COMPRESSION_MODEL = "claude-3-5-sonnet-20241022"  # 平衡
LLM_COMPRESSION_MODEL = "claude-3-opus-20240229"      # 最高质量
```

### 调整压缩质量参数

```python
# 温度：控制输出的随机性（0-1）
LLM_COMPRESSION_TEMPERATURE = 0.3  # 默认，较确定
LLM_COMPRESSION_TEMPERATURE = 0.1  # 更确定，更稳定
LLM_COMPRESSION_TEMPERATURE = 0.5  # 更多样化

# 最大输出tokens
LLM_COMPRESSION_MAX_TOKENS = 2000  # 默认
LLM_COMPRESSION_MAX_TOKENS = 1500  # 更简洁
LLM_COMPRESSION_MAX_TOKENS = 3000  # 更详细
```

---

## 🔒 安全提示

1. **保护API密钥**
   - 不要将 `.env` 文件提交到Git
   - 不要在公开场合分享密钥
   - 定期更换密钥

2. **.env 已自动添加到 .gitignore**
   - 配置向导会自动处理
   - 确认 `.gitignore` 文件中包含 `.env`

3. **监控API使用**
   - OpenAI: https://platform.openai.com/usage
   - Anthropic: https://console.anthropic.com/settings/billing

4. **设置使用限制**
   - 在API提供商控制台设置每月使用上限
   - 避免意外超支

---

## 📞 获取帮助

如果遇到问题：

1. **查看详细文档**
   - [LLM压缩完整指南](LLM_COMPRESSION_GUIDE.md)
   - [README](README.md)

2. **运行诊断**
   ```bash
   python test_llm_compression.py
   ```

3. **检查配置**
   ```bash
   python
   >>> import config
   >>> print(config.USE_LLM_COMPRESSION)
   >>> print(config.LLM_COMPRESSION_PROVIDER)
   >>> print(config.LLM_COMPRESSION_MODEL)
   ```

4. **查看日志**
   - 运行时的错误信息
   - API响应信息

---

## ✨ 总结

### 最简单的方法：

```bash
# 1. 运行配置向导
python setup_llm_compression.py

# 2. 按提示操作

# 3. 测试配置
python test_llm_compression.py

# 4. 启动系统
python web_server.py
```

### 核心文件：

- **.env** - 存储API密钥（不要提交到Git）
- **config.py** - 系统配置选项
- **setup_llm_compression.py** - 交互式配置向导

### 推荐配置：

- 提供商：OpenAI
- 模型：gpt-4o-mini
- 阈值：10条消息
- 成本：~$0.002/次

---

**祝配置顺利！有问题随时查看文档或提问。** 🎉
