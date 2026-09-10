r"""
02 - 最小服务器：15 行写出一个能跑的 MCP Server

对照官方 README 的 "A server in 15 lines"：

    from mcp.server import MCPServer

    mcp = MCPServer("Demo")

    @mcp.tool()
    def add(a: int, b: int) -> int:
        '''Add two numbers.'''
        return a + b

    @mcp.resource("greeting://{name}")
    def greeting(name: str) -> str:
        '''Greet someone by name.'''
        return f"Hello, {name}!"

注意你**没有**写的东西：
  * 没有 JSON Schema —— `a: int, b: int` 本身就是 schema
  * 没有请求解析、没有参数校验、没有协议处理
  * 没有 main 函数里的框架启动代码

运行：
    .\.venv\Scripts\python.exe "02_最小服务器.py"           # 内存自测（推荐先跑这个）
    .\.venv\Scripts\python.exe "02_最小服务器.py" --serve   # 真正以 stdio 启动
"""

from __future__ import annotations

import asyncio
import sys

from mcp.server import MCPServer

# ---------------------------------------------------------------------------
# 1. 创建服务器对象
# ---------------------------------------------------------------------------
# name 是必填的服务器标识；instructions 是给模型看的"使用说明"，
# Host 会把它放进系统提示里（可以不写）。
mcp = MCPServer(
    "Demo",
    title="最小示例服务器",
    instructions="这是一个教学用的最小 MCP 服务器，只提供一个加法工具和一个问候资源。",
)


# ---------------------------------------------------------------------------
# 2. 注册一个工具（Tool）—— 模型可以调用它
# ---------------------------------------------------------------------------
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    #  ↑ docstring 会成为工具的 description，模型靠它决定什么时候调用
    return a + b


# ---------------------------------------------------------------------------
# 3. 注册一个资源模板（Resource）—— 模型/用户可以读取它
# ---------------------------------------------------------------------------
# URI 里的 {name} 是占位符，参数名必须和函数参数名一致，否则导入时直接报错。
@mcp.resource("greeting://{name}")
def greeting(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"


# ---------------------------------------------------------------------------
# 4. 自测：用内存 Client 直连这个服务器对象
# ---------------------------------------------------------------------------
async def demo() -> None:
    from mcp import Client

    # Client(mcp) 直接把服务器对象当"传输"，不起子进程、不开端口 —— 官方推荐的测试方式
    async with Client(mcp) as client:
        print("--- 1) 握手后拿到的服务器信息 ---")
        print("server_info        :", client.server_info)
        print("protocol_version   :", client.protocol_version)
        print("instructions       :", client.instructions)

        print("\n--- 2) tools/list：看看 SDK 自动生成了什么 ---")
        tools = await client.list_tools()
        for t in tools.tools:
            print(f"name        : {t.name}")
            print(f"description : {t.description}")
            print(f"input_schema: {t.input_schema}")

        print("\n--- 3) tools/call：真正调用一次 ---")
        result = await client.call_tool("add", {"a": 1, "b": 2})
        print("content            :", result.content)
        print("structured_content :", result.structured_content)
        print("is_error           :", result.is_error)

        print("\n--- 4) resources/list + resources/templates/list ---")
        resources = await client.list_resources()
        templates = await client.list_resource_templates()
        print("静态资源   :", [r.uri for r in resources.resources])
        print("资源模板   :", [t.uri_template for t in templates.resource_templates])

        print("\n--- 5) resources/read：按模板读取 ---")
        read = await client.read_resource("greeting://世界")
        for contents in read.contents:
            print("uri        :", contents.uri)
            print("mime_type  :", getattr(contents, "mime_type", None))
            print("text       :", contents.text)


if __name__ == "__main__":
    if "--serve" in sys.argv:
        # 默认 stdio：Host 会启动这个进程，并通过 stdin/stdout 收发 JSON-RPC 报文。
        # 直接运行会阻塞在这里等你输入报文 —— 所以自测请用不带参数的方式。
        print("以 stdio 传输启动，等待 Host 连接……（Ctrl+C 退出）", file=sys.stderr)
        mcp.run()
    else:
        asyncio.run(demo())
        print("\n提示：加 --serve 参数可以真正启动服务器。")
