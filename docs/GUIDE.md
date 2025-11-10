# 使用指南

全面的功能使用说明，包括Web界面、对话导入、安全测试和CLI使用。

## 📑 目录

1. [Web界面使用](#web界面使用)
2. [对话导入功能](#对话导入功能)
3. [安全测试场景](#安全测试场景)
4. [命令行使用](#命令行使用)
5. [API参考](#api参考)

---

## 🌐 Web界面使用

### 启动Web服务

```bash
python web_server.py
```

访问：http://localhost:8000

### 主要功能

#### 1. 实时对话

**使用方法：**
1. 在输入框输入问题
2. 点击"发送"或按Enter键
3. 查看LLM响应和统计信息

**显示信息：**
- 💬 对话内容
- 📊 每条消息的Token数
- 💰 估算成本
- ⏱️ 响应时间

#### 2. Token使用率监控

**实时显示：**
- 📈 可视化进度条
- 🔢 当前Token / 最大Token
- ⚠️ 状态提示

**颜色含义：**
- 🟢 绿色 (0-60%) - 正常
- 🟡 黄色 (60-80%) - 警告
- 🔴 红色 (80%+) - 即将触发压缩

#### 3. 压缩功能

**自动压缩：**
- Token使用率达到92%时自动触发

**手动压缩：**
- 点击"手动压缩"按钮
- 立即执行压缩
- 查看压缩效果

**压缩信息显示：**
- 原始Token数
- 压缩后Token数
- 节省Token数
- 压缩率
- 信息保留率

#### 4. 查看上下文

**当前上下文：**
- 点击"查看上下文"
- 显示发送给LLM的完整消息列表
- 包括压缩摘要、系统消息、最近对话

**压缩内容：**
- 点击"查看压缩内容"
- 显示历史压缩的详细信息
- 包含关键实体、讨论点等

#### 5. 统计信息

点击"查看统计"查看：
- 💬 对话统计（总消息数、用户/助手消息）
- 🔄 压缩统计（压缩次数、节省Token、压缩率）
- 🏗️ 存储结构（短期/中期/长期存储情况）
- 📚 知识库状态

#### 6. 对话管理

**导出对话：**
```
点击"导出历史" → 下载JSON文件
```

**重置对话：**
```
点击"重置对话" → 清空所有历史（保留知识库）
```

### API文档

访问：http://localhost:8000/docs

FastAPI自动生成的交互式API文档，可以：
- 查看所有API端点
- 测试API调用
- 查看请求/响应格式

---

## 📥 对话导入功能

### 导入Claude对话历史

系统支持导入从Claude Web界面导出的对话历史JSON文件。

#### 1. 导出Claude对话

在Claude Web界面：
1. 打开对话
2. 点击右上角"···"菜单
3. 选择"Export conversation"
4. 下载JSON文件

#### 2. 导入到系统

**方法A: Web界面导入**

1. 访问 http://localhost:8000
2. 点击"导入对话"按钮
3. 选择导出的JSON文件
4. 等待处理完成
5. 查看导入结果

**方法B: 使用导入工具**

```python
from conversation_importer import ConversationImporter

importer = ConversationImporter()
result = importer.import_from_file("conversation.json")

print(f"导入 {result['message_count']} 条消息")
print(f"总Token: {result['total_tokens']}")
```

#### 3. 导入后功能

- ✅ 完整保留对话历史
- ✅ 自动识别用户/助手消息
- ✅ 计算Token使用量
- ✅ 可立即进行压缩测试
- ✅ 支持继续对话

#### 4. 支持的格式

系统支持以下JSON格式：

```json
{
  "chat_messages": [
    {
      "sender": "human",
      "text": "用户消息内容"
    },
    {
      "sender": "assistant",
      "text": "助手回复内容"
    }
  ]
}
```

---

## 🔒 安全测试场景

系统扩展支持安全测试和渗透测试场景。

### 渗透测试模式

#### 1. 使用安全扩展

```python
from security_extensions import SecurityExtensions

# 初始化安全扩展
security = SecurityExtensions()

# 添加渗透测试上下文
security.add_pentest_context(
    target="目标系统描述",
    findings=["发现1", "发现2"]
)
```

#### 2. 安全相关实体识别

系统会自动识别和保护安全相关信息：

- 🔍 **漏洞信息**: CVE编号、漏洞类型
- 🎯 **目标信息**: IP地址、域名、端口
- 🔧 **工具命令**: nmap、burp等工具使用记录
- 💉 **Payload**: 注入语句、测试数据
- 🔑 **凭证信息**: 用户名、密码模式

#### 3. 压缩时的特殊处理

**关键信息保留：**
- Critical级别的安全发现永不删除
- 漏洞细节和利用方法完整保留
- 工具命令和输出结果保留

**结构化存储：**
```
## 安全测试发现
### 高危漏洞
- CVE-2024-XXXX: SQL注入
- 影响范围：...
- 利用方法：...

### 中危漏洞
...
```

### 典型使用场景

#### 场景1: 渗透测试记录

```python
# 记录扫描结果
manager.add_message("user", "扫描目标: example.com")
manager.add_message("assistant", """
扫描结果:
- 端口80: HTTP (开放)
- 端口443: HTTPS (开放)
- 端口22: SSH (开放)
发现: 使用弱SSL协议
""")

# 后续测试
manager.add_message("user", "测试SQL注入")
# ... 更多对话

# 压缩时，关键发现会被保留
```

#### 场景2: 漏洞研究

```python
# 讨论漏洞细节
manager.add_message("user", "CVE-2024-1234的利用方法")
manager.add_message("assistant", "该漏洞的利用步骤...")

# 压缩后，CVE编号和关键细节会被识别并保留
```

#### 场景3: 工具使用记录

```python
# 记录工具命令
manager.add_message("user", "nmap -sV -p- target.com")
manager.add_message("assistant", "扫描结果...")

# 命令和结果会被标记为重要信息
```

### 安全注意事项

⚠️ **重要提示：**

1. **敏感信息**
   - 不要在LLM压缩中处理真实的密码和密钥
   - 敏感数据应使用规则压缩方法
   - 或完全关闭压缩功能

2. **合规使用**
   - 仅用于授权的渗透测试
   - 遵守相关法律法规
   - 不得用于非法目的

3. **数据保护**
   - 定期清理测试数据
   - 注意导出文件的安全性
   - 使用加密存储敏感记录

---

## 💻 命令行使用

### 启动CLI

```bash
python main.py
```

### 基本命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示所有命令 |
| `/stats` | 查看统计信息 |
| `/history` | 查看对话历史 |
| `/context` | 查看当前上下文 |
| `/view` | 查看压缩内容 |
| `/compress` | 手动触发压缩 |
| `/reset` | 重置对话 |
| `/config` | 查看配置 |
| `/test` | 测试API连接 |
| `/compare` | 对比压缩效果 |
| `/export` | 导出对话历史 |
| `/quit` | 退出程序 |

### 使用示例

#### 基本对话

```
💬 用户> 你好，我想创建一个Python项目
🤖 助手> 你好！我很乐意帮助你...

[Token使用率: 28% ▓▓▓░░░░░░░] ✅ 正常
```

#### 查看压缩内容

```
💬 用户> /view

📝 压缩后的上下文内容
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

压缩片段 #1
────────────────────────────────────────────────
📊 元数据:
  • 压缩状态: ✅ 已压缩
  • 原始消息数: 14条
  • Token数: 2,256
  • 创建时间: 2025-01-10 10:30:15

📄 完整内容:
...
```

#### 手动压缩

```
💬 用户> /compress

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 正在执行压缩...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 压缩完成！

📊 压缩效果:
  原始Tokens: 7,520
  压缩后Tokens: 2,256
  节省Tokens: 5,264 (70.0%)
  信息保留率: 95%
```

#### 对比测试

```
💬 用户> /compare

📊 压缩效果对比测试
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

测试问题: "总结一下我们之前讨论的要点"

【当前上下文】
🔄 正在调用API (5条消息, 2,300 tokens)...
🤖 响应: 我们讨论了以下要点...

📊 响应质量: ⭐⭐⭐⭐⭐ (详细且准确)
⏱️  响应时间: 2.1秒
💰 成本估算: $0.0046
```

### 模拟模式

无需真实API即可测试系统：

```bash
python main.py --mock
```

---

## 📚 API参考

### REST API端点

基础URL: `http://localhost:8000`

#### POST /chat

发送消息并获取响应。

**请求：**
```json
{
  "message": "用户消息内容"
}
```

**响应：**
```json
{
  "response": "助手回复内容",
  "usage": {
    "current_tokens": 1500,
    "max_tokens": 8000,
    "usage_rate": 0.1875
  },
  "compressed": false
}
```

#### POST /compress

手动触发压缩。

**响应：**
```json
{
  "success": true,
  "original_tokens": 7520,
  "compressed_tokens": 2256,
  "saved_tokens": 5264,
  "compression_ratio": 0.7,
  "new_usage": 0.28
}
```

#### GET /context

获取当前上下文。

**响应：**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "...",
      "tokens": 350
    },
    ...
  ],
  "total_tokens": 3200
}
```

#### GET /stats

获取统计信息。

**响应：**
```json
{
  "dialog_stats": {...},
  "compression_stats": {...},
  "storage_structure": {...},
  "knowledge_base": {...}
}
```

#### POST /import

导入对话历史。

**请求：**
```json
{
  "conversation_data": {...}
}
```

#### POST /reset

重置对话。

**响应：**
```json
{
  "success": true,
  "message": "对话已重置"
}
```

#### GET /export

导出对话历史。

**响应：** JSON文件下载

### WebSocket端点

#### WS /ws

实时双向通信。

**连接：**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

**消息格式：**
```json
{
  "type": "chat|compress|stats|...",
  "data": {...}
}
```

---

## 💡 最佳实践

### 1. 对话管理

- 定期使用 `/stats` 查看系统状态
- Token使用率超过60%时注意监控
- 重要对话记得导出备份

### 2. 压缩策略

- 使用混合压缩模式（默认）
- 对于重要对话，手动选择压缩时机
- 压缩后检查关键信息是否保留

### 3. 成本控制

- 使用规则方法处理简单对话
- 启用LLM压缩处理长对话
- 监控API使用量和成本

### 4. 安全测试

- 敏感信息使用规则压缩
- 定期清理测试数据
- 导出文件注意保密

---

## 🆘 故障排除

### Web界面无法访问

**检查：**
1. 服务是否正常启动
2. 端口8000是否被占用
3. 防火墙设置

**解决：**
```bash
# 查看端口占用
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# 更换端口
uvicorn web_server:app --port 8080
```

### 对话导入失败

**检查：**
1. JSON文件格式是否正确
2. 文件编码是否为UTF-8
3. 文件大小是否过大

**解决：**
- 使用文本编辑器检查JSON格式
- 转换文件编码为UTF-8
- 大文件分批导入

### API响应慢

**可能原因：**
1. LLM API响应慢
2. 网络连接问题
3. Token数过大

**解决：**
- 检查网络连接
- 使用更快的模型
- 及时压缩减少Token数

---

## 📖 相关文档

- [配置指南](SETUP.md) - 系统配置和API设置
- [快速开始](QUICKSTART.md) - 最快上手方式
- [项目README](../README.md) - 项目概览

---

**需要更多帮助？** 查看项目GitHub Issues或联系维护者。
