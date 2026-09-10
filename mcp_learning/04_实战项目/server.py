r"""
04_实战项目 / server.py —— 个人笔记库 MCP 服务器

一个"能用"的完整例子，把前面学的东西全用上：

    ✅ lifespan        启动时从 JSON 文件加载笔记，关闭时落盘
    ✅ Tools           add / search / get / delete / list_tags
    ✅ Resources       notes://index（索引）与 notes://note/{id}（单篇）
    ✅ Prompts         review_note / summarize_topic
    ✅ 注解            delete 标成 destructive，search 标成 readOnly
    ✅ 错误处理        ToolError（给模型看）vs ResourceNotFoundError
    ✅ 结构化输出      pydantic 模型
    ✅ 日志            标准库 logging（走 stderr）
    ✅ 测试友好        模块级 mcp 对象，可以被 Client(mcp) 直连

运行：
    # 内存自测（不用起进程，直接看效果）
    .\.venv\Scripts\python.exe server.py

    # stdio（给 Claude Desktop / Inspector 用）
    .\.venv\Scripts\python.exe server.py --serve

    # Streamable HTTP
    .\.venv\Scripts\python.exe server.py --http

    # 单元测试
    .\.venv\Scripts\python.exe test_server.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from mcp.server import MCPServer
from mcp.server.mcpserver import Context, UserMessage
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError
from mcp.types import Annotations, ToolAnnotations

logger = logging.getLogger(__name__)

# 数据文件：默认跟 server.py 放一起，可用环境变量覆盖
NOTES_FILE = Path(os.environ.get("MCP_NOTES_FILE", Path(__file__).with_name("notes.json")))


# ===========================================================================
# 1. 领域模型（pydantic）
# ===========================================================================
class Note(BaseModel):
    """一篇笔记。"""

    id: str = Field(description="笔记 ID")
    title: str = Field(min_length=1, max_length=100, description="标题")
    content: str = Field(description="正文")
    tags: list[str] = Field(default_factory=list, description="标签")
    updated_at: str = Field(default="", description="最后更新时间（ISO 8601）")


class NoteSummary(BaseModel):
    """搜索结果里的一条。"""

    id: str
    title: str
    tags: list[str]
    snippet: str = Field(description="正文摘要")


class SearchResult(BaseModel):
    """搜索结果。"""

    keyword: str = ""
    tag: str = ""
    total: int
    items: list[NoteSummary]


class TagCount(BaseModel):
    tag: str
    count: int


# ===========================================================================
# 2. 存储层 + lifespan
# ===========================================================================
class NoteStore:
    """极简的 JSON 文件存储。真实项目里换成数据库即可。"""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.notes: dict[str, Note] = {}

    # ---- 生命周期 --------------------------------------------------------
    def load(self) -> None:
        if not self.path.exists():
            logger.info("笔记文件不存在，从空库开始：%s", self.path)
            self.notes = {}
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("读取笔记文件失败（将从空库开始）：%s", exc)
            self.notes = {}
            return
        self.notes = {item["id"]: Note(**item) for item in raw}
        logger.info("已加载 %d 篇笔记", len(self.notes))

    def save(self) -> None:
        try:
            payload = [n.model_dump() for n in self.notes.values()]
            self.path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            logger.info("已保存 %d 篇笔记到 %s", len(self.notes), self.path)
        except OSError as exc:
            logger.error("保存失败：%s", exc)

    # ---- 业务方法 --------------------------------------------------------
    def add(self, title: str, content: str, tags: list[str]) -> Note:
        import datetime

        note = Note(
            id=uuid.uuid4().hex[:8],
            title=title.strip(),
            content=content,
            tags=[t.strip().lower() for t in tags if t.strip()],
            updated_at=datetime.datetime.now().isoformat(timespec="seconds"),
        )
        self.notes[note.id] = note
        return note

    def get(self, note_id: str) -> Note:
        note = self.notes.get(note_id)
        if note is None:
            raise ResourceNotFoundError(
                f"没有 ID 为 {note_id!r} 的笔记。可用 ID：{sorted(self.notes)[:10]}"
            )
        return note

    def delete(self, note_id: str) -> Note:
        if note_id not in self.notes:
            raise ToolError(f"删除失败：没有 ID 为 {note_id!r} 的笔记")
        return self.notes.pop(note_id)

    def search(self, keyword: str = "", tag: str = "", limit: int = 10) -> list[Note]:
        keyword = keyword.strip().lower()
        tag = tag.strip().lower()
        hits: list[Note] = []
        for note in self.notes.values():
            if tag and tag not in note.tags:
                continue
            if keyword and keyword not in note.title.lower() and keyword not in note.content.lower():
                continue
            hits.append(note)
        hits.sort(key=lambda n: n.updated_at, reverse=True)
        return hits[:limit]


@dataclass
class AppContext:
    """lifespan 交给每个请求的东西。"""

    store: NoteStore
    stats: dict[str, int] = field(default_factory=lambda: {"tools_called": 0})


@asynccontextmanager
async def app_lifespan(server: MCPServer) -> AsyncIterator[AppContext]:
    store = NoteStore(NOTES_FILE)
    store.load()
    logger.info("笔记库已就绪：%s", NOTES_FILE)
    try:
        yield AppContext(store=store)
    finally:
        store.save()
        logger.info("笔记库已落盘")


# ===========================================================================
# 3. 服务器与工具
# ===========================================================================
mcp = MCPServer(
    "笔记库",
    title="个人笔记库",
    description="一个演示用的 MCP 服务器：管理你的个人笔记。",
    instructions=(
        "这是一个个人笔记库。回答用户关于笔记的问题前，先调用 search_notes 查找；"
        "要引用原文就用 resources/read 读 notes://note/{id}；"
        "删除笔记前必须先向用户确认，并让用户明确说出笔记 ID。"
    ),
    lifespan=app_lifespan,
)

# 参数化 URI 用 {} 占位；名字必须和函数参数名一致
#
# ⚠️ 踩坑记录：静态资源（URI 里没有 {}) **不允许**声明 Context 参数，导入期就报
#    ValueError: Resource 'notes://index' has no URI template variables, but the
#    handler declares a Context parameter.
#    所以"需要 lifespan 数据"的资源必须写成**模板**（带 {param}），
#    或者干脆做成 tool。下面两种写法都演示了。
NOTE_URI = "notes://note/{note_id}"
TAG_URI = "notes://tag/{tag}"


def _ctx_app(ctx: Context[AppContext]) -> AppContext:
    """把 ctx 里的 lifespan_context 取出来（顺手类型收窄）。"""
    return ctx.request_context.lifespan_context


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def search_notes(
    ctx: Context[AppContext],
    keyword: str = "",
    tag: str = "",
    limit: int = 10,
) -> SearchResult:
    """Search notes by keyword and/or tag. Use this before answering note questions."""
    app = _ctx_app(ctx)
    app.stats["tools_called"] += 1
    notes = app.store.search(keyword, tag, limit)
    logger.info("search_notes keyword=%r tag=%r -> %d 条", keyword, tag, len(notes))

    def snippet(text: str, width: int = 80) -> str:
        flat = re.sub(r"\s+", " ", text).strip()
        return flat if len(flat) <= width else flat[: width - 1] + "…"

    return SearchResult(
        keyword=keyword,
        tag=tag,
        total=len(notes),
        items=[
            NoteSummary(id=n.id, title=n.title, tags=n.tags, snippet=snippet(n.content))
            for n in notes
        ],
    )


@mcp.tool()
def add_note(
    ctx: Context[AppContext],
    title: str,
    content: str,
    tags: list[str] | None = None,
) -> Note:
    """Create a new note and return it."""
    app = _ctx_app(ctx)
    if not title.strip():
        # 可预期的用户输入错误 -> ToolError，模型能看到并自我纠正
        raise ToolError("标题不能为空")
    note = app.store.add(title, content, tags or [])
    app.store.save()                     # 立刻落盘，避免进程被杀丢数据
    app.stats["tools_called"] += 1
    logger.info("add_note -> %s (%s)", note.id, note.title)
    return note


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def get_note(ctx: Context[AppContext], note_id: str) -> Note:
    """Get one note by its id."""
    app = _ctx_app(ctx)
    app.stats["tools_called"] += 1
    return app.store.get(note_id)


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,      # 会删除数据，明确告诉 Host
        idempotentHint=True,
        openWorldHint=False,
    )
)
def delete_note(ctx: Context[AppContext], note_id: str, confirm: bool = False) -> str:
    """DANGEROUS: delete a note. Requires confirm=true."""
    if not confirm:
        raise ToolError("这是一次破坏性操作。请让用户确认后，再用 confirm=true 调用。")
    app = _ctx_app(ctx)
    note = app.store.delete(note_id)
    app.store.save()
    app.stats["tools_called"] += 1
    return f"已删除笔记 {note.id}（{note.title}）"


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def list_tags(ctx: Context[AppContext]) -> list[TagCount]:
    """List all tags with how many notes use each one."""
    app = _ctx_app(ctx)
    counter: dict[str, int] = {}
    for note in app.store.notes.values():
        for tag in note.tags:
            counter[tag] = counter.get(tag, 0) + 1
    app.stats["tools_called"] += 1
    return [TagCount(tag=t, count=c) for t, c in sorted(counter.items(), key=lambda kv: -kv[1])]


# ---------------------------------------------------------------------------
# 资源：单篇（模板）+ 按标签（模板）
# 静态资源拿不到 lifespan 数据，所以"索引"这类需求要么做成 tool，要么做成模板。
# ---------------------------------------------------------------------------
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def list_notes(ctx: Context[AppContext]) -> list[NoteSummary]:
    """List every note as a short summary (id / title / tags / snippet)."""
    app = _ctx_app(ctx)
    app.stats["tools_called"] += 1
    return [
        NoteSummary(
            id=n.id,
            title=n.title,
            tags=n.tags,
            snippet=(n.content[:60] + "…") if len(n.content) > 60 else n.content,
        )
        for n in sorted(app.store.notes.values(), key=lambda n: n.updated_at, reverse=True)
    ]


@mcp.resource(TAG_URI, name="按标签查笔记", mime_type="application/json")
def notes_by_tag(ctx: Context, tag: str) -> list[dict[str, Any]]:
    """All notes carrying a tag, as JSON. (resource templates may use Context)"""
    # ⚠️ resource 里只能写裸 Context，不能写 Context[AppContext]
    app: AppContext = ctx.request_context.lifespan_context
    return [
        {"id": n.id, "title": n.title, "updated_at": n.updated_at}
        for n in app.store.search(tag=tag, limit=100)
    ]


@mcp.resource(NOTE_URI, name="单篇笔记", mime_type="text/markdown")
def note_markdown(ctx: Context, note_id: str) -> str:
    """One note rendered as Markdown."""
    app: AppContext = ctx.request_context.lifespan_context
    note = app.store.get(note_id)         # 找不到会抛 ResourceNotFoundError
    tags = " ".join(f"#{t}" for t in note.tags)
    return f"# {note.title}\n\n{note.content}\n\n{tags}\n\n_更新于 {note.updated_at}_"


# ---------------------------------------------------------------------------
# 提示词
# ---------------------------------------------------------------------------
@mcp.prompt(title="评审笔记")
def review_note(note_id: str) -> str:
    """Ask the model to review one note for structure and clarity."""
    return (
        f"请先读取资源 notes://note/{note_id}，然后：\n"
        f"1. 用一句话概括这篇笔记在讲什么\n"
        f"2. 指出结构或表达上的问题（不超过 3 条）\n"
        f"3. 给出一个改写后的版本"
    )


@mcp.prompt(title="围绕主题整理")
def summarize_topic(topic: str, style: str = "要点清单") -> list[UserMessage]:
    """Ask the model to synthesise everything about a topic."""
    return [
        UserMessage(f"请先用 search_notes(keyword='{topic}') 找出所有相关笔记。"),
        UserMessage(
            f"然后把这些笔记整合成一份{style}，要求：\n"
            f"- 合并重复内容，标出互相矛盾的地方\n"
            f"- 每条结论后面用 [笔记ID] 标注来源\n"
            f"- 最后列出 3 个还没搞清楚的问题"
        ),
    ]


# ===========================================================================
# 4. 自测
# ===========================================================================
async def demo() -> None:
    from mcp import Client

    async with Client(mcp) as client:
        print("=" * 74)
        print(f"服务器：{client.server_info.name}  协议：{client.protocol_version}")
        print("=" * 74)
        print(client.instructions)

        print()
        print("--- 1) 工具清单 ---")
        for t in (await client.list_tools()).tools:
            flags = ""
            if t.annotations:
                a = t.annotations
                if a.read_only_hint:
                    flags += " [只读]"
                if a.destructive_hint:
                    flags += " [破坏性]"
            print(f"  {t.name:<14}{t.description.splitlines()[0][:52]}{flags}")

        print()
        print("--- 2) 添加笔记 ---")
        created: list[str] = []
        for title, content, tags in [
            ("MCP 学习笔记", "MCP 是模型上下文协议，用 JSON-RPC 2.0 通信。", ["mcp", "学习"]),
            ("装饰器要点", "装饰器本质是函数加工函数；一定要写 functools.wraps。", ["python", "学习"]),
            ("周会纪要", "决定下周把笔记库接进团队的知识库。", ["工作"]),
        ]:
            r = await client.call_tool("add_note", {"title": title, "content": content, "tags": tags})
            created.append(r.structured_content["id"])
            print(f"  + {r.structured_content['id']}  {r.structured_content['title']}")

        print()
        print("--- 3) 搜索 ---")
        r = await client.call_tool("search_notes", {"keyword": "学习"})
        for item in r.structured_content["items"]:
            print(f"  [{item['id']}] {item['title']}  {item['tags']}  {item['snippet']}")

        print()
        print("--- 4) 标签统计 ---")
        r = await client.call_tool("list_tags", {})
        print(f"  {r.structured_content}")

        print()
        print("--- 5) 读资源 ---")
        # 注意：list[NoteSummary] 这类"裸列表"返回会被包一层 {"result": [...]}
        listed = (await client.call_tool("list_notes", {})).structured_content["result"]
        print(f"  list_notes -> {len(listed)} 条")
        first_id = listed[0]["id"]
        note = await client.read_resource(f"notes://note/{first_id}")
        print(f"  notes://note/{first_id} ->")
        for line in note.contents[0].text.splitlines()[:4]:
            print(f"      {line}")
        tagged = await client.read_resource("notes://tag/学习")
        print(f"  notes://tag/学习 -> {tagged.contents[0].text[:90]}...")

        print()
        print("--- 6) 取提示词 ---")
        p = await client.get_prompt("review_note", {"note_id": first_id})
        print(f"  {p.messages[0].content.text.splitlines()[0]}")
        p = await client.get_prompt("summarize_topic", {"topic": "学习", "style": "三条要点"})
        print(f"  多轮提示词共 {len(p.messages)} 条消息")

        print()
        print("--- 7) 错误处理 ---")
        r = await client.call_tool("get_note", {"note_id": "nope"})
        print(f"  未知 ID  -> is_error={r.is_error}  {r.content[0].text[:60]}")
        r = await client.call_tool("add_note", {"title": "   ", "content": "x"})
        print(f"  空标题    -> is_error={r.is_error}  {r.content[0].text[:60]}")
        r = await client.call_tool("delete_note", {"note_id": first_id})
        print(f"  未确认删除 -> is_error={r.is_error}  {r.content[0].text[:60]}")

        print()
        print("--- 8) 确认后删除 ---")
        r = await client.call_tool("delete_note", {"note_id": first_id, "confirm": True})
        print(f"  {r.content[0].text}")

        # 把这次演示新建的笔记清掉，让 notes.json 保持干净
        for note_id in created:
            if note_id != first_id:
                await client.call_tool("delete_note", {"note_id": note_id, "confirm": True})
        print(f"  （已清理本次演示新建的 {len(created)} 篇笔记）")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if "--serve" in sys.argv:
        mcp.run()
    elif "--http" in sys.argv:
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)
    else:
        asyncio.run(demo())
