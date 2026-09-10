r"""
04_实战项目 / test_server.py —— 给笔记库服务器写测试

要点：
  * **在 import server 之前**设置 MCP_NOTES_FILE 环境变量，把数据指到临时文件，
    这样测试不会污染真实的 notes.json
  * 用 `Client(server.mcp)` 内存直连，不需要起进程
  * 断言 is_error / structured_content / content 三种返回途径

运行：
    .\.venv\Scripts\python.exe test_server.py            # 内置运行器
    .\.venv\Scripts\python.exe -m pytest test_server.py -v   # 装了 pytest 之后
"""

from __future__ import annotations

import asyncio
import inspect
import os
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. 隔离数据文件（必须在导入 server 之前）
# ---------------------------------------------------------------------------
TMP_NOTES = Path(tempfile.gettempdir()) / "mcp_learning_test_notes.json"
TMP_NOTES.unlink(missing_ok=True)
os.environ["MCP_NOTES_FILE"] = str(TMP_NOTES)

sys.path.insert(0, str(Path(__file__).parent))

from mcp import Client  # noqa: E402
import server  # noqa: E402

mcp = server.mcp


# ---------------------------------------------------------------------------
# 2. 用例
# ---------------------------------------------------------------------------
async def test_tool_inventory() -> None:
    async with Client(mcp) as client:
        names = {t.name for t in (await client.list_tools()).tools}
        assert names == {
            "search_notes", "add_note", "get_note", "delete_note", "list_tags", "list_notes",
        }, names


async def test_destructive_annotation() -> None:
    async with Client(mcp) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
        assert tools["delete_note"].annotations.destructive_hint is True
        assert tools["search_notes"].annotations.read_only_hint is True


async def test_add_and_get_note() -> None:
    async with Client(mcp) as client:
        added = await client.call_tool(
            "add_note",
            {"title": "测试笔记", "content": "这是正文", "tags": ["测试", "  大写会被归一化  "]},
        )
        assert added.is_error is False
        note = added.structured_content
        assert note["title"] == "测试笔记"
        assert note["tags"] == ["测试", "大写会被归一化"]      # lower() + strip()

        got = await client.call_tool("get_note", {"note_id": note["id"]})
        assert got.structured_content["content"] == "这是正文"


async def test_empty_title_is_tool_error() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool("add_note", {"title": "   ", "content": "x"})
        assert result.is_error is True
        assert "标题不能为空" in result.content[0].text


async def test_unknown_note_id() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool("get_note", {"note_id": "does-not-exist"})
        assert result.is_error is True
        assert "does-not-exist" in result.content[0].text


async def test_search_by_keyword_and_tag() -> None:
    async with Client(mcp) as client:
        await client.call_tool("add_note", {"title": "K8s 备忘", "content": "kubectl get pods", "tags": ["ops"]})
        await client.call_tool("add_note", {"title": "Docker 备忘", "content": "docker ps", "tags": ["ops"]})

        by_tag = await client.call_tool("search_notes", {"tag": "ops"})
        assert by_tag.structured_content["total"] == 2

        by_kw = await client.call_tool("search_notes", {"keyword": "kubectl"})
        assert by_kw.structured_content["total"] == 1
        assert by_kw.structured_content["items"][0]["title"] == "K8s 备忘"


async def test_delete_requires_confirmation() -> None:
    async with Client(mcp) as client:
        added = await client.call_tool("add_note", {"title": "待删除", "content": "x"})
        note_id = added.structured_content["id"]

        refused = await client.call_tool("delete_note", {"note_id": note_id})
        assert refused.is_error is True
        assert "破坏性操作" in refused.content[0].text

        # 确认后仍然存在 -> 说明上面确实没删
        assert (await client.call_tool("get_note", {"note_id": note_id})).is_error is False

        ok = await client.call_tool("delete_note", {"note_id": note_id, "confirm": True})
        assert ok.is_error is False
        assert (await client.call_tool("get_note", {"note_id": note_id})).is_error is True


async def test_resource_note_markdown() -> None:
    async with Client(mcp) as client:
        added = await client.call_tool(
            "add_note", {"title": "资源测试", "content": "正文内容", "tags": ["r"]}
        )
        note_id = added.structured_content["id"]
        read = await client.read_resource(f"notes://note/{note_id}")
        text = read.contents[0].text
        assert text.startswith("# 资源测试")
        assert "正文内容" in text
        assert "#r" in text
        assert read.contents[0].mime_type == "text/markdown"


async def test_resource_template_list() -> None:
    async with Client(mcp) as client:
        templates = await client.list_resource_templates()
        uris = {t.uri_template for t in templates.resource_templates}
        assert "notes://note/{note_id}" in uris
        assert "notes://tag/{tag}" in uris


async def test_prompts() -> None:
    async with Client(mcp) as client:
        names = {p.name for p in (await client.list_prompts()).prompts}
        assert names == {"review_note", "summarize_topic"}

        single = await client.get_prompt("review_note", {"note_id": "abc"})
        assert len(single.messages) == 1
        assert "notes://note/abc" in single.messages[0].content.text

        multi = await client.get_prompt("summarize_topic", {"topic": "学习", "style": "三条要点"})
        assert len(multi.messages) == 2


async def test_lifespan_persists_to_disk() -> None:
    """lifespan 的 finally 会落盘；新连接能读回数据。"""
    async with Client(mcp) as client:
        added = await client.call_tool("add_note", {"title": "持久化", "content": "check"})
        note_id = added.structured_content["id"]
    # 连接已关闭 -> lifespan 已执行 save()
    assert TMP_NOTES.exists()
    import json

    raw = json.loads(TMP_NOTES.read_text(encoding="utf-8"))
    assert any(item["id"] == note_id for item in raw)


# ---------------------------------------------------------------------------
# 3. pytest 兼容层（装了 pytest 时生效）
# ---------------------------------------------------------------------------
try:
    import pytest

    @pytest.fixture
    def anyio_backend() -> str:
        return "asyncio"

    @pytest.fixture
    async def client():
        async with Client(mcp, raise_exceptions=False) as c:
            yield c

    @pytest.mark.anyio
    async def test_via_fixture(client: Client) -> None:
        result = await client.call_tool("list_tags", {})
        assert result.is_error is False

except ImportError:
    pytest = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# 4. 内置运行器
# ---------------------------------------------------------------------------
async def run_all() -> int:
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and inspect.iscoroutinefunction(obj) and name != "test_via_fixture"
    ]
    passed = failed = 0
    for name, fn in tests:
        try:
            await fn()
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  [FAIL] {name}: {type(exc).__name__}: {exc}")
        else:
            passed += 1
            print(f"  [PASS] {name}")
    print(f"\n共 {len(tests)} 个用例：通过 {passed}，失败 {failed}")
    if failed == 0:
        TMP_NOTES.unlink(missing_ok=True)
    return 1 if failed else 0


if __name__ == "__main__":
    print("=" * 74)
    print("笔记库服务器测试")
    print("=" * 74)
    code = asyncio.run(run_all())
    sys.exit(code)
