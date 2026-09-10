r"""
03_进阶 / 01 - 结构化输出与 pydantic

MCP 的工具返回值有两副面孔：
  * content            —— 给模型看的**内容块**（文本/图片/音频/资源引用）
  * structured_content —— 给程序看的**结构化数据**

SDK 会根据你的**返回类型注解**自动生成 outputSchema，
并按规则决定 structured_content 长什么样。

实测规则（本文件跑一遍就能看到）：

    返回类型                  structured_content              outputSchema
    ─────────────────────────────────────────────────────────────────────────
    int / str / float / bool  {"result": <值>}                {"result": <类型>}
    list[X]                   {"result": [<值>, ...]}         {"result": array}
    None                      {"result": None}                {"result": "null"}
    pydantic BaseModel        {"字段": 值, ...}（模型本身）     模型自己的 JSON Schema
    dataclass                 {"字段": 值, ...}               同字段
    structured_output=False   None（只有纯文本 content）       （不生成）

⚠️ 注意标量/列表会被包一层 "result"，而 pydantic 模型不会 —— 这是写客户端断言时
   最容易搞错的地方。列表返回时，每个元素在 content 里是**独立的文本块**。

运行：
    .\.venv\Scripts\python.exe "01_结构化输出与pydantic.py"
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field

from mcp.server import MCPServer

mcp = MCPServer("StructuredOutput", instructions="演示各种返回类型对应的输出结构。")


# ---------------------------------------------------------------------------
# 1. 标量 / 容器：会被包一层 "result"
# ---------------------------------------------------------------------------
@mcp.tool()
def plain_int(a: int, b: int) -> int:
    """Return a bare integer."""
    return a + b


@mcp.tool()
def plain_list(n: int) -> list[str]:
    """Return a bare list."""
    return [f"item-{i}" for i in range(n)]


@mcp.tool()
def no_return(x: int) -> None:
    """Return nothing at all."""
    print("（这个副作用不会传给客户端）", file=sys.stderr)


# ---------------------------------------------------------------------------
# 2. pydantic 模型：推荐的"复杂返回"写法
# ---------------------------------------------------------------------------
class Address(BaseModel):
    """嵌套模型。"""

    city: str
    street: str = Field(description="街道地址")


class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(BaseModel):
    """用户信息（嵌套 + 枚举 + 约束 + 可选）。"""

    id: int = Field(ge=1, description="用户 ID，必须为正整数")
    name: str = Field(min_length=1, max_length=50, description="显示名")
    role: Role = Field(default=Role.USER, description="角色")
    address: Address | None = Field(default=None, description="地址，可能为空")
    tags: list[str] = Field(default_factory=list, description="标签")


@mcp.tool()
def get_user(user_id: int) -> User:
    """Look up a user by id."""
    return User(
        id=user_id,
        name="张三",
        role=Role.ADMIN,
        address=Address(city="北京", street="中关村大街 1 号"),
        tags=["vip", "beta"],
    )


# ---------------------------------------------------------------------------
# 3. dataclass 也可以
# ---------------------------------------------------------------------------
@dataclass
class Point:
    x: float
    y: float
    label: Annotated[str, Field(description="点的名字")] = "origin"


@mcp.tool()
def origin() -> Point:
    """Return the origin point."""
    return Point(0.0, 0.0)


@mcp.tool()
def point_list(n: int) -> list[Point]:
    """Return several points."""
    return [Point(float(i), float(i * 2), f"p{i}") for i in range(n)]


# ---------------------------------------------------------------------------
# 4. Literal / Optional 等特殊类型
# ---------------------------------------------------------------------------
class Report(BaseModel):
    status: Literal["ok", "warning", "error"] = Field(description="状态字面量")
    score: float | None = Field(default=None, description="可选分数")


@mcp.tool()
def make_report(status: str) -> Report:
    """Build a report. (status 用 str 接收，返回类型里用 Literal 约束)"""
    value: Literal["ok", "warning", "error"] = "ok"
    if status in ("ok", "warning", "error"):
        value = status  # type: ignore[assignment]
    return Report(status=value, score=None if value == "error" else 87.5)


# ---------------------------------------------------------------------------
# 5. structured_output=False：强制走纯文本
# ---------------------------------------------------------------------------
@mcp.tool(structured_output=False)
def plain_text(x: int) -> int:
    """Force plain-text output even though it returns an int."""
    return x * 2


# ---------------------------------------------------------------------------
# 6. 需要给人看的内容 + 给机器看的数据？用 pydantic 模型同时满足
#    （SDK 会自动把结构化内容也序列化进 content，见下面 demo 的输出）
# ---------------------------------------------------------------------------
class SearchResult(BaseModel):
    """搜索结果。"""

    query: str
    hits: list[str]
    total: int = Field(description="命中总数")


@mcp.tool()
def search(query: str, limit: int = 3) -> SearchResult:
    """Search something and return both a summary and structured data."""
    hits = [f"{query}-{i}" for i in range(1, limit + 1)]
    return SearchResult(query=query, hits=hits, total=len(hits))


# ---------------------------------------------------------------------------
# 自测
# ---------------------------------------------------------------------------
async def demo() -> None:
    from mcp import Client

    async with Client(mcp) as client:
        print("=" * 74)
        print("1) tools/list 里的 outputSchema")
        print("=" * 74)
        for t in (await client.list_tools()).tools:
            schema = json.dumps(t.output_schema, ensure_ascii=False) if t.output_schema else "（无）"
            if len(schema) > 150:
                schema = schema[:150] + " ..."
            print(f"  {t.name:<12} {schema}")

        print()
        print("=" * 74)
        print("2) 各种返回类型的 structured_content / content")
        print("=" * 74)

        async def show(tool: str, args: dict) -> None:
            r = await client.call_tool(tool, args)
            text = r.content[0].text if r.content else ""
            text = text if len(text) <= 70 else text[:70] + "..."
            print(f"  {tool}{args}")
            print(f"      structured_content = {r.structured_content}")
            print(f"      content[0].text    = {text!r}")

        await show("plain_int", {"a": 1, "b": 2})
        await show("plain_list", {"n": 2})
        await show("no_return", {"x": 1})
        await show("get_user", {"user_id": 7})
        await show("origin", {})
        await show("point_list", {"n": 2})
        await show("make_report", {"status": "warning"})
        await show("plain_text", {"x": 21})
        await show("search", {"query": "mcp", "limit": 2})

        print()
        print("=" * 74)
        print("3) 完整看一个工具的返回对象")
        print("=" * 74)
        r = await client.call_tool("get_user", {"user_id": 7})
        print(json.dumps(r.model_dump(), ensure_ascii=False, indent=2, default=str))

        print()
        print("=" * 74)
        print("结论")
        print("=" * 74)
        print("  * 标量/列表/字典 -> 被包成 {'result': ...}；pydantic 模型 -> 直接用模型字段")
        print("  * outputSchema 是自动生成的，客户端可以据此做校验")
        print("  * 想让模型读到 JSON，SDK 会把结构化结果序列化进 content")
        print("  * 不确定想要什么时，就定义一个 pydantic 模型当返回类型")


if __name__ == "__main__":
    asyncio.run(demo())
