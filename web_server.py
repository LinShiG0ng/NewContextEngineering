"""
Web可视化后台服务器

提供REST API和WebSocket接口，支持:
- 实时对话交互
- 压缩过程可视化
- Token使用率监控
- 统计数据展示
- 历史记录查看
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from context_manager import ContextManager
from llm_client import LLMClient, MockLLMClient
from config_loader import load_config
from utils import estimate_cost


# ============================================================================
# 数据模型
# ============================================================================

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    use_mock: bool = False


class CompressRequest(BaseModel):
    """压缩请求"""
    force: bool = True


class ConfigRequest(BaseModel):
    """配置更新请求"""
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: Optional[int] = None


# ============================================================================
# WebSocket连接管理
# ============================================================================

class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受连接"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


# ============================================================================
# 应用实例
# ============================================================================

app = FastAPI(
    title="上下文工程可视化系统",
    description="实时监控和可视化上下文压缩过程",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
manager_instance: Optional[ContextManager] = None
client_instance: Optional[LLMClient] = None
config_instance: dict = {}
ws_manager = ConnectionManager()

# 会话统计
session_stats = {
    "queries": 0,
    "api_calls": 0,
    "total_cost": 0.0,
    "start_time": datetime.now().isoformat()
}


# ============================================================================
# 初始化函数
# ============================================================================

def init_system(use_mock: bool = False):
    """初始化系统"""
    global manager_instance, client_instance, config_instance

    try:
        # 加载配置
        config_instance = load_config(interactive=False)

        # 初始化上下文管理器
        manager_instance = ContextManager(
            max_tokens=config_instance.get("max_tokens", 8000)
        )

        # 初始化LLM客户端
        if use_mock:
            client_instance = MockLLMClient(config_instance)
        else:
            client_instance = LLMClient(config_instance)

        print("✅ 系统初始化成功")
        return True

    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return False


# ============================================================================
# API路由
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    init_system(use_mock=False)


@app.get("/")
async def root():
    """首页"""
    return FileResponse(Path(__file__).parent / "web" / "index.html")


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "initialized": manager_instance is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/config")
async def get_config():
    """获取当前配置"""
    if not client_instance:
        raise HTTPException(status_code=500, detail="系统未初始化")

    model_info = client_instance.get_model_info()

    return {
        "provider": config_instance.get("provider", "unknown"),
        "model": config_instance.get("model", "unknown"),
        "max_tokens": config_instance.get("max_tokens", 8000),
        "temperature": config_instance.get("temperature", 0.7),
        "warning_threshold": config_instance.get("warning_threshold", 0.6),
        "error_threshold": config_instance.get("error_threshold", 0.8),
        "auto_compact_threshold": config_instance.get("auto_compact_threshold", 0.92),
        "model_info": model_info
    }


@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    if not manager_instance:
        raise HTTPException(status_code=500, detail="系统未初始化")

    stats = manager_instance.get_statistics()

    # 添加会话统计
    stats["session"] = session_stats

    return stats


@app.get("/api/usage")
async def get_usage():
    """获取Token使用率"""
    if not manager_instance:
        raise HTTPException(status_code=500, detail="系统未初始化")

    status = manager_instance.get_usage_status()

    return {
        "current_tokens": status["current_tokens"],
        "max_tokens": status["max_tokens"],
        "usage": status["usage"],
        "status": status["status"],
        "message": status["message"]
    }


@app.get("/api/history")
async def get_history(limit: int = 50):
    """获取对话历史"""
    if not manager_instance:
        raise HTTPException(status_code=500, detail="系统未初始化")

    all_messages = manager_instance.storage.get_all_messages()

    # 限制返回数量
    messages = all_messages[-limit:] if len(all_messages) > limit else all_messages

    # 格式化消息
    formatted = []
    for msg in messages:
        formatted.append({
            "role": msg.get("role", "unknown"),
            "content": msg.get("content", ""),
            "tokens": msg.get("tokens", 0),
            "compressed": msg.get("compressed", False),
            "timestamp": msg.get("timestamp", 0)
        })

    return {
        "total": len(all_messages),
        "returned": len(formatted),
        "messages": formatted
    }


@app.get("/api/context")
async def get_context():
    """获取当前上下文"""
    if not manager_instance or not client_instance:
        raise HTTPException(status_code=500, detail="系统未初始化")

    context = await manager_instance.get_context(current_query=None)

    # 计算token数
    total_tokens = client_instance.count_messages_tokens(context)
    usage_percent = (total_tokens / manager_instance.max_tokens) * 100

    formatted = []
    for msg in context:
        formatted.append({
            "role": msg.get("role", "unknown"),
            "content": msg.get("content", ""),
            "tokens": msg.get("tokens", 0),
            "compressed": msg.get("compressed", False),
            "injected": msg.get("injected", False),
            "from_knowledge_base": msg.get("from_knowledge_base", False)
        })

    return {
        "messages": formatted,
        "total_tokens": total_tokens,
        "max_tokens": manager_instance.max_tokens,
        "usage_percent": usage_percent
    }


@app.get("/api/compressed")
async def get_compressed():
    """获取压缩内容"""
    if not manager_instance:
        raise HTTPException(status_code=500, detail="系统未初始化")

    mid_term = manager_instance.storage.get_mid_term()

    formatted = []
    for msg in mid_term:
        formatted.append({
            "content": msg.get("content", ""),
            "tokens": msg.get("tokens", 0),
            "compressed": msg.get("compressed", False),
            "original_count": msg.get("original_count", 0),
            "timestamp": msg.get("timestamp", 0)
        })

    return {
        "count": len(formatted),
        "segments": formatted
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """发送聊天消息"""
    if not manager_instance or not client_instance:
        raise HTTPException(status_code=500, detail="系统未初始化")

    try:
        # 更新统计
        session_stats["queries"] += 1

        # 添加用户消息
        await manager_instance.add_message("user", request.message)

        # 广播用户消息
        await ws_manager.broadcast({
            "type": "user_message",
            "data": {
                "role": "user",
                "content": request.message,
                "timestamp": datetime.now().isoformat()
            }
        })

        # 构建上下文
        context = await manager_instance.get_context(current_query=request.message)

        # 广播使用率更新
        usage_status = manager_instance.get_usage_status()
        await ws_manager.broadcast({
            "type": "usage_update",
            "data": usage_status
        })

        # 调用LLM
        input_tokens = client_instance.count_messages_tokens(context)

        # 广播API调用开始
        await ws_manager.broadcast({
            "type": "api_call_start",
            "data": {
                "input_tokens": input_tokens,
                "message_count": len(context)
            }
        })

        response = await client_instance.chat_with_retry(
            messages=context,
            stream=False
        )

        # 计算成本
        output_tokens = client_instance.count_tokens(response)
        cost = (
            estimate_cost(input_tokens, "input", client_instance.model) +
            estimate_cost(output_tokens, "output", client_instance.model)
        )

        session_stats["api_calls"] += 1
        session_stats["total_cost"] += cost

        # 添加助手响应
        await manager_instance.add_message("assistant", response)

        # 广播助手响应
        await ws_manager.broadcast({
            "type": "assistant_message",
            "data": {
                "role": "assistant",
                "content": response,
                "tokens": output_tokens,
                "cost": cost,
                "timestamp": datetime.now().isoformat()
            }
        })

        # 检查是否需要压缩
        compression_result = await manager_instance.compress_if_needed(force=False)

        if compression_result.get("compressed"):
            # 广播压缩事件
            await ws_manager.broadcast({
                "type": "compression",
                "data": compression_result
            })

        return {
            "success": True,
            "response": response,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "compressed": compression_result.get("compressed", False)
        }

    except Exception as e:
        await ws_manager.broadcast({
            "type": "error",
            "data": {
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compress")
async def compress(request: CompressRequest):
    """手动触发压缩"""
    if not manager_instance:
        raise HTTPException(status_code=500, detail="系统未初始化")

    try:
        # 广播压缩开始
        await ws_manager.broadcast({
            "type": "compression_start",
            "data": {
                "manual": True,
                "timestamp": datetime.now().isoformat()
            }
        })

        result = await manager_instance.compress_if_needed(force=request.force)

        # 广播压缩结果
        await ws_manager.broadcast({
            "type": "compression",
            "data": result
        })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
async def reset():
    """重置对话"""
    global session_stats

    if not manager_instance:
        raise HTTPException(status_code=500, detail="系统未初始化")

    try:
        manager_instance.reset()

        # 重置统计
        session_stats = {
            "queries": 0,
            "api_calls": 0,
            "total_cost": 0.0,
            "start_time": datetime.now().isoformat()
        }

        # 广播重置事件
        await ws_manager.broadcast({
            "type": "reset",
            "data": {
                "timestamp": datetime.now().isoformat()
            }
        })

        return {
            "success": True,
            "message": "对话已重置"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export")
async def export_history():
    """导出对话历史"""
    if not manager_instance:
        raise HTTPException(status_code=500, detail="系统未初始化")

    try:
        output_path = manager_instance.export_history()

        if output_path:
            return {
                "success": True,
                "path": output_path,
                "message": "历史已导出"
            }
        else:
            return {
                "success": False,
                "message": "导出失败"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket路由
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接处理"""
    await ws_manager.connect(websocket)

    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "data": {
                "message": "WebSocket连接已建立",
                "timestamp": datetime.now().isoformat()
            }
        })

        # 发送初始状态
        if manager_instance:
            usage_status = manager_instance.get_usage_status()
            await websocket.send_json({
                "type": "usage_update",
                "data": usage_status
            })

        # 保持连接
        while True:
            data = await websocket.receive_text()
            # 可以在这里处理客户端发来的消息

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket错误: {e}")
        ws_manager.disconnect(websocket)


# ============================================================================
# 静态文件服务
# ============================================================================

# 挂载静态文件目录（如果存在）
web_dir = Path(__file__).parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("🌐 上下文工程可视化系统")
    print("=" * 60)
    print("\n启动Web服务器...")
    print("\n访问地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止服务器\n")
    print("=" * 60 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
