r"""
03 - 工具（Tool）：MCP 里最重要的原语

工具 = 模型可以主动调用的函数。
MCP 的 @mcp.tool() 会把你的 Python 函数"翻译"成模型能理解的规格：

    Python 签名                                        JSON Schema
    ─────────────────────────────────────────────      ─────────────────────────────
    def add(a: int, b: int) -> int:                    {"type":"object",
                                                         "properties":{
                                                           "a":{"type":"integer"},
                                                           "b":{"type":"integer"}},
    docstring  "Add two numbers."                      "required":["a","b"]}
        ↓                                                   ↓
    工具的 description                                   工具的 inputSchema

本文件覆盖 7 件事：
  1. 基本写法（类型注解 = Schema）
  2. 给参数加描述和约束：Annotated + pydantic.Field
  3. 默认值 -> 可选参数
  4. 结构化输出（返回 pydantic 模型 / dataclass）
  5. 错误处理：ToolError（给模型看）vs 未捕获异常（协议错误）
  6. 工具注解 annotations：告诉 Host 这个工具危不危险
  7. 运行时增删工具

运行：
    .\.venv\Scripts\python.exe "03_工具Tool.py"
    .\.venv\Scripts\python.exe "03_工具Tool.py" --serve
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, Field

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

mcp = MCPServer(
    "ToolShowcase",
    instructions="演示 MCP 工具的各类写法。调用工具前先看它的 description。",
)


# ---------------------------------------------------------------------------
# 1. 基本写法：类型注解就是 Schema
# ---------------------------------------------------------------------------
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


# ---------------------------------------------------------------------------
# 2. 用 Annotated + Field 给参数加描述和约束
#    描述会写进 JSON Schema 的 description 字段，模型能看到，非常影响调用准确率。
#    ge/le/min_length 等约束由 pydantic 在调用前校验，非法参数根本进不了你的函数。
# ---------------------------------------------------------------------------
@mcp.tool(title="搜索文档")          # title 是给人看的标题，description 才给模型看
def search_docs(
    query: Annotated[str, Field(description="搜索关键词，支持空格分词。", min_length=1)],
    limit: Annotated[int, Field(ge=1, le=50, description="最多返回多少条结果。")] = 10,
    fuzzy: Annotated[bool, Field(description="是否开启模糊匹配。")] = False,
) -> list[str]:
    """Search the internal documentation by keyword."""
    prefix = "~" if fuzzy else ""
    return [f"{prefix}{query}-结果{i}" for i in range(1, limit + 1)]


# ---------------------------------------------------------------------------
# 3. 默认值 -> 参数变成"可选"
#    search_docs 的 limit / fuzzy 有默认值，所以不在 required 里。
# ---------------------------------------------------------------------------
@mcp.tool()
def divide(a: float, b: float = 1.0) -> float:
    """Divide a by b."""
    return a / b


# ---------------------------------------------------------------------------
# 4. 结构化输出：返回类型是 pydantic 模型时，SDK 自动生成 outputSchema，
#    并同时在结果里给出 structured_content（机器可读）和 content（文本）。
# ---------------------------------------------------------------------------
class WeatherReport(BaseModel):
    """某个城市的天气。"""

    city: str
    temperature: float = Field(description="摄氏度")
    condition: str = Field(description="天气状况，例如 sunny / rainy")
    humidity: int = Field(ge=0, le=100, description="相对湿度百分比")


@mcp.tool()
def get_weather(
    city: Annotated[str, Field(description="城市名，例如 北京。")],
) -> WeatherReport:
    """Get the current weather for a city."""
    fake = {"北京": (23.5, "sunny", 40), "上海": (26.0, "rainy", 78)}
    temp, cond, hum = fake.get(city, (20.0, "unknown", 50))
    return WeatherReport(city=city, temperature=temp, condition=cond, humidity=hum)


# dataclass 同样支持
@dataclass
class Point:
    x: float
    y: float


@mcp.tool()
def origin() -> Point:
    """Return the origin point."""
    return Point(0.0, 0.0)


# ---------------------------------------------------------------------------
# 5. 错误处理（下面的输出是实测结果，不是推测）
#    * ToolError        -> is_error=True，错误信息**原样**给模型看，模型能自我纠正
#    * 其它未捕获异常    -> 也是 is_error=True，但信息被吞成 "Error executing tool xxx"，
#                          真实堆栈只写进服务器 stderr 日志 —— 模型看不到细节，无法纠正
#    * MCPError         -> 变成 JSON-RPC 协议错误（模型看不到）
#    结论：凡是"用户/模型输入不合法"这类可预期错误，一律抛 ToolError。
# ---------------------------------------------------------------------------
@mcp.tool()
def read_file(path: str) -> str:
    """Read a small text file, for demonstration only."""
    allowed = {"readme.txt": "hello mcp"}
    if path not in allowed:
        raise ToolError(f"文件 {path!r} 不存在或不允许访问。可用文件：{sorted(allowed)}")
    return allowed[path]


@mcp.tool()
def always_crashes() -> str:
    """故意抛未捕获异常，用来对比错误处理方式。"""
    raise RuntimeError("内部未处理的错误")


# ---------------------------------------------------------------------------
# 6. 工具注解 annotations：给 Host 的安全提示（不是强制约束！）
#    readOnlyHint     只读，不会改数据
#    destructiveHint  可能造成破坏性修改
#    idempotentHint   重复调用结果相同
#    openWorldHint    会与外部世界交互（网络等），结果不可完全预测
# ---------------------------------------------------------------------------
@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )
)
def get_server_time() -> str:
    """Return the current server time (read-only operation)."""
    import datetime

    return datetime.datetime.now().isoformat(timespec="seconds")


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )
)
def delete_everything(confirm: bool = False) -> str:
    """DANGEROUS: delete all data. Requires confirm=True. (demo only, does nothing)"""
    return "已确认（演示，未真的删除）" if confirm else "未确认，什么都没做"


# ---------------------------------------------------------------------------
# 7. 运行时增删工具
# ---------------------------------------------------------------------------
def dynamic_tool(x: int) -> int:
    """A tool added at runtime (not via decorator)."""
    return x * 100


# ---------------------------------------------------------------------------
# 自测
# ---------------------------------------------------------------------------
def show(label: str, value: object) -> None:
    print(f"  {label}: {value}")


async def demo() -> None:
    from mcp import Client

    async with Client(mcp) as client:
        print("=" * 72)
        print("1) tools/list：SDK 自动生成的规格")
        print("=" * 72)
        tools = await client.list_tools()
        for t in tools.tools:
            print(f"\n● {t.name}")
            print(f"  description : {t.description}")
            print(f"  inputSchema : {json.dumps(t.input_schema, ensure_ascii=False)}")
            if t.output_schema:
                print(f"  outputSchema: {json.dumps(t.output_schema, ensure_ascii=False)}")
            if t.annotations:
                print(f"  annotations : {t.annotations.model_dump(exclude_none=True)}")

        print()
        print("=" * 72)
        print("2) 正常调用")
        print("=" * 72)
        r = await client.call_tool("add", {"a": 1, "b": 2})
        show("add(1,2).structured_content", r.structured_content)
        show("add(1,2).content[0].text     ", r.content[0].text)

        r = await client.call_tool("search_docs", {"query": "mcp", "limit": 2})
        show("search_docs(query=mcp,limit=2)", r.structured_content)

        r = await client.call_tool("get_weather", {"city": "上海"})
        show("get_weather(上海).structured", r.structured_content)
        show("get_weather(上海).text      ", r.content[0].text)

        r = await client.call_tool("origin", {})
        show("origin().structured_content ", r.structured_content)

        print()
        print("=" * 72)
        print("3) 错误处理对比")
        print("=" * 72)
        r = await client.call_tool("read_file", {"path": "secret.txt"})
        show("ToolError -> is_error", r.is_error)
        show("ToolError -> 模型能看到的话", r.content[0].text)

        r = await client.call_tool("always_crashes", {})
        show("未捕获异常 -> is_error", r.is_error)
        show("未捕获异常 -> 内容", r.content[0].text[:120])

        print()
        print("=" * 72)
        print("4) 参数校验（pydantic 在进入你的函数之前就拦下了）")
        print("=" * 72)
        r = await client.call_tool("search_docs", {"query": "mcp", "limit": 999})
        show("limit=999（超过 le=50）-> is_error", r.is_error)
        show("内容", r.content[0].text[:160])

        print()
        print("=" * 72)
        print("5) 运行时增删工具")
        print("=" * 72)
        mcp.add_tool(dynamic_tool, name="dynamic", description="运行时注册的工具")
        names = [t.name for t in (await client.list_tools()).tools]
        show("注册后", names)
        r = await client.call_tool("dynamic", {"x": 7})
        show("dynamic(7)", r.structured_content)

        mcp.remove_tool("dynamic")
        names = [t.name for t in (await client.list_tools()).tools]
        show("移除后", names)


if __name__ == "__main__":
    if "--serve" in sys.argv:
        mcp.run()
    else:
        print("MCP 工具写法演示 —— 用内存 Client 直连服务器\n")
        asyncio.run(demo())
