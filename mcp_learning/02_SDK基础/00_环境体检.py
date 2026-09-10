r"""
00 - 环境体检：确认 MCP Python SDK 装好了、能用。

运行：
    .\.venv\Scripts\python.exe "00_环境体检.py"

它会检查：
  1. mcp 包能否导入、版本是多少
  2. 协议版本常量（v2 是 2026-07-28）
  3. 能否创建一个 MCPServer 并用内存 Client 调用它的工具（端到端冒烟测试）
"""

from __future__ import annotations

import asyncio
import sys

OK = "[OK]"
BAD = "[X ]"


def check_python() -> bool:
    v = sys.version_info
    print(f"{OK if v >= (3, 10) else BAD} Python {v.major}.{v.minor}.{v.micro}（需要 >= 3.10）")
    return v >= (3, 10)


def check_import() -> bool:
    try:
        import mcp
        from mcp.server import MCPServer  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        print(f"{BAD} 导入 mcp 失败：{type(exc).__name__}: {exc}")
        print("     安装命令： .\\.venv\\Scripts\\python.exe -m pip install \"mcp[cli]\"")
        return False

    try:
        from importlib.metadata import version

        sdk_version = version("mcp")
    except Exception:  # noqa: BLE001
        sdk_version = getattr(mcp, "__version__", "未知")

    print(f"{OK} 导入 mcp 成功，SDK 版本 = {sdk_version}")
    if sdk_version != "未知" and sdk_version.split(".")[0] == "1":
        print(f"{BAD} 检测到 v1（FastMCP 时代）。本教程基于 v2，请升级：pip install -U \"mcp>=2.2\"")
        return False
    return True


def check_protocol_versions() -> None:
    try:
        from mcp.types.version import (  # type: ignore[import-not-found]
            KNOWN_PROTOCOL_VERSIONS,
            LATEST_PROTOCOL_VERSION,
            SUPPORTED_PROTOCOL_VERSIONS,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"{BAD} 读取协议版本常量失败：{type(exc).__name__}: {exc}")
        return

    print(f"{OK} LATEST_PROTOCOL_VERSION      = {LATEST_PROTOCOL_VERSION}")
    print(f"     KNOWN_PROTOCOL_VERSIONS    = {KNOWN_PROTOCOL_VERSIONS}")
    print(f"     SUPPORTED_PROTOCOL_VERSIONS= {SUPPORTED_PROTOCOL_VERSIONS}")


def smoke_test() -> None:
    """最关键的一步：真的建一个服务器 + 客户端，跑一次 tools/call。"""
    try:
        from mcp import Client
        from mcp.server import MCPServer
    except Exception:  # noqa: BLE001
        return

    mcp = MCPServer("SmokeTest")

    @mcp.tool()
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    async def main() -> None:
        async with Client(mcp) as client:
            tools = await client.list_tools()
            print(f"{OK} tools/list 返回 {len(tools.tools)} 个工具：{[t.name for t in tools.tools]}")
            print(f"     生成的 inputSchema = {tools.tools[0].input_schema}")

            result = await client.call_tool("add", {"a": 1, "b": 2})
            print(f"{OK} tools/call add(1, 2) -> content={result.content} "
                  f"structured_content={result.structured_content}")

    try:
        asyncio.run(main())
        print(f"{OK} 端到端冒烟测试通过，环境可用。")
    except Exception as exc:  # noqa: BLE001
        print(f"{BAD} 冒烟测试失败：{type(exc).__name__}: {exc}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 70)
    print("MCP Python SDK 环境体检")
    print("=" * 70)
    ok = check_python()
    if ok:
        ok = check_import()
    if ok:
        check_protocol_versions()
        print("-" * 70)
        smoke_test()
    print("=" * 70)
    sys.exit(0 if ok else 1)
