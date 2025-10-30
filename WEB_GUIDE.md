# 🌐 Web可视化后台使用指南

## 📋 简介

Web可视化后台为上下文工程系统提供了一个直观的Web界面，让你可以：

- ✅ **实时对话**: 与LLM进行实时对话交互
- ✅ **可视化监控**: 实时查看Token使用率和系统状态
- ✅ **压缩过程**: 直观展示上下文压缩的完整过程
- ✅ **统计分析**: 查看详细的统计数据和压缩效果
- ✅ **历史查看**: 浏览和导出完整的对话历史
- ✅ **实时更新**: 通过WebSocket实现实时数据推送

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

依赖包括：
- FastAPI（Web框架）
- Uvicorn（ASGI服务器）
- WebSockets（实时通信）

### 2. 配置系统

在启动Web服务前，需要先配置LLM API：

```bash
# 方式1: 交互式配置（推荐首次使用）
python main.py --interactive

# 方式2: 手动配置
cp .env.example .env
cp config.yaml.example config.yaml
# 编辑 .env 文件填入你的API密钥
```

### 3. 启动Web服务

#### 方式A: 使用启动脚本（推荐）

```bash
./start_web.sh
```

或者在Windows上:
```bash
bash start_web.sh
```

#### 方式B: 直接启动

```bash
python web_server.py
```

### 4. 访问界面

启动后，在浏览器中访问：

- **主页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs （自动生成的交互式API文档）

## 🎨 界面功能

### 1. 实时对话区域

![对话区域](https://via.placeholder.com/800x400?text=Chat+Area)

**功能特点:**
- 💬 发送消息并获得LLM响应
- 📊 显示每条消息的Token数和成本
- 🔄 自动滚动到最新消息
- ⚡ 实时显示发送状态

**使用方法:**
1. 在输入框中输入你的问题
2. 点击"发送"按钮或按Enter键
3. 等待LLM响应（显示加载状态）
4. 查看响应和统计信息

### 2. Token使用率监控

**实时监控:**
- 📈 可视化进度条（绿色/黄色/红色）
- 🔢 当前Token数 / 最大Token数
- ⚠️ 状态提示（正常/警告/严重警告）

**颜色含义:**
- 🟢 **绿色** (0-60%): 正常运行
- 🟡 **黄色** (60-80%): 警告，接近限制
- 🔴 **红色** (80%+): 严重警告，即将触发压缩

**操作按钮:**
- ⚙️ **手动压缩**: 立即触发上下文压缩
- 🔄 **重置对话**: 清空所有历史记录
- 📤 **导出历史**: 保存对话记录到文件

### 3. 统计信息面板

显示四个关键指标：

1. **查询次数**: 用户总共提出的问题数
2. **API调用**: 实际调用LLM API的次数
3. **压缩次数**: 自动或手动压缩的次数
4. **总成本**: 预估的API使用成本

**压缩统计:**
- 节省的Token数
- 平均压缩率

### 4. 当前上下文查看

**功能:**
- 📋 显示当前将发送给LLM的所有消息
- 🏷️ 标记消息类型（压缩/动态注入/知识库）
- 📊 显示每条消息的Token数
- 📈 显示总Token使用率

**标签说明:**
- 🔵 **压缩**: 已被AU2算法压缩的内容
- 🟢 **动态注入**: 根据查询自动注入的历史
- 🔵 **知识库**: 来自长期知识库的内容

### 5. 压缩内容展示

**查看压缩片段:**
- 📝 显示所有压缩后的内容
- ℹ️ 显示压缩元数据（原始消息数、Token数等）
- 📄 展示完整的压缩摘要内容

**压缩片段信息:**
- 压缩状态（已压缩/未压缩）
- 原始消息数量
- 压缩后Token数
- 创建时间

## 🔌 API接口

Web服务提供了完整的REST API，可以通过编程方式访问：

### 基础接口

```bash
# 健康检查
GET /api/health

# 获取配置
GET /api/config

# 获取统计信息
GET /api/stats

# 获取Token使用率
GET /api/usage
```

### 对话接口

```bash
# 发送消息
POST /api/chat
Content-Type: application/json
{
  "message": "你好，我想了解上下文工程",
  "use_mock": false
}

# 获取对话历史
GET /api/history?limit=50

# 获取当前上下文
GET /api/context

# 获取压缩内容
GET /api/compressed
```

### 控制接口

```bash
# 手动触发压缩
POST /api/compress
Content-Type: application/json
{
  "force": true
}

# 重置对话
POST /api/reset

# 导出历史
GET /api/export
```

### WebSocket接口

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'usage_update':
      // 使用率更新
      console.log('Token使用率:', data.data.usage);
      break;

    case 'user_message':
      // 用户消息
      console.log('用户:', data.data.content);
      break;

    case 'assistant_message':
      // 助手响应
      console.log('助手:', data.data.content);
      break;

    case 'compression':
      // 压缩事件
      console.log('压缩完成，节省Token:', data.data.saved_tokens);
      break;
  }
};
```

## 🛠️ 高级功能

### 1. 自动压缩演示

当Token使用率达到92%时，系统会自动触发压缩：

**观察步骤:**
1. 进行多轮对话，观察使用率逐渐上升
2. 注意进度条颜色变化（绿→黄→红）
3. 使用率达到92%时，自动触发压缩
4. 观察压缩结果（节省Token、新使用率）
5. 查看"压缩内容"面板，查看压缩摘要

### 2. 手动压缩测试

**测试流程:**
1. 进行5-10轮对话
2. 点击"手动压缩"按钮
3. 等待压缩完成（显示通知）
4. 查看压缩统计信息
5. 刷新"当前上下文"查看变化

### 3. 实时更新体验

**测试WebSocket:**
1. 打开两个浏览器标签页
2. 在第一个标签页发送消息
3. 观察第二个标签页是否实时更新
4. 所有连接的客户端都会收到实时更新

### 4. 导出功能

**导出对话历史:**
1. 点击"导出历史"按钮
2. 系统自动保存为JSON文件
3. 文件位于 `workspace/exports/` 目录
4. 可以用于后续分析或备份

## 📊 使用场景

### 场景1: 学习上下文工程

**目标:** 理解上下文压缩的原理

**步骤:**
1. 启动Web界面
2. 进行多轮技术讨论（如代码设计）
3. 观察Token使用率的变化
4. 等待自动压缩触发
5. 查看"压缩内容"，分析压缩摘要
6. 对比"当前上下文"的压缩前后差异

### 场景2: 测试压缩效果

**目标:** 评估AU2算法的压缩质量

**步骤:**
1. 进行长对话（15-20轮）
2. 手动触发压缩
3. 查看压缩率和节省Token数
4. 继续提问，测试模型是否保留关键信息
5. 导出历史进行详细分析

### 场景3: 演示系统功能

**目标:** 向他人展示上下文管理

**步骤:**
1. 打开Web界面（大屏幕效果更好）
2. 进行实时对话演示
3. 指出实时Token监控
4. 触发压缩，展示压缩过程
5. 查看统计数据，展示成本节省

## 🔧 配置与自定义

### 修改服务器端口

编辑 `web_server.py` 最后一行：

```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,  # 修改这里
    log_level="info"
)
```

### 调整显示限制

在API路由中修改限制：

```python
@app.get("/api/history")
async def get_history(limit: int = 50):  # 修改默认限制
    ...
```

### 自定义前端样式

编辑 `web/index.html` 中的CSS样式：

```css
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    /* 修改背景渐变色 */
}
```

## ❓ 常见问题

### Q1: 启动失败，提示端口被占用

**A:** 端口8000已被其他程序使用，可以：
1. 关闭占用端口的程序
2. 修改服务器端口（参见上文）

### Q2: WebSocket连接失败

**A:** 检查：
1. 防火墙是否阻止WebSocket连接
2. 浏览器是否支持WebSocket（现代浏览器都支持）
3. 使用 http:// 而非 https://（本地开发）

### Q3: API调用失败

**A:** 确认：
1. LLM API已正确配置（.env文件）
2. API密钥有效且有额度
3. 网络连接正常
4. 查看终端日志获取详细错误

### Q4: 界面显示不正常

**A:** 尝试：
1. 清除浏览器缓存
2. 使用Ctrl+F5强制刷新
3. 检查浏览器控制台是否有错误
4. 确认CDN资源（Vue.js、Element Plus）可访问

### Q5: 如何在生产环境部署？

**A:** 需要考虑：
1. 使用HTTPS（配置SSL证书）
2. 配置Nginx作为反向代理
3. 使用Gunicorn管理进程
4. 设置环境变量保护密钥
5. 配置CORS策略
6. 添加身份认证

**示例Nginx配置:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🎯 性能优化

### 1. 减少轮询

Web界面默认通过WebSocket实时更新，避免频繁轮询。

### 2. 限制历史记录

获取历史时使用limit参数：

```javascript
fetch('/api/history?limit=20')  // 只获取最近20条
```

### 3. 缓存静态资源

浏览器会自动缓存CSS、JS等静态资源。

### 4. 压缩响应

在生产环境中启用Gzip压缩：

```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## 📚 扩展开发

### 添加新的API端点

```python
@app.get("/api/custom")
async def custom_endpoint():
    """自定义端点"""
    return {"message": "Hello World"}
```

### 添加新的前端组件

在 `web/index.html` 中添加Vue组件：

```javascript
const CustomComponent = {
    template: `<div>Custom Component</div>`,
    setup() {
        // 组件逻辑
    }
};
```

### 集成其他可视化库

可以集成ECharts、D3.js等：

```html
<!-- 添加ECharts -->
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
```

## 🤝 贡献与反馈

欢迎贡献代码和提供反馈！

**改进建议:**
- 添加更多图表可视化
- 支持多用户会话
- 添加主题切换功能
- 集成更多LLM提供商

## 📄 许可证

MIT License

---

**🎉 享受可视化的上下文工程体验！**

有问题？查看主README.md或提交Issue。
