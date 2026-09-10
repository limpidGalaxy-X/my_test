r"""
07 - 客户端（Client）：站在"调用方"的角度看 MCP

写 Server 是给别人用的；写 Client 才让你看清协议的另一半。
学会 Client 之后，你能自己写 Agent、写测试、写集成工具。

Client 支持四种构造方式：

    Client(mcp)                                 内存直连服务器对象（最快，适合测试）
    Client(StdioServerParameters(...))          启动子进程 + stdio 通信
    Client("http://127.0.0.1:8000/mcp")         连接 Streamable HTTP 服务器
    Client(transport)                           自定义传输（streamable_http_client / sse_client）

⚠ 构造 ≠ 连接：必须进入 `async with` 才真正建立连接，否则报
   RuntimeError: Client must be used within an async context manager

运行：
    .\.venv\Scripts\python.exe "07_客户端Client.py"                    # 内存模式（默认）
    .\.venv\Scripts\python.exe "07_客户端Client.py" --stdio             # stdio 模式
    .\.venv\Scripts\python.exe "07_客户端Client.py" --http http://127.0.0.1:8000/mcp
"""

from __future__ import annotations

import asyncio
import json
import sys

from mcp import Client, StdioServerParameters
from mcp.server import MCPServer
from mcp.types import ToolAnnotations

# ---------------------------------------------------------------------------
# 内置一个演示用的服务器（内存模式直接用它，不用起进程）
# ---------------------------------------------------------------------------
demo_server = MCPServer("ClientDemo", instructions="供客户端示例调用的迷你服务器。")


@demo_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@demo_server.tool()
def boom() -> str:
    """Always fails, to show is_error."""
    raise ValueError("故意失败")


@demo_server.resource("greeting://{name}")
def greeting(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"


@demo_server.prompt()
def review(code: str) -> str:
    """Review a piece of code."""
    return f"请评审这段代码：\n{code}"


# ---------------------------------------------------------------------------
# 1. 内存模式：把服务器对象直接当"传输"
# ---------------------------------------------------------------------------
async def demo_in_memory() -> None:
    # raise_exceptions=True 时，服务端异常会直接抛到客户端（仅对进程内连接有效）
    async with Client(demo_server, raise_exceptions=False) as client:
        print("=" * 72)
        print("连接建立后能拿到什么")
        print("=" * 72)
        print(f"  server_info         : {client.server_info}")
        print(f"  server_capabilities : {client.server_capabilities}")
        print(f"  protocol_version    : {client.protocol_version}")
        print(f"  instructions        : {client.instructions}")

        print()
        print("=" * 72)
        print("tools/list 与 tools/call")
        print("=" * 72)
        tools = await client.list_tools()
        for t in tools.tools:
            print(f"  {t.name:<6} {t.description!r}  schema={json.dumps(t.input_schema, ensure_ascii=False)}")
            if t.annotations:
                print(f"         annotations={t.annotations.model_dump(exclude_none=True)}")

        result = await client.call_tool("add", {"a": 2, "b": 3})
        print("\n  call_tool('add', {a:2,b:3}) 的返回对象：")
        print(f"    .content            = {result.content}          # 给模型看的内容块")
        print(f"    .structured_content = {result.structured_content}   # 机器可读")
        print(f"    .is_error           = {result.is_error}")

        failed = await client.call_tool("boom", {})
        print(f"\n  服务端抛异常时：is_error={failed.is_error}  text={failed.content[0].text!r}")

        print()
        print("=" * 72)
        print("resources 与 prompts")
        print("=" * 72)
        resources = await client.list_resources()
        templates = await client.list_resource_templates()
        print(f"  静态资源: {[r.uri for r in resources.resources]}")
        print(f"  资源模板: {[t.uri_template for t in templates.resource_templates]}")

        read = await client.read_resource("greeting://World")
        print(f"  read_resource -> {read.contents[0].text!r}")

        prompts = await client.list_prompts()
        print(f"  提示词: {[(p.name, [a.name for a in (p.arguments or [])]) for p in prompts.prompts]}")
        got = await client.get_prompt("review", {"code": "print(1)"})
        print(f"  get_prompt -> role={got.messages[0].role} text={got.messages[0].content.text!r}")

        print()
        print("=" * 72)
        print("分页：cursor 是不透明令牌")
        print("=" * 72)
        page = await client.list_tools(cursor=None)
        print(f"  next_cursor = {page.next_cursor}   （没有更多页时是 None）")


# ---------------------------------------------------------------------------
# 2. stdio 模式：Client 帮你把服务器拉起来当子进程
# ---------------------------------------------------------------------------
async def demo_stdio(server_file: str) -> None:
    params = StdioServerParameters(
        command=sys.executable,          # 用当前解释器（.venv 里的）
        args=[server_file, "--serve"],
        # 子进程**不继承**你的环境变量，需要显式传：
        # env={"MY_TOKEN": "..."},
    )
    print(f"即将启动子进程：{params.command} {params.args}")
    async with Client(params) as client:
        tools = await client.list_tools()
        print(f"  server_info = {client.server_info}")
        print(f"  tools = {[t.name for t in tools.tools]}")
        result = await client.call_tool("add", {"a": 1, "b": 2})
        print(f"  add(1,2) = {result.structured_content}")

    print("  退出 async with 时会自动关闭子进程（stdin 关闭 -> SIGTERM -> SIGKILL）")


# ---------------------------------------------------------------------------
# 3. Streamable HTTP 模式：连一个已经在跑的服务器
# ---------------------------------------------------------------------------
async def demo_http(url: str) -> None:
    print(f"连接 {url}")
    print("  （URL 形式 = Streamable HTTP 传输；也可以用 streamable_http_client 自定义 http 客户端）")

    async with Client(url) as client:
        print(f"  server_info      = {client.server_info}")
        print(f"  protocol_version = {client.protocol_version}")
        print(f"  instructions     = {client.instructions}")
        tools = await client.list_tools()
        for t in tools.tools:
            print(f"    - {t.name}: {t.description}")

        result = await client.call_tool("add", {"a": 10, "b": 20})
        print(f"  add(10,20) = {result.structured_content}")

    print()
    print("  想用自定义 httpx2 客户端（加认证头/超时）时：")
    print("""
    import httpx2
    from mcp.client.streamable_http import streamable_http_client

    async with httpx2.AsyncClient(
        headers={"Authorization": "Bearer <token>"},
        timeout=httpx2.Timeout(30.0, read=300.0),
    ) as http_client:
        transport = streamable_http_client(url, http_client=http_client)
        async with Client(transport) as c:
            ...
    """)


# ---------------------------------------------------------------------------
# 4. mode 参数：auto / legacy / 指定版本
# ---------------------------------------------------------------------------
def explain_mode() -> None:
    print("=" * 72)
    print("关于 Client 的 mode 参数（决定用哪套协议时代说话）")
    print("=" * 72)
    print("  mode='auto'（默认）：先发 server/discover 探测，不支持就回退到 initialize 握手")
    print("  mode='legacy'      ：强制走 initialize 握手，协商到 2025-11-25 或更早")
    print("  mode='2026-07-28'  ：直接采用无状态协议，不握手，server_info 为 None")
    print()
    print("  实测对照（连同一个 v2 服务器）：")
    print("    Client(mcp)               -> protocol_version = 2026-07-28")
    print("    Client(url, mode='legacy')-> protocol_version = 2025-11-25")
    print()
    print("  什么时候必须用 legacy？")
    print("    * 需要**服务端反向请求**：elicitation / roots / sampling")
    print("      （2026-07-28 取消了这类请求，改用 MRTR，SDK 的 ctx.elicit 仍走老路）")
    print("    * 需要 message_handler 接收服务端推送")
    print()
    print("  其它常用构造参数：")
    print("    raise_exceptions=True     进程内连接时，服务端异常直接抛出而不是变成 is_error")
    print("    read_timeout_seconds=30   请求超时（秒）")
    print("    elicitation_callback=...  处理服务端追问")
    print("    sampling_callback=...     替服务端调用 LLM")
    print("    list_roots_callback=...   告诉服务端可操作的目录")


if __name__ == "__main__":
    if "--stdio" in sys.argv:
        target = r"02_最小服务器.py"
        asyncio.run(demo_stdio(target))
    elif "--http" in sys.argv:
        idx = sys.argv.index("--http")
        url = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "http://127.0.0.1:8000/mcp"
        asyncio.run(demo_http(url))
    elif "--mode-help" in sys.argv:
        explain_mode()
    else:
        asyncio.run(demo_in_memory())
        print()
        explain_mode()
        print()
        print("试试：")
        print('  python "07_客户端Client.py" --stdio')
        print('  python "06_上下文Context.py" --http     # 另一个终端')
        print('  python "07_客户端Client.py" --http http://127.0.0.1:8000/mcp')
