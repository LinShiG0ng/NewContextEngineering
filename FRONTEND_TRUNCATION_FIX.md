# 前端System Prompt截断显示问题修复

## 问题描述

用户反馈：在Web界面的"当前上下文"面板中，压缩后查看上下文时，system prompt的内容被省略号（...）截断，无法看到完整内容。

### 用户场景

1. 用户添加一个长的system prompt（例如1000+字符）
2. 添加对话消息并触发压缩
3. 在Web界面查看"当前上下文"面板
4. **问题**：System prompt只显示前200字符，后面显示"..."

### 问题示例

**完整的System Prompt（1682字符）：**
```
You are an advanced AI assistant specialized in cybersecurity and penetration testing.

Your capabilities include:
- Network reconnaissance and scanning using tools like nmap, masscan, and rustscan
- Vulnerability assessment and exploitation using Metasploit, Burp Suite, and custom scripts
...（还有很多内容）
You must NEVER engage in unauthorized testing or malicious activities.
```

**Web界面显示（修复前）：**
```
You are an advanced AI assistant specialized in cybersecurity and penetration testing.

Your capabilities include:
- Network reconnaissance and scanning using tools like nmap, masscan...  ❌
```

## 根本原因

在前端代码 `web/index.html` 第450行，"当前上下文"面板显示消息内容时，**所有消息**都被统一截断到200字符：

```vue
<div style="margin-top: 8px; color: #606266; font-size: 13px;">
    {{ msg.content.substring(0, 200) }}{{ msg.content.length > 200 ? '...' : '' }}
</div>
```

这个限制是为了防止界面显示过长的对话消息，但它也影响了system prompt的显示。

### 为什么会有这个问题？

1. **后端没有问题**：后端的compressor.py和context_manager.py都正确保护了system prompt
2. **数据传输没有问题**：API返回的JSON中system prompt是完整的
3. **前端显示有问题**：前端在渲染时统一截断了所有消息

## 解决方案

区分不同类型的消息，对system prompt和其他消息采用不同的显示策略：

- **System prompt（非压缩）**：完整显示，不截断
- **其他消息**：截断到200字符，添加省略号

### 实现细节

修改 `web/index.html` 第449-458行：

```vue
<!-- 修复前 -->
<div style="margin-top: 8px; color: #606266; font-size: 13px;">
    {{ msg.content.substring(0, 200) }}{{ msg.content.length > 200 ? '...' : '' }}
</div>

<!-- 修复后 -->
<div style="margin-top: 8px; color: #606266; font-size: 13px; white-space: pre-wrap; word-break: break-word;">
    <template v-if="msg.role === 'system' && !msg.compressed">
        <!-- System prompt完整显示，不截断 -->
        {{ msg.content }}
    </template>
    <template v-else>
        <!-- 其他消息截断到200字符 -->
        {{ msg.content.substring(0, 200) }}{{ msg.content.length > 200 ? '...' : '' }}
    </template>
</div>
```

### 判断条件

```javascript
msg.role === 'system' && !msg.compressed
```

- `msg.role === 'system'`：确保是system角色的消息
- `!msg.compressed`：排除压缩后的摘要消息（它们的role也是system）

### CSS改进

添加了两个CSS属性以改善长文本显示：
- `white-space: pre-wrap`：保留换行和空格，自动换行
- `word-break: break-word`：长单词在边界处断开

## 修复效果

### 修复前
```
当前上下文面板：
┌─────────────────────────────────────┐
│ SYSTEM                              │
│ 100 tokens                          │
│ You are an advanced AI assistant... │  ❌ 只显示200字符
└─────────────────────────────────────┘
```

### 修复后
```
当前上下文面板：
┌─────────────────────────────────────┐
│ SYSTEM                              │
│ 420 tokens                          │
│ You are an advanced AI assistant    │  ✅ 完整显示
│ specialized in cybersecurity and    │
│ penetration testing.                │
│                                     │
│ Your capabilities include:          │
│ - Network reconnaissance...         │
│ - Vulnerability assessment...       │
│ ...（完整内容）                       │
│                                     │
│ You must NEVER engage in            │
│ unauthorized testing...             │
└─────────────────────────────────────┘
```

## 测试验证

### 方法1：使用测试脚本

运行 `reproduce_user_issue.py` 并启动Web服务器：

```bash
# 生成测试数据
python reproduce_user_issue.py

# 启动服务器
python web_server.py
```

然后访问 http://localhost:8000，查看"当前上下文"面板。

### 方法2：手动测试

1. 启动Web服务器：`python web_server.py`
2. 访问 http://localhost:8000
3. 在聊天框输入一个长的system prompt（建议1000+字符）
4. 发送几条对话消息
5. 手动触发压缩（如果token使用率高）或添加更多消息自动触发
6. 查看"当前上下文"面板
7. 验证system prompt完整显示，没有省略号

### 验证要点

✅ **System prompt完整显示**
- 长度超过200字符的system prompt完整显示
- 没有省略号（...）
- 所有段落和内容都可见
- 换行和格式保持正确

✅ **其他消息正常截断**
- User和Assistant消息仍然截断到200字符
- 压缩摘要消息仍然截断到200字符
- 避免界面过长

✅ **压缩后的system消息正常截断**
- 压缩后生成的system角色摘要消息仍然截断
- 只有原始的system prompt不截断

## 相关修复

这是继之前修复之后的又一个相关问题：

1. **第一次修复**：`SYSTEM_PROMPT_PROTECTION.md`
   - 在compressor中分离system prompt
   - 在context_manager中保护system prompt
   - 修复时间：前一次提交

2. **第二次修复**：`SYSTEM_PROMPT_FIX.md`
   - 修复compressor中4处错误使用messages的地方
   - 确保system prompt不参与任何压缩流程
   - 修复时间：本次提交的前一部分

3. **第三次修复（本次）**：`FRONTEND_TRUNCATION_FIX.md`
   - 修复前端显示截断问题
   - System prompt在Web界面完整显示
   - 修复时间：本次提交

## 注意事项

1. **只影响"当前上下文"面板**
   - "实时对话"面板显示完整消息内容（没有截断）
   - "查看完整上下文"对话框显示完整内容（没有截断）
   - 只有"当前上下文"面板的预览受影响

2. **压缩摘要仍然会截断**
   - 压缩后生成的system角色摘要消息（role='system', compressed=true）
   - 这些摘要本身就是精简版，截断是合理的

3. **长内容可能导致滚动**
   - 如果system prompt特别长（如5000+字符），可能需要滚动查看
   - 这比截断后看不到内容更好

## 未来改进建议

如果需要更好的用户体验，可以考虑：

1. **折叠/展开功能**
   - 默认显示前几行，点击"展开"查看全部
   - 适用于所有长消息

2. **悬浮提示**
   - 鼠标悬停显示完整内容
   - 使用Element Plus的el-tooltip组件

3. **模态对话框**
   - 点击消息打开对话框查看完整内容
   - 类似"查看完整上下文"功能

4. **智能截断**
   - 根据内容重要性决定截断长度
   - System prompt优先完整显示

## 更新日志

- **2025-01-XX**: 修复前端System Prompt截断显示问题
  - web/index.html: 区分system prompt和其他消息的显示
  - System prompt完整显示，不截断
  - 添加white-space和word-break CSS以改善显示
  - 测试验证：1682字符的system prompt完整显示
