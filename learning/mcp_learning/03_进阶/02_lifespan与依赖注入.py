r"""
03_进阶 / 02 - lifespan：跨请求共享"重资源"

问题：数据库连接池、HTTP 客户端、模型客户端……这些不能每次调用工具都新建一遍，
      但也不能在模块顶层创建（那时还没有事件循环，而且是 import 副作用）。

答案：lifespan —— 一个异步上下文管理器，服务器启动时执行 `yield` 之前的代码，
      关闭时执行 `yield` 之后的代码（finally）。yield 出来的对象会挂到
      `ctx.request_context.lifespan_context` 上，供所有 handler 使用。

    @asynccontextmanager
    async def app_lifespan(server: MCPServer) -> AsyncIterator[AppContext]:
        db = Database(); await db.connect()      # 启动：只做一次
        try:
            yield AppContext(db=db)              # 交给所有请求用
        finally:
            await db.disconnect()                # 关闭：只做一次

    mcp = MCPServer("X", lifespan=app_lifespan)

⚠️ 没有传 lifespan 时，`ctx.request_context.lifespan_context` 是**空 dict `{}`**，
   不是 None。所以老代码写 `lifespan_context["db"]` 不会 AttributeError，
   而是 KeyError —— 这个区别能帮你判断"到底有没有配 lifespan"。

运行：
    .\.venv\Scripts\python.exe "02_lifespan与依赖注入.py"
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context


# ---------------------------------------------------------------------------
# 1. 假装这是一个真实资源
# ---------------------------------------------------------------------------
class FakeDatabase:
    """一个需要 connect / disconnect 的"昂贵"对象。"""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.connected = False
        self.events: list[str] = []

    async def connect(self) -> None:
        await asyncio.sleep(0.01)                # 模拟耗时的握手
        self.connected = True
        self.events.append("connect")

    async def disconnect(self) -> None:
        self.connected = False
        self.events.append("disconnect")

    def query(self, sql: str) -> list[dict[str, Any]]:
        if not self.connected:
            raise RuntimeError("数据库未连接！")
        self.events.append(f"query:{sql}")
        return [{"id": i, "name": f"row-{i}"} for i in range(1, 4)]


# ---------------------------------------------------------------------------
# 2. 定义 lifespan 与"应用上下文"对象
# ---------------------------------------------------------------------------
@dataclass
class AppContext:
    """lifespan 交给每个请求的东西。"""

    db: FakeDatabase
    stats: dict[str, int] = field(default_factory=lambda: {"calls": 0})


@asynccontextmanager
async def app_lifespan(server: MCPServer) -> AsyncIterator[AppContext]:
    db = FakeDatabase("postgres://demo")
    await db.connect()
    print("  [lifespan] 服务器启动：数据库已连接", file=sys.stderr)
    try:
        yield AppContext(db=db)
    finally:
        await db.disconnect()
        print(f"  [lifespan] 服务器关闭：数据库已断开（事件：{db.events}）", file=sys.stderr)


# ---------------------------------------------------------------------------
# 3. 把 lifespan 交给服务器
# ---------------------------------------------------------------------------
mcp = MCPServer(
    "LifespanDemo",
    instructions="演示如何用 lifespan 共享数据库连接。",
    lifespan=app_lifespan,
)


# ---------------------------------------------------------------------------
# 4. 在 handler 里取用它
#    工具里可以写 Context[AppContext]，这样类型检查器也知道 lifespan_context 是什么
# ---------------------------------------------------------------------------
@mcp.tool()
def list_rows(ctx: Context[AppContext], limit: int = 3) -> dict[str, Any]:
    """Query rows using the shared database connection."""
    app = ctx.request_context.lifespan_context
    app.stats["calls"] += 1
    rows = app.db.query("select * from demo")[:limit]
    return {"rows": rows, "connected": app.db.connected, "calls": app.stats["calls"]}


@mcp.tool()
async def connection_info(ctx: Context[AppContext]) -> str:
    """Show the state of the shared connection."""
    app = ctx.request_context.lifespan_context
    return (
        f"dsn={app.db.dsn} connected={app.db.connected} "
        f"events={app.db.events} 本连接已处理 {app.stats['calls']} 次调用"
    )


# ---------------------------------------------------------------------------
# 5. 对比：没有 lifespan 的服务器
# ---------------------------------------------------------------------------
bare_server = MCPServer("NoLifespan")


@bare_server.tool()
def check_lifespan_context(ctx: Context) -> str:
    """Show what lifespan_context looks like without a lifespan."""
    value = ctx.request_context.lifespan_context
    return f"type={type(value).__name__} value={value!r}"


# ---------------------------------------------------------------------------
# 6. 手动把 ctx 传给 helper 函数
#    Context 只在**被注册的**函数上自动注入，普通函数必须手动传
# ---------------------------------------------------------------------------
def _format_rows(app: AppContext, rows: list[dict[str, Any]]) -> str:
    return f"db={'up' if app.db.connected else 'down'} " + ", ".join(
        f"{r['id']}:{r['name']}" for r in rows
    )


@mcp.tool()
def rows_as_text(ctx: Context[AppContext]) -> str:
    """Format rows using a helper that receives ctx manually."""
    app = ctx.request_context.lifespan_context
    return _format_rows(app, app.db.query("select * from demo"))


# ---------------------------------------------------------------------------
# 自测
# ---------------------------------------------------------------------------
async def demo() -> None:
    from mcp import Client

    print("=" * 74)
    print("1) 带 lifespan 的服务器")
    print("=" * 74)
    async with Client(mcp) as client:
        r = await client.call_tool("list_rows", {"limit": 2})
        print(f"  list_rows      -> {r.structured_content}")

        r = await client.call_tool("connection_info", {})
        print(f"  connection_info-> {r.content[0].text}")

        r = await client.call_tool("list_rows", {"limit": 3})
        print(f"  再调一次 list_rows -> calls={r.structured_content['calls']}  "
              f"（同一个 db 实例，状态是累积的）")

        r = await client.call_tool("rows_as_text", {})
        print(f"  rows_as_text   -> {r.content[0].text}")

    print("  ↑ 退出 async with 时会触发 lifespan 的 finally，看到 stderr 里的 disconnect")

    print()
    print("=" * 74)
    print("2) 没配 lifespan 的服务器")
    print("=" * 74)
    async with Client(bare_server) as client:
        r = await client.call_tool("check_lifespan_context", {})
        print(f"  {r.content[0].text}")
        print("  结论：没有 lifespan 时它是空 dict，不是 None。")

    print()
    print("=" * 74)
    print("3) 用内存 Client 重复连接两次，lifespan 会跑几次？")
    print("=" * 74)
    for i in (1, 2):
        async with Client(mcp) as client:
            await client.call_tool("list_rows", {"limit": 1})
        print(f"  第 {i} 次连接结束（上面应该各出现一次启动/关闭日志）")
    print()
    print("  结论：**每次连接**都会跑一遍 lifespan ——")
    print("        所以 db.events 每次都是全新的；跨连接不共享状态。")
    print("        想跨连接共享，得把资源放在 lifespan 外面（模块级/类属性）。")


if __name__ == "__main__":
    asyncio.run(demo())
