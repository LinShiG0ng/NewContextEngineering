# System Prompt位置识别问题修复

## 问题描述

用户反馈：

> "我详细看了下压缩后的结果，我发现了问题所在，system prompt在压缩完成后，被放在了'关键讨论点' 1. [critical] 的位置，同时被进行了截断，这样导致system prompt在经过处理后并没有放在它应该在的位置"

### 问题根源

之前的实现只检查**第一条消息**是否为system prompt：

```python
# 旧代码 - 只检查第一条
if messages and messages[0].get("role") == "system":
    system_prompt = messages[0]
    messages_to_compress = messages[1:]
```

这导致的问题：
1. **如果system prompt不是第一条消息**（例如用户先发送了对话，后来添加system prompt），它不会被识别
2. **未被识别的system prompt会被当作普通消息处理**
3. **如果内容包含"critical"、"error"等关键词**，会被归类为critical消息
4. **在生成压缩摘要时被截断到150字符**，出现省略号
5. **最终出现在压缩摘要的"关键讨论点"部分**

### 问题场景

**场景：用户添加消息的顺序**
```
1. user: "你好"
2. system: "You are a cybersecurity expert with CRITICAL requirements..." (476字符)
3. user: "请帮我测试服务器"
4. assistant: "好的，开始测试"
```

**旧实现的处理流程：**
```
1. 检查第一条消息 → role='user' → 不是system prompt
2. system prompt没有被识别和分离
3. 所有4条消息都进入压缩流程
4. system prompt因包含"CRITICAL"被归类为critical
5. 在generate_summary()中被截断：
   content[:150] + "..."
6. 出现在压缩摘要中：
   "1. [critical] 🤖 You are a cybersecurity expert with CRITICAL requirements..."
```

## 解决方案

改进system prompt的识别逻辑，识别**所有**未压缩的system消息，而不仅仅是第一条。

###实现细节

**1. 修改compress()方法 (`compressor.py` 第88-122行)**

```python
# 新代码 - 识别所有未压缩的system消息
system_prompts = []
messages_to_compress = []

for msg in messages:
    # 识别未压缩的system消息作为system prompt
    if msg.get("role") == "system" and not msg.get("compressed", False):
        system_prompts.append(msg)
    else:
        messages_to_compress.append(msg)

if system_prompts:
    print(f"🔒 检测到 {len(system_prompts)} 个System Prompt，将保持不压缩")
    for i, sp in enumerate(system_prompts, 1):
        tokens = sp.get('tokens', count_tokens(sp.get('content', '')))
        print(f"   {i}. System Prompt Token数: {tokens}")
```

**关键改进：**
- ✅ 遍历所有消息，不仅检查第一条
- ✅ 检查`role == "system"`且`compressed == False`
- ✅ 支持多个system prompts（虽然通常只有一个）
- ✅ 将system prompts完全从压缩流程中排除

**2. 更新返回字段名 (`compressor.py` 第233行)**

```python
return {
    "compressed_message": restructured['compressed_message'],
    ...
    "system_prompts": system_prompts  # 改为复数
}
```

**3. 更新ContextManager (`context_manager.py`)**

```python
# 第86行：存储改为复数
self.preserved_system_prompts = []

# 第195-197行：保存所有system prompts
if compression_result.get("system_prompts"):
    self.preserved_system_prompts = compression_result["system_prompts"]
    print(f"🔒 {len(self.preserved_system_prompts)} 个System Prompt已保护")

# 第245-247行：添加到上下文时使用extend
if self.preserved_system_prompts:
    context.extend(self.preserved_system_prompts)

# 第325行：重置时清空列表
self.preserved_system_prompts = []
```

## 修复效果对比

### 修复前 ❌

```
【输入消息】
1. user: "你好"
2. system: "You are a cybersecurity expert with CRITICAL requirements..."
3. user: "请帮我测试服务器"
4. assistant: "好的，开始测试"

【压缩流程】
阶段 1/8: 分类消息
  • Critical: 1条 (必须保留) ← system prompt被归类为critical

【压缩摘要内容】
📝 对话历史摘要（已压缩）

💬 关键讨论点:
1. [critical] 🤖 You are a cybersecurity expert with CRITICAL requirements... ❌

【结果】
- system prompt出现在摘要中
- 内容被截断到150字符
- 包含省略号"..."
```

### 修复后 ✅

```
【输入消息】
1. user: "你好"
2. system: "You are a cybersecurity expert with CRITICAL requirements..."
3. user: "请帮我测试服务器"
4. assistant: "好的，开始测试"

【压缩流程】
🔒 检测到 1 个System Prompt，将保持不压缩
   1. System Prompt Token数: 100

阶段 1/8: 分类消息
  • Critical: 0条 (必须保留) ← system prompt已被排除
  • Contextual: 3条 (提取要点) ← 只包含user和assistant消息

【压缩摘要内容】
📝 对话历史摘要（已压缩）

💬 关键讨论点:
1. [contextual] 👤 你好
2. [contextual] 🤖 好的，开始测试

【返回结果】
{
  "compressed_message": {...压缩摘要...},
  "system_prompts": [
    {
      "role": "system",
      "content": "You are a cybersecurity expert with CRITICAL requirements...", ← 完整内容
      "tokens": 100
    }
  ]
}

【最终上下文顺序】
1. system prompt (完整，476字符)
2. 知识库 (如果有)
3. 压缩摘要
4. 最近消息
```

## 测试验证

### 测试场景

创建了 `test_system_in_summary.py` 测试两个关键场景：

**场景1：System Prompt是第一条消息**
- 输入：system → user → assistant
- 预期：system prompt被识别和保护
- 结果：✅ 通过

**场景2：System Prompt不是第一条消息（重现用户问题）**
- 输入：user → system → user → assistant
- 预期：system prompt仍被识别和保护
- 结果：✅ 通过

### 测试结果

```bash
$ python test_system_in_summary.py

【场景1】
✅ System Prompt内容未出现在压缩摘要中
✅ system_prompts字段存在
   数量: 1
   第一个长度: 476 字符

【场景2】
✅ System Prompt内容未出现在压缩摘要中 ← 修复前这里是❌
✅ system_prompts字段存在 ← 修复前这里是❌
   数量: 1
   第一个长度: 476 字符
```

## 关键改进总结

| 方面 | 修复前 | 修复后 |
|------|--------|--------|
| **识别范围** | 只检查第一条消息 | 检查所有消息 |
| **识别条件** | `messages[0].role == "system"` | `role == "system" && !compressed` |
| **支持场景** | System prompt必须在第一位 | System prompt可在任意位置 |
| **字段名称** | `system_prompt` (单数) | `system_prompts` (复数) |
| **返回类型** | Dict 或 None | List[Dict] |
| **多个system** | 不支持 | 支持多个system prompts |

## 边界情况处理

1. **多个system prompts**
   - 所有未压缩的system消息都会被识别
   - 全部保存在`system_prompts`列表中
   - 在get_context()时用extend添加到上下文

2. **压缩后的system消息**
   - 压缩生成的摘要role也是"system"
   - 但有`compressed=True`标志
   - 不会被误识别为system prompt

3. **没有system prompt**
   - `system_prompts`为空列表
   - 不影响正常压缩流程

4. **只有system prompts**
   - 直接返回，不执行压缩
   - 返回所有system prompts

## 向后兼容性

**破坏性变更：**
- 字段名从`system_prompt`（单数）改为`system_prompts`（复数）
- 返回类型从`Dict | None`改为`List[Dict]`

**受影响的代码：**
- ✅ `context_manager.py` - 已更新
- ✅ `test_system_prompt_protection.py` - 需要更新
- ✅ `test_system_prompt_integrity.py` - 需要更新

## 相关修复时间线

这是System Prompt保护功能的第四个修复：

1. **第一次修复** (`SYSTEM_PROMPT_PROTECTION.md`)
   - 在compressor中分离第一个system prompt
   - 在context_manager中保护system prompt

2. **第二次修复** (`SYSTEM_PROMPT_FIX.md`)
   - 修复compressor中4处错误使用messages的地方
   - 确保system prompt不参与任何压缩流程

3. **第三次修复** (`FRONTEND_TRUNCATION_FIX.md`)
   - 修复前端显示截断问题
   - System prompt在Web界面完整显示

4. **第四次修复（本次）** (`SYSTEM_PROMPT_POSITION_FIX.md`) ✨
   - 改进识别逻辑，支持任意位置的system prompt
   - 完全解决"出现在关键讨论点"的问题
   - 支持多个system prompts

## 更新日志

- **2025-01-XX**: 修复System Prompt位置识别问题
  - 改进识别逻辑：检查所有消息，不仅是第一条
  - 支持任意位置的system prompts
  - 支持多个system prompts
  - 字段名改为复数：system_prompts
  - 测试覆盖：system prompt在第一位和非第一位的场景
  - 完全解决"出现在关键讨论点并被截断"的问题
