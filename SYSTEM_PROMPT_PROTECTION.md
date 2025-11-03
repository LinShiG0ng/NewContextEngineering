# System Prompt保护机制

## 概述

在上下文压缩过程中，System Prompt（系统提示词）包含了智能体的核心身份、能力和行为准则，**绝对不能被压缩**。一旦被压缩，智能体将失去对自己身份和能力的认知。

为了解决这个问题，我们实现了**System Prompt自动保护机制**。

## 功能特性

### 🔒 自动检测与保护

- 自动识别上下文中第一个 `role=system` 的消息
- 将其从压缩流程中分离出来
- 确保System Prompt永远不会被压缩
- 在构建最终上下文时，将其放在最前面

### 📊 Token计算优化

- System Prompt的token数不计入压缩率计算
- 压缩率只针对需要压缩的消息计算
- 保持统计数据的准确性

### 🎯 边界情况处理

- 如果只有System Prompt，直接返回，不执行压缩
- 如果没有System Prompt，正常执行压缩流程
- 支持后续追加的system消息（但只保护第一个）

## 使用示例

### 示例1：带有System Prompt的对话

```python
import asyncio
from compressor import AU2Compressor

async def example_with_system_prompt():
    messages = [
        {
            "role": "system",
            "content": "You are an AI security expert...",
            "timestamp": 1234567890,
            "tokens": 50
        },
        {
            "role": "user",
            "content": "帮我测试这个Web应用",
            "timestamp": 1234567900,
            "tokens": 20
        },
        # ... 更多消息
    ]

    compressor = AU2Compressor()
    result = await compressor.compress(messages)

    # System Prompt被保护
    print(f"System Prompt: {result['system_prompt']}")
    print(f"压缩后消息: {result['compressed_message']}")

asyncio.run(example_with_system_prompt())
```

### 示例2：在ContextManager中使用

```python
from context_manager import ContextManager

async def example_with_context_manager():
    manager = ContextManager(max_tokens=100000)

    # 添加System Prompt
    await manager.add_message(
        "system",
        "You are a penetration testing expert..."
    )

    # 添加对话消息
    await manager.add_message("user", "开始渗透测试")
    await manager.add_message("assistant", "好的，使用nmap扫描...")

    # 触发压缩（System Prompt会被自动保护）
    await manager.compress_if_needed(force=True)

    # 获取上下文（System Prompt在最前面）
    context = await manager.get_context()

    # context[0] 就是被保护的System Prompt
    assert context[0]['role'] == 'system'
    print("System Prompt已保护！")

asyncio.run(example_with_context_manager())
```

## 技术实现

### 1. Compressor层面

在 `compressor.py` 的 `compress()` 方法中：

```python
# 分离system prompt（第一个system消息永远不压缩）
system_prompt = None
messages_to_compress = messages

if messages and messages[0].get("role") == "system":
    system_prompt = messages[0]
    messages_to_compress = messages[1:]
    print("🔒 检测到System Prompt，将保持不压缩")

# 如果只有system prompt，无需压缩
if not messages_to_compress:
    return {
        "compressed_message": system_prompt,
        "system_prompt": system_prompt,
        # ...
    }

# 继续压缩其他消息...
```

返回结果中包含 `system_prompt` 字段：

```python
return {
    "compressed_message": restructured['compressed_message'],
    "system_prompt": system_prompt,  # 保留的system prompt
    # ...
}
```

### 2. ContextManager层面

在 `context_manager.py` 中：

**存储System Prompt:**

```python
# 保存system prompt（如果存在）
if compression_result.get("system_prompt"):
    self.preserved_system_prompt = compression_result["system_prompt"]
    print(f"🔒 System Prompt已保护，不会被压缩")
```

**构建上下文时优先添加:**

```python
async def get_context(self, current_query: Optional[str] = None):
    context = []

    # 0. 首先添加保留的system prompt（如果存在，永远在最前面）
    if self.preserved_system_prompt:
        context.append(self.preserved_system_prompt)

    # 1. 添加系统上下文（知识库）
    if self.system_context:
        context.append(self.system_context)

    # 2. 添加中期存储（压缩后的历史）
    # 3. 添加短期存储（最近的完整消息）
    # ...
```

## 测试验证

运行测试脚本验证功能：

```bash
python test_system_prompt_protection.py
```

测试覆盖：
- ✅ System Prompt被正确识别和分离
- ✅ System Prompt不被压缩
- ✅ System Prompt始终在上下文最前面
- ✅ 只有System Prompt的情况
- ✅ 没有System Prompt的情况

## 压缩效果示例

### 压缩前（5条消息）

```
1. [system] You are an AI security expert... (50 tokens)
2. [user] 我需要测试服务器192.168.1.100 (20 tokens)
3. [assistant] 使用nmap扫描... (30 tokens)
4. [user] 发现开放端口22, 80, 443, 3306 (25 tokens)
5. [assistant] 使用burpsuite拦截请求... (35 tokens)

总计: 160 tokens
```

### 压缩后（2条消息）

```
1. [system] You are an AI security expert... (50 tokens) ← 未压缩
2. [system] 📝 对话历史摘要（已压缩）
   关键实体: IP(192.168.1.100), 工具(nmap, burpsuite)
   关键讨论: 端口扫描、HTTP拦截
   (60 tokens)

总计: 110 tokens
压缩率: 31.3% (只计算非system prompt部分)
```

## 注意事项

1. **只保护第一个System Prompt**：如果上下文中有多个system消息，只有第一个会被特殊保护
2. **Token计算**：System Prompt的tokens不计入压缩率，但计入总体token使用量
3. **重置行为**：调用 `manager.reset()` 会清除保留的System Prompt
4. **位置保证**：System Prompt永远在最终上下文的最前面

## 适用场景

- 🤖 **智能体开发**：保护智能体的角色定义和能力声明
- 🔒 **安全测试**：保护渗透测试agent的行为准则和约束
- 🎭 **角色扮演**：保护角色设定不被压缩
- 📋 **任务规范**：保护任务的核心要求和规则

## 相关文件

- `compressor.py` - 压缩算法实现（System Prompt分离逻辑）
- `context_manager.py` - 上下文管理（System Prompt存储和使用）
- `test_system_prompt_protection.py` - 功能测试脚本

## 更新日志

- **2025-01-XX**: 初始实现System Prompt保护机制
- 支持自动检测和分离
- 支持在ContextManager中保护和使用
- 添加完整的测试覆盖
