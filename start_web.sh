#!/bin/bash

# 上下文工程可视化系统启动脚本

echo "================================"
echo "🌐 上下文工程可视化系统"
echo "================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  缺少依赖，正在安装..."
    pip install -r requirements.txt
fi

echo "✅ 依赖检查完成"
echo ""

# 启动服务器
echo "🚀 启动Web服务器..."
echo ""
echo "访问地址:"
echo "  主页: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""
echo "================================"
echo ""

python3 web_server.py
