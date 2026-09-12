r"""
08 - 测试与 pytest：用内存 Client 给你的服务器写单元测试

官方推荐做法（也是 SDK 自己的测试方式）：

    from mcp import Client
    from server import mcp

    @pytest.mark.anyio
    async def test_add() -> None:
        async with Client(mcp) as client:
            result = await client.call_tool("add", {"a": 1, "b": 2})
            assert result.structured_content == {"result": 3}

没有子进程、没有端口、没有传输层 —— `Client(mcp)` 直接连服务器对象。

本文件有两种运行方式：
  1) 装了 pytest：
        .\.venv\Scripts\python.exe -m pip install pytest anyio inline-snapshot
        .\.venv\Scripts\python.exe -m pytest "08_测试与pytest.py" -v
  2) 没装 pytest（默认）：
        .\.venv\Scripts\python.exe "08_测试与pytest.py"
     文件底部的 __main__ 里有一个极简测试运行器，直接跑同样的用例。

小技巧：debug 断言失败时，先打印整个结果的 model_dump()，
       这样你能看到 content / structured_content / is_error 的真实结构。
"""

from __future__ import annotations

import asyncio
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any

from mcp import Client
from mcp.server import MCPServer

HERE = Path(__file__).parent


# ---------------------------------------------------------------------------
# 0. 把 "02_最小服务器.py" 当模块加载（文件名是中文，普通 import 不行）
#    真实项目里你会写成 from server import mcp
# ---------------------------------------------------------------------------
def load_server_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("example_server", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["example_server"] = module
    spec.loader.exec_module(module)
    return module


server_module = load_server_module(HERE / "02_最小服务器.py")
mcp: MCPServer = server_module.mcp


# ---------------------------------------------------------------------------
# 1. 被测服务器（内联一份，保证文件自包含）
# ---------------------------------------------------------------------------
test_server = MCPServer("TestDemo")


@test_server.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@test_server.tool()
def divide(a: float, b: float = 1.0) -> float:
    """Divide a by b."""
    return a / b


@test_server.tool()
def get_weather(city: str) -> dict[str, Any]:
    """Return a weather report."""
    return {"city": city, "temperature": 23.5, "condition": "sunny"}


@test_server.resource("greeting://{name}")
def greeting(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"


@test_server.prompt()
def review(code: str) -> str:
    """Review a piece of code."""
    return f"请评审：{code}"


# ---------------------------------------------------------------------------
# 2. 测试用例（既能被 pytest 收集，也能被下面的简易运行器执行）
# ---------------------------------------------------------------------------
async def test_list_tools_has_add() -> None:
    async with Client(test_server) as client:
        result = await client.list_tools()
        names = [t.name for t in result.tools]
        assert "add" in names, names

        add_tool = next(t for t in result.tools if t.name == "add")
        # SDK 自动生成的 JSON Schema
        assert add_tool.input_schema["type"] == "object"
        assert add_tool.input_schema["required"] == ["a", "b"]
        assert add_tool.input_schema["properties"]["a"]["type"] == "integer"
        assert add_tool.description == "Add two numbers."


async def test_call_add_returns_structured_content() -> None:
    async with Client(test_server) as client:
        result = await client.call_tool("add", {"a": 1, "b": 2})
        assert result.is_error is False
        assert result.structured_content == {"result": 3}
        assert result.content[0].text == "3"


async def test_default_argument_is_optional() -> None:
    async with Client(test_server) as client:
        # b 有默认值 1.0，可以不传
        result = await client.call_tool("divide", {"a": 9})
        assert result.structured_content == {"result": 9.0}


async def test_type_validation_rejects_bad_arguments() -> None:
    async with Client(test_server) as client:
        result = await client.call_tool("add", {"a": "not-a-number", "b": 2})
        # pydantic 校验失败 -> is_error=True，而不是抛异常
        assert result.is_error is True
        assert "validation error" in result.content[0].text


async def test_pydantic_model_return() -> None:
    async with Client(test_server) as client:
        result = await client.call_tool("get_weather", {"city": "北京"})
        assert result.structured_content == {
            "city": "北京",
            "temperature": 23.5,
            "condition": "sunny",
        }
        # 结构化内容同时也会被序列化进 content（方便模型直接读）
        assert "北京" in result.content[0].text


async def test_read_resource_template() -> None:
    async with Client(test_server) as client:
        result = await client.read_resource("greeting://World")
        assert result.contents[0].text == "Hello, World!"
        assert result.contents[0].mime_type == "text/plain"


async def test_get_prompt() -> None:
    async with Client(test_server) as client:
        result = await client.get_prompt("review", {"code": "print(1)"})
        assert result.messages[0].role == "user"
        assert "print(1)" in result.messages[0].content.text


async def test_tool_error_message_is_preserved() -> None:
    """ToolError 的消息会**原样**传给客户端；其它异常会被吞成一句话。"""
    from mcp.server.mcpserver.exceptions import ToolError

    @test_server.tool()
    def read_note(path: str) -> str:
        """Read a note by name."""
        if path != "ok.txt":
            raise ToolError(f"文件 {path!r} 不存在")
        return "hello"

    async with Client(test_server) as client:
        bad = await client.call_tool("read_note", {"path": "bad.txt"})
        assert bad.is_error is True
        assert "不存在" in bad.content[0].text, bad.content[0].text

        good = await client.call_tool("read_note", {"path": "ok.txt"})
        assert good.is_error is False
        assert good.content[0].text == "hello"


async def test_uncaught_exception_hides_details() -> None:
    """未捕获异常同样是 is_error=True，但细节被吞掉（只留在服务器日志里）。"""

    @test_server.tool()
    def crashes() -> str:
        """Always raises an uncaught error."""
        raise RuntimeError("敏感的内部细节")

    async with Client(test_server) as client:
        result = await client.call_tool("crashes", {})
        assert result.is_error is True
        # 模型看不到 "敏感的内部细节"，只能看到这句模板化的错误
        assert "敏感的内部细节" not in result.content[0].text
        assert "crashes" in result.content[0].text


# 关于 raise_exceptions=True 的实测说明：
#   在 SDK 2.2.0 中，Client(..., raise_exceptions=True) 对**工具执行错误**没有影响，
#   两种模式下 call_tool 都返回 is_error=True 的结果（不抛异常）。
#   它主要影响连接期/协议层的错误。所以别指望用它来"让测试更快失败"，
#   断言 is_error 才是可靠做法。


async def test_the_example_server_from_02() -> None:
    """顺手验证 02_最小服务器.py 真的能用。"""
    async with Client(mcp) as client:
        result = await client.call_tool("add", {"a": 1, "b": 2})
        assert result.structured_content == {"result": 3}
        greeting_result = await client.read_resource("greeting://测试")
        assert greeting_result.contents[0].text == "Hello, 测试!"


# ---------------------------------------------------------------------------
# 3. pytest 专属：fixture 写法（装了 pytest 才会用到）
# ---------------------------------------------------------------------------
try:
    import pytest

    @pytest.fixture
    def anyio_backend() -> str:
        return "asyncio"

    @pytest.fixture
    async def client():
        async with Client(test_server, raise_exceptions=True) as c:
            yield c

    @pytest.mark.anyio
    async def test_with_fixture(client: Client) -> None:
        result = await client.call_tool("add", {"a": 20, "b": 22})
        assert result.structured_content == {"result": 42}

except ImportError:  # 没装 pytest 也能正常 import 本文件
    pytest = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# 4. 极简测试运行器（不依赖 pytest）
# ---------------------------------------------------------------------------
async def run_all() -> int:
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and asyncio.iscoroutinefunction(obj) and name != "test_with_fixture"
    ]
    passed, failed = 0, 0
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
    return 1 if failed else 0


if __name__ == "__main__":
    print("=" * 72)
    print("测试 MCP 服务器（内置运行器）")
    print("=" * 72)
    code = asyncio.run(run_all())
    print()
    print("装了 pytest 之后可以这样跑：")
    print('  .\\.venv\\Scripts\\python.exe -m pip install pytest anyio inline-snapshot')
    print('  .\\.venv\\Scripts\\python.exe -m pytest "08_测试与pytest.py" -v')
    sys.exit(code)
