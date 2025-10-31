# 📥 对话导入功能使用指南

## 功能简介

对话导入功能允许你将从其他平台（如ChatGPT、Claude等）导出的对话记录导入到系统中，然后测试AU2压缩算法的效果。

## 🎯 主要用途

1. **测试压缩效果**: 使用真实对话数据测试压缩算法
2. **对比分析**: 对比不同对话的压缩率
3. **快速体验**: 无需长时间对话即可看到压缩效果
4. **数据迁移**: 从其他平台迁移对话历史

## 🚀 使用方法

### 1. Web界面导入（推荐）

#### 步骤：

1. 启动Web服务
   ```bash
   ./start_web.sh
   ```

2. 在浏览器打开 http://localhost:8000

3. 点击"📥 导入对话"按钮

4. 在对话框中：
   - 选择格式类型（推荐"自动检测"）
   - 粘贴JSON格式的对话记录
   - 选择是否自动压缩
   - 点击"导入并测试压缩"

5. 查看导入结果和压缩统计

#### 界面功能：

- **格式类型选择**:
  - 自动检测（推荐）
  - ChatGPT格式
  - Claude格式
  - 通用格式

- **自动压缩开关**: 导入后自动检测是否需要压缩

- **格式示例**: 点击"查看格式示例"可以看到各种格式的示例

### 2. API调用导入

```bash
curl -X POST http://localhost:8000/api/import \
  -H "Content-Type: application/json" \
  -d '{
    "json_data": "[{\"role\":\"user\",\"content\":\"你好\"},{\"role\":\"assistant\",\"content\":\"你好！\"}]",
    "format_type": "auto",
    "auto_compress": true
  }'
```

## 📋 支持的格式

### 1. 通用格式（推荐）

最简单直接的格式，适用于大多数场景。

```json
[
  {"role": "user", "content": "你好，我想学习Python"},
  {"role": "assistant", "content": "你好！我很乐意帮助你学习Python。"},
  {"role": "user", "content": "从哪里开始比较好？"},
  {"role": "assistant", "content": "建议从基础语法开始..."}
]
```

**字段说明:**
- `role`: 角色，可以是 "user" 或 "assistant"
- `content`: 消息内容

### 2. ChatGPT导出格式

从ChatGPT导出的完整对话格式。

```json
{
  "title": "Python学习讨论",
  "mapping": {
    "message-1": {
      "id": "message-1",
      "message": {
        "author": {"role": "user"},
        "content": {"parts": ["你好，我想学习Python"]},
        "create_time": 1234567890
      }
    },
    "message-2": {
      "id": "message-2",
      "message": {
        "author": {"role": "assistant"},
        "content": {"parts": ["你好！我很乐意帮助你学习Python。"]},
        "create_time": 1234567891
      }
    }
  }
}
```

**如何获取:**
1. 在ChatGPT中打开对话
2. 点击右上角的"..."菜单
3. 选择"Export chat"
4. 复制导出的JSON

### 3. Claude导出格式

Claude API或Claude对话的标准格式。

```json
{
  "messages": [
    {
      "role": "user",
      "content": "你好，我想学习Python"
    },
    {
      "role": "assistant",
      "content": "你好！我很乐意帮助你学习Python。从基础语法开始是个好主意。"
    }
  ]
}
```

**或包含多种内容类型:**

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "你好，我想学习Python"}
      ]
    },
    {
      "role": "assistant",
      "content": [
        {"type": "text", "text": "你好！我很乐意帮助你学习Python。"}
      ]
    }
  ]
}
```

### 4. 其他变体格式

系统也支持一些常见的变体：

```json
{
  "conversation": [
    {"sender": "human", "message": "你好"},
    {"sender": "ai", "message": "你好！"}
  ]
}
```

或：

```json
{
  "chat_history": [
    {"author": "user", "text": "你好"},
    {"author": "bot", "text": "你好！"}
  ]
}
```

## 🔧 自定义格式适配

如果你的格式不被支持，可以手动转换为通用格式：

### Python脚本示例：

```python
import json

# 你的原始格式
original_data = {
    "chat": [
        {"from": "me", "msg": "你好"},
        {"from": "bot", "msg": "你好！"}
    ]
}

# 转换为通用格式
converted = []
for item in original_data["chat"]:
    role = "user" if item["from"] == "me" else "assistant"
    converted.append({
        "role": role,
        "content": item["msg"]
    })

# 输出JSON
print(json.dumps(converted, ensure_ascii=False, indent=2))
```

## 📊 导入后的效果

### 1. 查看导入统计

导入成功后，系统会显示：
- 总消息数
- 用户消息数
- 助手消息数
- 平均消息长度

### 2. 查看Token使用率

导入后，Token使用率面板会实时更新：
- 当前Token数
- 使用率百分比
- 状态提示

### 3. 自动压缩（如果启用）

如果启用了"自动压缩"选项：
- 系统会自动检测是否需要压缩
- 显示压缩统计（节省Token、压缩率等）
- 可以在"压缩内容"面板查看压缩结果

### 4. 查看压缩内容

导航到"压缩内容"面板可以看到：
- 压缩片段数量
- 每个片段的元数据
- 完整的压缩摘要内容

## 💡 实用场景

### 场景1: 测试长对话压缩

```bash
# 准备一个包含20+轮对话的JSON文件
# 导入到系统
# 观察压缩效果
```

**预期结果:**
- 导入20条消息
- Token使用率约60-80%
- 自动触发压缩
- 节省40-70%的Token

### 场景2: 对比不同主题的压缩率

```bash
# 导入技术讨论对话（含代码）
# 记录压缩率

# 重置对话

# 导入日常聊天对话
# 记录压缩率

# 对比两者的压缩效果
```

### 场景3: 快速演示系统功能

```bash
# 准备一个包含多轮深度讨论的JSON
# 一键导入
# 立即看到压缩过程和结果
# 无需手动逐条输入
```

## ⚠️ 注意事项

### 1. JSON格式要求

- 必须是有效的JSON（可以在 https://jsonlint.com/ 验证）
- 确保引号使用正确（双引号）
- 特殊字符需要转义

### 2. 消息数量限制

- 建议单次导入不超过100条消息
- 过多消息可能导致处理时间较长

### 3. 内容质量

- 空消息会被自动过滤
- 过短的消息可能影响压缩效果

### 4. 编码问题

- 确保JSON使用UTF-8编码
- 中文字符应正确显示

## 🐛 常见问题

### Q1: 提示"无效的JSON格式"

**A:** 检查：
1. 是否使用双引号（不是单引号）
2. 是否有多余的逗号
3. 是否缺少括号
4. 使用在线JSON验证工具检查

### Q2: 导入后没有看到消息

**A:** 检查：
1. JSON中是否真的包含消息
2. 消息的role字段是否正确
3. 消息内容是否为空

### Q3: 自动压缩没有触发

**A:** 可能原因：
1. Token使用率未达到压缩阈值（92%）
2. "自动压缩"开关未打开
3. 可以手动点击"手动压缩"按钮

### Q4: 导入的格式不被识别

**A:** 解决方案：
1. 尝试选择特定格式类型（而非"自动检测"）
2. 手动转换为通用格式
3. 查看浏览器控制台的错误信息

## 📝 示例数据

### 简单示例（用于测试）

```json
[
  {"role": "user", "content": "你好"},
  {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
  {"role": "user", "content": "告诉我关于上下文压缩的信息"},
  {"role": "assistant", "content": "上下文压缩是一种优化技术，用于减少发送给大语言模型的Token数量，同时保留关键信息。"},
  {"role": "user", "content": "它是如何工作的？"},
  {"role": "assistant", "content": "上下文压缩通过多种技术工作：1. 消息分类 2. 实体提取 3. 摘要生成 4. 重要性评分。"}
]
```

### 复杂示例（用于测试压缩）

准备一个包含15-20轮技术讨论的对话，包含：
- 代码片段
- 详细解释
- 问题和答案
- 多个主题

导入后，系统会自动触发压缩，你可以观察完整的压缩过程。

## 🎓 最佳实践

1. **从简单开始**: 先用3-5条消息测试导入功能
2. **验证JSON**: 导入前使用工具验证JSON格式
3. **启用自动压缩**: 第一次使用时建议启用，以便看到完整流程
4. **对比分析**: 尝试不同类型的对话，对比压缩效果
5. **保存示例**: 保存几个不同格式的示例，方便以后使用

## 🔗 相关文档

- [Web使用指南](WEB_GUIDE.md)
- [主README](README.md)
- [快速开始](QUICKSTART.md)

---

**Happy Importing! 🎉**
