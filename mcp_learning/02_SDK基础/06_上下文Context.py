r"""
06 - 上下文（Context）：处理器内部能做什么

在 handler 里加一个**类型注解为 Context** 的参数，SDK 就会自动注入它。
参数名叫什么都不重要（`ctx` / `context` / `c` 都行），关键是**注解**。

Context 提供的能力（下列签名均由 `inspect.signature` 实测得到）：
    ctx.request_id            本次请求的 id
    ctx.protocol_version      协商到的协议版本
    ctx.client_capabilities   客户端声明支持哪些能力
    ctx.headers               HTTP 传输时的请求头（stdio 下是 None）
    await ctx.report_progress(progress: float, total: float|None = None, message: str|None = None)
    contents = await ctx.read_resource(uri) -> list[ReadResourceContents]（每个有 .content/.mime_type）
    result = await ctx.elicit(message: str, schema: type[BaseModel]) -> 三种结果之一
    await ctx.notify_tools_changed()      通知"工具列表变了"

⚠ 重要：
  * Context 只在**被注册的**函数上生效，普通 helper 函数拿不到，必须手动传参
  * **静态 resource 和 prompt 只能写裸 Context，不能写 Context[X]**，否则运行时报错
  * ctx.info() / ctx.debug() / ctx.warning() 在 2026-07-28 起**已废弃**，
    请改用标准库 logging（日志走 stderr）
  * Context 参数不会出现在 inputSchema 里，模型也看不到它

运行：
    .\.venv\Scripts\python.exe "06_上下文Context.py"
    .\.venv\Scripts\python.exe "06_上下文Context.py" --serve
"""

from __future__ import annotations

import asyncio
import logging
import sys

from pydantic import BaseModel, Field

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.types import ElicitResult

logger = logging.getLogger(__name__)

mcp = MCPServer("ContextShowcase", instructions="演示 Context 的各种能力。")


# ---------------------------------------------------------------------------
# 1. 注入 Context：只是加一个带注解的参数
#    （Context 建议放第一个参数，免得和带默认值的参数顺序冲突）
# ---------------------------------------------------------------------------
@mcp.tool()
async def who_am_i(ctx: Context) -> str:
    """Tells you what the server knows about this request."""
    return (
        f"request_id={ctx.request_id}\n"
        f"protocol_version={ctx.protocol_version}\n"
        f"headers={ctx.headers}\n"
        f"client_capabilities={ctx.client_capabilities}"
    )


# ---------------------------------------------------------------------------
# 2. 上报进度：长任务必备。客户端要传 progress_callback 才收得到。
# ---------------------------------------------------------------------------
@mcp.tool()
async def countdown(ctx: Context, n: int = 5) -> str:
    """Count down from n, reporting progress along the way."""
    for i in range(n, 0, -1):
        await ctx.report_progress(n - i + 1, total=n, message=f"还剩 {i}")
        await asyncio.sleep(0.05)
    return f"倒计时结束（共 {n} 步）"


# ---------------------------------------------------------------------------
# 3. 用标准库 logging 写日志（官方推荐做法）
#    stdio 传输下日志必须走 stderr —— 用 print 会污染协议流，直接崩掉连接！
# ---------------------------------------------------------------------------
@mcp.tool()
def compute(ctx: Context, x: int) -> int:
    """Compute something and log what happened."""
    logger.info("compute 被调用 x=%s request_id=%s", x, ctx.request_id)
    result = x * 2
    logger.debug("compute 结果 %s", result)
    return result


# ---------------------------------------------------------------------------
# 4. 在 handler 里读取本服务器自己的资源（避免重复实现取数逻辑）
# ---------------------------------------------------------------------------
@mcp.resource("settings://app", mime_type="text/plain")
def settings() -> str:
    """Application settings."""
    return "threshold=10\nmode=strict"


@mcp.tool()
async def check_threshold(ctx: Context, value: int) -> str:
    """Read the settings resource from inside a tool handler."""
    contents = await ctx.read_resource("settings://app")
    first = contents[0]
    threshold = 10
    for line in first.content.splitlines():
        if line.startswith("threshold="):
            threshold = int(line.split("=", 1)[1])
    return f"value={value} threshold={threshold} mime={first.mime_type} " \
           f"-> {'通过' if value >= threshold else '不通过'}"


# ---------------------------------------------------------------------------
# 5. 向用户追问（Elicitation）
#    * schema 参数是**一个 pydantic 模型类**，不是 dict
#    * 返回三种之一：AcceptedElicitation(.data) / DeclinedElicitation / CancelledElicitation
#    * 客户端必须提供 elicitation_callback，否则会收到协议错误
#    * ⚠ 内存连接（Client(mcp)）**不支持**服务端反向请求，实测会报
#      NoBackChannelError: this transport context has no back-channel for
#      server-initiated requests.  —— 要用 stdio 或 Streamable HTTP 才能跑通
#    * 规范红线：MUST NOT 用 elicitation 索取敏感信息
# ---------------------------------------------------------------------------
class FlightDate(BaseModel):
    """追问表单的字段定义。"""

    date: str = Field(description="出发日期", json_schema_extra={"format": "date"})


@mcp.tool()
async def book_flight(ctx: Context, city: str) -> str:
    """Ask the user for the missing information before proceeding."""
    result = await ctx.elicit(f"你想订去 {city} 的哪一天的机票？", FlightDate)

    if result.action == "accept":
        return f"已按 {result.data.date} 为你准备去 {city} 的行程"
    if result.action == "decline":
        return "用户拒绝了这次询问"
    return "用户取消了这次询问"


# ---------------------------------------------------------------------------
# 6. 主动通知客户端"我的工具列表变了"
# ---------------------------------------------------------------------------
_extra_tools: list[str] = []


@mcp.tool()
async def add_dynamic_tool(ctx: Context, name: str) -> str:
    """Dynamically register a new tool, then notify the client."""
    text = (name or "dynamic").strip()

    def generated(x: int) -> str:
        return f"{text} 收到了 {x}"

    mcp.add_tool(generated, name=f"dyn_{text}", description=f"由 add_dynamic_tool 创建：{text}")
    _extra_tools.append(f"dyn_{text}")

    await ctx.notify_tools_changed()          # 让客户端重新拉 tools/list
    return f"已注册工具 dyn_{text}，当前动态工具：{_extra_tools}"


# ---------------------------------------------------------------------------
# 自测
# ---------------------------------------------------------------------------
async def demo() -> None:
    from mcp import Client

    # 注意：进度回调必须是 async def！实测传同步函数时，
    # 第一次通知能收到，之后会报 "TypeError: 'NoneType' object can't be awaited"。
    async def progress_printer(progress: float, total: float | None, message: str | None) -> None:
        print(f"    [progress] {progress}/{total} {message or ''}")

    async def elicitation_handler(context: object, params: object) -> ElicitResult:
        """假装用户填了 2026-10-01 并点了确认。

        真实回调签名：(context: ClientRequestContext, params: ElicitRequestParams)
        """
        print(f"    [elicitation] 服务器问：{getattr(params, 'message', params)}")
        print(f"    [elicitation] 表单字段：{getattr(params, 'requested_schema', None)}")
        return ElicitResult(action="accept", content={"date": "2026-10-01"})

    async with Client(mcp, elicitation_callback=elicitation_handler) as client:
        print("=" * 72)
        print("1) Context 里能看到什么")
        print("=" * 72)
        r = await client.call_tool("who_am_i", {})
        print("  " + r.content[0].text.replace("\n", "\n  "))

        print()
        print("=" * 72)
        print("2) 进度上报（需要 progress_callback）")
        print("=" * 72)
        r = await client.call_tool("countdown", {"n": 3}, progress_callback=progress_printer)
        print(f"  最终结果: {r.content[0].text}")

        print()
        print("=" * 72)
        print("3) 在 handler 里用 logging（日志走 stderr，不污染协议流）")
        print("=" * 72)
        r = await client.call_tool("compute", {"x": 21})
        print(f"  compute(x=21) = {r.structured_content}   （上面那行 INFO 来自 logger）")

        print()
        print("=" * 72)
        print("4) 在 handler 里读自己的资源")
        print("=" * 72)
        r = await client.call_tool("check_threshold", {"value": 12})
        print("  " + r.content[0].text)

        print()
        print("=" * 72)
        print("5) 向用户追问（Elicitation）")
        print("=" * 72)
        print("  内存连接不支持服务端反向请求，所以这里会失败 —— 这正是要教你的点：")
        try:
            r = await client.call_tool("book_flight", {"city": "上海"})
            print("  " + r.content[0].text)
        except Exception as exc:  # noqa: BLE001
            print(f"  {type(exc).__name__}: {str(exc)[:110]}")
            print("  （真实的 NoBackChannelError 被包在 ExceptionGroup 里）")
            print("  结论：elicitation / roots / sampling 这类**服务端反向请求**")
            print("        在 Client(mcp) 内存连接下不可用，必须用 stdio 或 HTTP 传输。")

        print()
        print("=" * 72)
        print("6) 运行时注册工具 + 通知客户端刷新")
        print("=" * 72)
        r = await client.call_tool("add_dynamic_tool", {"name": "hello"})
        print("  " + r.content[0].text)
        names = [t.name for t in (await client.list_tools()).tools]
        print(f"  当前工具列表: {names}")
        r = await client.call_tool("dyn_hello", {"x": 1})
        print(f"  调用新工具 dyn_hello -> {r.structured_content}")

        print()
        print("=" * 72)
        print("7) 想真正跑通 elicitation 怎么办？（已实测结论）")
        print("=" * 72)
        print("  elicitation 属于『服务端反向请求』。而 2026-07-28 版协议**取消了**服务端主动")
        print("  请求（改用 MRTR），所以：")
        print("    ✗ 内存连接 Client(mcp)            -> NoBackChannelError")
        print("    ✗ HTTP 但用默认 mode='auto'（协商到 2026-07-28）-> NoBackChannelError")
        print("    ✓ HTTP + mode='legacy'（协商到 2025-11-25）     -> 成功")
        print()
        print("  实测代码（先另开一个终端跑：python \"06_上下文Context.py\" --http）：")
        print("""
    from mcp import Client

    async with Client("http://127.0.0.1:8000/mcp",
                      mode="legacy",                 # ← 关键
                      elicitation_callback=handler) as c:
        r = await c.call_tool("book_flight", {"city": "上海"})
        print(r.content[0].text)     # -> 已按 2026-10-01 为你准备去 上海 的行程
""")
        print("  stdio 同理：Client(StdioServerParameters(...), mode='legacy', elicitation_callback=...)")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        mcp.run()
    elif "--http" in sys.argv:
        mcp.run(transport="streamable-http", port=8000)
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
        asyncio.run(demo())
