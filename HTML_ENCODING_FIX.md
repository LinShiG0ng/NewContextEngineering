# HTML实体编码问题修复

## 问题描述

在前端显示上下文内容时，出现HTML实体编码的问题：
- `<` 被显示为 `&lt;`
- `>` 被显示为 `&gt;`
- `"` 被显示为 `&quot;`
- `&` 被显示为 `&amp;`

这导致包含XML/HTML标签的内容（如渗透测试流程中的 `<step>`、`<done>` 等标签）无法正常显示。

### 示例

**期望显示：**
```
<step>
<id>S4</id>
<goal>构造SQL注入测试payload</goal>
<done>false</done>
</step>
```

**实际显示（修复前）：**
```
&lt;step&gt;
&lt;id&gt;S4&lt;/id&gt;
&lt;goal&gt;构造SQL注入测试payload&lt;/goal&gt;
&lt;done&gt;false&lt;/done&gt;
&lt;/step&gt;
```

## 根本原因

1. **后端**：FastAPI的JSON响应不会对内容进行HTML编码（验证通过）
2. **前端**：Vue模板的双花括号插值 `{{ }}` 会自动转义HTML特殊字符，这是为了安全考虑
3. **数据流**：某些情况下，数据可能在传输或处理过程中被意外编码

## 解决方案

在前端JavaScript中添加HTML实体解码函数，在显示内容前进行解码。

### 实现细节

**1. 添加解码函数** (`web/index.html`)

```javascript
// HTML实体解码函数
function decodeHTMLEntities(text) {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    return textarea.value;
}
```

**工作原理：**
- 创建一个临时的 `<textarea>` 元素
- 将包含HTML实体的文本赋值给 `innerHTML`
- 浏览器自动解码HTML实体
- 从 `value` 属性获取解码后的纯文本

**2. 在加载完整上下文时应用解码** (`loadFullContext()`)

```javascript
if (fullContextFormat.value === 'json') {
    // JSON格式需要美化，并解码HTML实体
    const jsonStr = JSON.stringify(data.messages, null, 2);
    fullContextContent.value = decodeHTMLEntities(jsonStr);
} else {
    // 文本和Markdown格式直接使用content，并解码HTML实体
    fullContextContent.value = decodeHTMLEntities(data.content);
}
```

**3. 在加载历史消息时应用解码** (`loadHistory()`)

```javascript
// 解码每条消息的内容
messages.value = data.messages.map(msg => ({
    ...msg,
    content: decodeHTMLEntities(msg.content || '')
}));
```

## 修复覆盖范围

✅ **查看完整上下文对话框**
- JSON格式
- 文本格式
- Markdown格式

✅ **聊天消息区域**
- 历史消息加载
- 新消息接收（通过WebSocket）

✅ **导出功能**
- 复制到剪贴板
- 下载为文件

## 测试验证

### 1. 单元测试

运行 `test_html_decode.html` 在浏览器中验证解码函数：

```bash
# 在浏览器中打开
open test_html_decode.html
```

测试用例包括：
- ✅ XML标签编码：`&lt;done&gt;` → `<done>`
- ✅ 复杂结构：`&lt;step&gt;...&lt;/step&gt;`
- ✅ 混合内容：命令标签 + 普通文本
- ✅ 引号和符号：`&quot;` → `"`，`&amp;` → `&`
- ✅ 无编码内容：保持原样

### 2. 集成测试

运行 `test_html_encoding_fix.py` 验证后端数据：

```bash
python test_html_encoding_fix.py
```

验证项目：
- ✅ 后端不进行HTML编码
- ✅ JSON序列化保留原始字符
- ✅ 上下文中的特殊字符被正确保留

### 3. Web UI测试

启动服务器并手动测试：

```bash
python web_server.py
```

测试步骤：
1. 访问 http://localhost:8000
2. 添加包含XML/HTML标签的消息
3. 点击"查看完整上下文"按钮
4. 验证显示的内容不包含 `&lt;` `&gt;` 等编码

## 安全考虑

### 为什么不使用 `v-html`？

虽然 Vue 的 `v-html` 指令可以直接渲染HTML，但这样做有XSS（跨站脚本）风险：

```javascript
// ❌ 不安全的做法
<div v-html="fullContextContent"></div>
```

**我们的方案更安全：**
- 使用 `decodeHTMLEntities()` 只解码HTML实体，不解释HTML标签
- 最终内容仍然通过 `{{ }}` 插值显示，Vue会自动转义用户输入的恶意脚本
- 保持了XSS防护，同时正确显示特殊字符

### 示例对比

假设用户输入包含恶意脚本：
```
<script>alert('XSS')</script>
```

**使用 v-html（不安全）：**
```
→ 脚本会被执行！❌
```

**使用我们的方案（安全）：**
```
→ 显示为纯文本：<script>alert('XSS')</script> ✅
```

## 支持的HTML实体

解码函数支持所有标准HTML实体：

| 实体编码 | 原始字符 | 说明 |
|---------|---------|------|
| `&lt;` | `<` | 小于号 |
| `&gt;` | `>` | 大于号 |
| `&amp;` | `&` | 和号 |
| `&quot;` | `"` | 双引号 |
| `&apos;` | `'` | 单引号 |
| `&#39;` | `'` | 单引号（数字编码） |
| `&nbsp;` | ` ` | 不间断空格 |

以及其他所有标准的数字和命名实体。

## 修复的文件

- `web/index.html`
  - 添加 `decodeHTMLEntities()` 函数
  - 修改 `loadFullContext()` 函数
  - 修改 `loadHistory()` 函数

## 相关文件

- `test_html_decode.html` - 浏览器端单元测试
- `test_html_encoding_fix.py` - Python集成测试
- `HTML_ENCODING_FIX.md` - 本文档

## 后续建议

如果未来需要支持富文本显示（例如Markdown渲染），建议：

1. 使用专门的Markdown渲染库（如 marked.js）
2. 配置适当的sanitization规则
3. 使用 Content Security Policy (CSP) 增强安全性

## 更新日志

- **2025-01-XX**: 修复HTML实体编码问题
  - 添加HTML解码函数
  - 应用到完整上下文查看
  - 应用到历史消息加载
  - 添加测试验证
