r"""
04 - 资源（Resource）：让应用决定"贴什么上下文给模型"

Tool 是模型主动调用；Resource 是**应用**决定要不要读取并放进上下文的数据。
可以理解成"MCP 世界的文件 / GET 接口"。

两种形态：
  * 静态资源   @mcp.resource("config://app")        -> 出现在 resources/list
  * 资源模板   @mcp.resource("books://{title}")     -> 出现在 resources/templates/list

规矩（否则导入期就报错）：
  1. 静态资源**不能**有函数参数，也**不能**有 Context 参数
  2. 模板里的 {placeholder} 必须和函数参数名**完全一致**
  3. 模板参数如果绑定 query 变量，必须有默认值

返回值约定：
  * str    -> 文本内容（text）
  * bytes  -> base64 二进制内容（blob）
  * 其它   -> JSON 序列化后的文本
  mime_type 默认 "text/plain"，SDK 不会去猜。

运行：
    .\.venv\Scripts\python.exe "04_资源Resource.py"
    .\.venv\Scripts\python.exe "04_资源Resource.py" --serve
"""

from __future__ import annotations

import asyncio
import json
import sys

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError
from mcp.types import Annotations

mcp = MCPServer(
    "ResourceShowcase",
    instructions="演示 MCP 资源的各种形态：静态、模板、二进制、JSON。",
)

# 假装这是数据库
BOOKS: dict[str, dict[str, object]] = {
    "Dune": {"author": "Frank Herbert", "year": 1965},
    "Neuromancer": {"author": "William Gibson", "year": 1984},
}

# 一段"文件内容"
README_BYTES = "这是一个二进制资源的示例（其实是文本，但以 bytes 返回）".encode("utf-8")


# ---------------------------------------------------------------------------
# 1. 静态资源：URI 里没有变量，函数不能有参数
# ---------------------------------------------------------------------------
@mcp.resource("config://app", mime_type="text/plain", name="应用配置")
def get_config() -> str:
    """The active application configuration."""
    return "theme=dark\nlanguage=zh-CN\ntimeout=30"


@mcp.resource("books://all", mime_type="application/json", name="全部图书")
def all_books() -> dict[str, object]:
    """All books in the catalog, as JSON."""
    # 返回 dict -> SDK 会自动 JSON 序列化后作为文本返回
    return BOOKS


# ---------------------------------------------------------------------------
# 2. 静态资源 + 注解：告诉应用"这资源给谁看、有多重要、什么时候改的"
# ---------------------------------------------------------------------------
@mcp.resource(
    "docs://readme",
    name="项目说明",
    mime_type="text/markdown",
    annotations=Annotations(
        audience=["user", "assistant"],      # user / assistant
        priority=1.0,                        # 0.0 ~ 1.0，1 = 最重要
        lastModified="2026-09-10T18:00:00Z",  # ISO 8601
    ),
)
def readme() -> str:
    """The project README."""
    return "# 示例项目\n\n这是一个用于学习 MCP 的项目。"


# ---------------------------------------------------------------------------
# 3. 资源模板：URI 里有 {title}，函数必须有同名参数
# ---------------------------------------------------------------------------
@mcp.resource("books://{title}", mime_type="application/json", name="单本图书")
def book_entry(title: str) -> dict[str, object]:
    """The catalog entry for one book."""
    if title not in BOOKS:
        # 资源找不到 -> ResourceNotFoundError
        raise ResourceNotFoundError(f"No book titled {title!r} in the catalog.")
    return {"title": title, **BOOKS[title]}


# ---------------------------------------------------------------------------
# 4. 返回 bytes -> 变成 base64 的 blob 内容（二进制资源）
# ---------------------------------------------------------------------------
@mcp.resource("files://readme.bin", mime_type="application/octet-stream", name="二进制示例")
def binary_blob() -> bytes:
    """A binary resource (returned as base64 blob)."""
    return README_BYTES


# ---------------------------------------------------------------------------
# 5. 多参数模板
# ---------------------------------------------------------------------------
@mcp.resource("books://{title}/field/{field}", mime_type="text/plain", name="图书字段")
def book_field(title: str, field: str) -> str:
    """Read a single field of a book entry."""
    entry = BOOKS.get(title)
    if entry is None:
        raise ResourceNotFoundError(f"No book titled {title!r}")
    if field not in entry:
        raise ResourceNotFoundError(f"Book {title!r} has no field {field!r}. "
                                    f"Available: {sorted(entry)}")
    return str(entry[field])


# ---------------------------------------------------------------------------
# 自测
# ---------------------------------------------------------------------------
async def demo() -> None:
    from mcp import Client

    async with Client(mcp) as client:
        print("=" * 72)
        print("1) resources/list：静态资源")
        print("=" * 72)
        listed = await client.list_resources()
        for r in listed.resources:
            print(f"  uri={r.uri}")
            print(f"    name={r.name!r}  mimeType={r.mime_type}  title={r.title!r}")
            if r.annotations:
                print(f"    annotations={r.annotations.model_dump(exclude_none=True)}")

        print()
        print("=" * 72)
        print("2) resources/templates/list：模板资源")
        print("=" * 72)
        templates = await client.list_resource_templates()
        for t in templates.resource_templates:
            print(f"  uriTemplate={t.uri_template}  name={t.name!r}  mimeType={t.mime_type}")

        print()
        print("=" * 72)
        print("3) resources/read：读取各种内容")
        print("=" * 72)

        async def read_and_show(uri: str) -> None:
            result = await client.read_resource(uri)
            for c in result.contents:
                kind = "blob" if getattr(c, "blob", None) is not None else "text"
                print(f"  {uri}")
                print(f"    uri={c.uri}  mimeType={getattr(c, 'mime_type', None)}  内容类型={kind}")
                if kind == "blob":
                    blob = c.blob
                    shown = blob if len(blob) < 60 else blob[:57] + "..."
                    print(f"    blob(base64)={shown}")
                else:
                    text = c.text
                    shown = text if len(text) < 200 else text[:200] + "..."
                    print(f"    text={shown!r}")

        await read_and_show("config://app")
        await read_and_show("books://all")
        await read_and_show("books://Dune")
        await read_and_show("books://Dune/field/year")
        await read_and_show("files://readme.bin")

        print()
        print("=" * 72)
        print("4) 读不存在的资源")
        print("=" * 72)
        try:
            await client.read_resource("books://Nonexistent")
        except Exception as exc:  # noqa: BLE001
            print(f"  {type(exc).__name__}: {exc}")

        print()
        print("提示：资源内容最终怎么用，由 Host（应用）决定 —— 这是 Resource 和 Tool 的本质区别。")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        mcp.run()
    else:
        asyncio.run(demo())
