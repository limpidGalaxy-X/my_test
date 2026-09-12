r"""
03_进阶 / 03 - 传输与 ASGI 挂载

MCP Server 有三种跑法，再加上"塞进你自己的 Web 应用"：

  1) stdio                 mcp.run()                              ← 本机 Host
  2) Streamable HTTP       mcp.run(transport="streamable-http")   ← 独立服务
  3) 挂进已有 ASGI 应用     app = mcp.streamable_http_app()        ← FastAPI/Starlette 里加个路由

⚠️ 三个必须记住的坑：

  a) 传输参数**不在构造函数里**
       MCPServer("x", port=9000)                      ❌ TypeError
       mcp.run(transport="streamable-http", port=...   ✅

  b) 没有 mcp.http_app() 这个方法！正确的是 mcp.streamable_http_app() / mcp.sse_app()

  c) 把子应用 Mount 到宿主上时，**宿主的 lifespan 会覆盖子应用的 lifespan**，
     必须自己在宿主 lifespan 里 `async with mcp.session_manager.run():`，
     否则第一个请求就报 RuntimeError: Task group is not initialized。

运行：
    .\.venv\Scripts\python.exe "03_传输与ASGI挂载.py"                # 只打印说明 + 构建 app（不联网）
    .\.venv\Scripts\python.exe "03_传输与ASGI挂载.py" --serve         # stdio
    .\.venv\Scripts\python.exe "03_传输与ASGI挂载.py" --http          # Streamable HTTP :8000
    .\.venv\Scripts\python.exe "03_传输与ASGI挂载.py" --asgi          # 挂进 Starlette :8100
"""

from __future__ import annotations

import sys

from mcp.server import MCPServer

# ---------------------------------------------------------------------------
# 业务代码和传输完全无关 —— 这是 MCP 设计得好的地方
# ---------------------------------------------------------------------------
mcp = MCPServer(
    "TransportDemo",
    instructions="演示 stdio / Streamable HTTP / ASGI 挂载三种传输。",
)


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@mcp.resource("info://transport")
def transport_info() -> str:
    """Describe the transports this server supports."""
    return "stdio | streamable-http | asgi-mount"


# ---------------------------------------------------------------------------
# custom_route：在 MCP 端点上挂自己的普通 HTTP 端点（比如健康检查）
# ⚠️ 规范提醒：custom_route 注册的端点**永远不会走 MCP 的鉴权层**，
#    所以不要在这里暴露敏感数据。
# ---------------------------------------------------------------------------
@mcp.custom_route("/health", methods=["GET"])
async def health(request):  # type: ignore[no-untyped-def]
    from starlette.responses import JSONResponse

    return JSONResponse({"status": "ok", "server": "TransportDemo"})


# ---------------------------------------------------------------------------
# 构建 ASGI 应用（FastAPI / Starlette 都能挂）
# ---------------------------------------------------------------------------
def build_asgi_app():
    from contextlib import asynccontextmanager
    from collections.abc import AsyncIterator

    from starlette.applications import Starlette
    from starlette.routing import Mount

    mcp_app = mcp.streamable_http_app()      # 一个 Starlette 实例，路由在 /mcp

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        # ★ 关键：宿主要替子应用启动 session manager，否则请求会 500
        async with mcp.session_manager.run():
            yield

    app = Starlette(
        routes=[
            Mount("/mcp-server", app=mcp_app),   # 挂到 /mcp-server 前缀下
        ],
        lifespan=lifespan,
    )
    return app


def explain() -> None:
    print("=" * 74)
    print("三种传输对照")
    print("=" * 74)
    rows = [
        ("stdio", "mcp.run()", "本机 Host 拉子进程", "无", "无"),
        ("streamable-http", 'mcp.run(transport="streamable-http")', "独立服务/远程", "/mcp", "Bearer"),
        ("asgi", "mcp.streamable_http_app()", "塞进已有 Web 应用", "/mcp", "自己加中间件"),
    ]
    print(f"  {'传输':<18}{'启动方式':<45}{'端点':<8}{'认证'}")
    for name, how, _use, path, auth in rows:
        print(f"  {name:<18}{how:<45}{path:<8}{auth}")

    print()
    print("=" * 74)
    print("关键 API 速查")
    print("=" * 74)
    print("  mcp.run()                                        stdio（默认）")
    print("  mcp.run(transport='streamable-http', port=8000)  Streamable HTTP")
    print("  mcp.streamable_http_app()                        返回 Starlette 应用")
    print("  mcp.sse_app()                                    旧的 SSE 应用（已过时）")
    print("  mcp.session_manager.run()                        挂载时必须手动启动")
    print("  mcp.custom_route(path, methods=[...])            自定义普通 HTTP 端点")
    print()
    print("  安全相关（真实域名部署必须配，否则全 421）：")
    print("    from mcp.server.transport_security import TransportSecuritySettings")
    print("    MCPServer(..., transport_security=TransportSecuritySettings(")
    print("        allowed_hosts=['example.com'], allowed_origins=['https://example.com']))")
    print()
    print("  自己测 HTTP 端点：")
    print('    curl.exe -s http://127.0.0.1:8000/mcp -H "Content-Type: application/json" \\')
    print('      -H "Accept: application/json, text/event-stream" \\')
    print('      -H "MCP-Protocol-Version: 2026-07-28" \\')
    print("      -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\",\"params\":{}}'")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        mcp.run()
    elif "--http" in sys.argv:
        print("Streamable HTTP 启动在 http://127.0.0.1:8000/mcp", file=sys.stderr)
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)
    elif "--asgi" in sys.argv:
        import uvicorn

        app = build_asgi_app()
        print("ASGI 应用启动在 http://127.0.0.1:8100/mcp-server/mcp", file=sys.stderr)
        # custom_route 注册在 MCP 子应用上，所以会带上挂载前缀
        print("健康检查：http://127.0.0.1:8100/mcp-server/health", file=sys.stderr)
        uvicorn.run(app, host="127.0.0.1", port=8100, log_level="warning")
    else:
        explain()
        print()
        print("=" * 74)
        print("构建 ASGI 应用（不启动，只验证代码能跑通）")
        print("=" * 74)
        app = build_asgi_app()
        print(f"  app = {app!r}")
        print(f"  路由 = {[getattr(r, 'path', r) for r in app.routes]}")
        print("  真实启动：python \"03_传输与ASGI挂载.py\" --asgi")
