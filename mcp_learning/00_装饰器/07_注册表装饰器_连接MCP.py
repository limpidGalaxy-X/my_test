"""
07 - 注册表装饰器：MCP 的魔法其实都在这里

学到这里，你已经具备看懂 MCP 装饰器的全部前置知识了。

先看 MCP 的写法（Python SDK）：

    from mcp.server import MCPServer
    mcp = MCPServer("Demo")

    @mcp.tool()                       # 带参数的装饰器工厂
    def add(a: int, b: int) -> int:
        "Add two numbers."
        return a + b

这三行到底发生了什么？
  1) mcp.tool() 返回一个 decorator；
  2) decorator 拿到函数 add；
  3) 从 add 的类型注解生成 JSON Schema {"a": "integer", "b": "integer"}；
  4) 从 add 的 docstring 取描述；
  5) 把 (name, schema, handler) 存进 mcp 内部的注册表；
  6) 客户端调 tools/list 时返回注册表内容，调 tools/call 时按名字找到函数执行。

本文件用纯标准库实现一个 40 行的迷你版，跑通同样的流程。
真正做到"不安装任何东西也能看懂 MCP 在干什么"。

运行：
    python "07_注册表装饰器_连接MCP.py"
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import json
from typing import Any, Callable, get_args, get_origin, get_type_hints

# ---------------------------------------------------------------------------
# 1. 类型注解 -> JSON Schema（MCP 的 inputSchema 就是这么来的）
# ---------------------------------------------------------------------------

# Python 类型 -> JSON Schema 类型
PRIMITIVE_MAP: dict[Any, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "null",
}


def type_to_schema(annotation: Any) -> dict[str, Any]:
    """把 Python 类型注解翻译成 JSON Schema 片段（简化版，够用即可）。"""
    if annotation is inspect.Parameter.empty or annotation is Any:
        return {}

    origin = get_origin(annotation)

    # Optional[X] / X | None  ->  {"anyOf": [...]}（这里简化为直接取 X）
    if origin is not None and str(origin).endswith("Union"):
        non_none = [a for a in get_args(annotation) if a is not type(None)]
        if len(non_none) == 1:
            return type_to_schema(non_none[0])
        return {"anyOf": [type_to_schema(a) for a in non_none]}

    # list[str] / list[int]
    if origin is list:
        args = get_args(annotation)
        items = type_to_schema(args[0]) if args else {}
        return {"type": "array", "items": items}

    # dict[str, int]
    if origin is dict:
        return {"type": "object"}

    # 普通类型
    if annotation in PRIMITIVE_MAP:
        return {"type": PRIMITIVE_MAP[annotation]}

    # 枚举
    if inspect.isclass(annotation):
        import enum
        if issubclass(annotation, enum.Enum):
            return {"type": "string", "enum": [m.value for m in annotation]}

    # 兜底：交给 pydantic 的话会生成 $defs/嵌套 model，这里只标 object
    return {"type": "object"}


def build_input_schema(func: Callable[..., Any]) -> dict[str, Any]:
    """根据函数签名生成 MCP 风格的 inputSchema。"""
    sig = inspect.signature(func)
    hints = get_type_hints(func)         # 会解析 from __future__ import annotations 的字符串注解
    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if name == "ctx":                # MCP 里 Context 参数不会出现在 schema 中
            continue

        schema = type_to_schema(hints.get(name, param.annotation))
        if param.default is not inspect.Parameter.empty:
            schema = {**schema, "default": param.default}
        else:
            required.append(name)
        properties[name] = schema

    result: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        result["required"] = required
    return result


def build_output_schema(func: Callable[..., Any]) -> dict[str, Any] | None:
    """返回注解 -> outputSchema。"""
    hints = get_type_hints(func)
    if "return" not in hints or hints["return"] is type(None):
        return None
    return build_input_schema.__wrapped__ if False else _schema_of_return(hints["return"])


def _schema_of_return(annotation: Any) -> dict[str, Any]:
    origin = get_origin(annotation)
    if origin is None and annotation in (str, int, float, bool):
        return type_to_schema(annotation)
    if origin is dict or annotation is dict:
        return {"type": "object"}
    return type_to_schema(annotation)


# ---------------------------------------------------------------------------
# 2. 迷你 MCP 服务器：装饰器 + 注册表
# ---------------------------------------------------------------------------

class MiniMCPServer:
    """把 MCP 的核心机制浓缩到 40 行。"""

    def __init__(self, name: str) -> None:
        self.name = name
        self.tools: dict[str, dict[str, Any]] = {}       # 注册表

    def tool(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """带参数的装饰器工厂 —— 和 @mcp.tool() 结构完全一致。"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            tool_name = name or func.__name__
            schema = build_input_schema(func)
            self.tools[tool_name] = {
                "name": tool_name,
                "description": description or (func.__doc__ or "").strip(),
                "inputSchema": schema,
                "outputSchema": build_output_schema(func),
                "handler": func,
                "is_async": inspect.iscoroutinefunction(func),
            }
            # 返回原函数（保持可调用），同时把名字挂上去方便调试
            wrapper = func
            wrapper.tool_name = tool_name            # type: ignore[attr-defined]
            return wrapper

        return decorator

    # ---- 模拟协议方法 -------------------------------------------------

    def list_tools(self) -> list[dict[str, Any]]:
        """相当于 MCP 的 tools/list。"""
        return [
            {k: v for k, v in tool.items() if k not in ("handler", "is_async")}
            for tool in self.tools.values()
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """相当于 MCP 的 tools/call（同步简化版）。"""
        if name not in self.tools:
            raise KeyError(f"MCP error -32602: Unknown tool: {name}")
        tool = self.tools[name]
        result = tool["handler"](**arguments)        # 参数校验由 pydantic 负责，这里直接透传
        if tool["is_async"]:
            return asyncio.run(result)
        return result


# ---------------------------------------------------------------------------
# 3. 用这个迷你框架写一个"服务器"
# ---------------------------------------------------------------------------

import enum


class Unit(enum.Enum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


server = MiniMCPServer("WeatherDemo")


@server.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@server.tool(description="查询某个城市的天气")
def get_weather(city: str, unit: Unit = Unit.CELSIUS, detailed: bool = False) -> dict[str, Any]:
    """Get weather for a city."""
    data = {"city": city, "temp": 23, "unit": unit.value}
    if detailed:
        data["humidity"] = 55
    return data


@server.tool(name="search_docs")
def search(keyword: str, limit: int = 5) -> list[str]:
    """Search the documentation."""
    return [f"{keyword} #{i}" for i in range(1, limit + 1)]


@server.tool()
async def slow_echo(text: str) -> str:
    """Echo text asynchronously."""
    await asyncio.sleep(0.01)
    return text


def demo_01_list_tools() -> None:
    print("模拟客户端发送 tools/list，服务器返回：")
    print(json.dumps(server.list_tools(), ensure_ascii=False, indent=2, default=str))


def demo_02_call_tools() -> None:
    print("模拟 tools/call：")
    print("  add(a=1, b=2)              ->", server.call_tool("add", {"a": 1, "b": 2}))
    print("  get_weather(city='北京')    ->",
          server.call_tool("get_weather", {"city": "北京"}))
    print("  get_weather(unit=celsius)  ->",
          server.call_tool("get_weather", {"city": "上海", "unit": Unit.FAHRENHEIT, "detailed": True}))
    print("  search_docs(kw='mcp')      ->",
          server.call_tool("search_docs", {"keyword": "mcp", "limit": 3}))
    print("  slow_echo(text='hi')       ->",
          server.call_tool("slow_echo", {"text": "hi"}))


def demo_03_what_you_just_built() -> None:
    print("你刚刚实现的东西，和真正的 MCP SDK 一一对应：")
    mapping = [
        ("MiniMCPServer('WeatherDemo')", "MCPServer('WeatherDemo')"),
        ("@server.tool()", "@mcp.tool()"),
        ("server.tools 注册表", "server 内部 _tool_manager"),
        ("list_tools()", "tools/list"),
        ("call_tool(name, args)", "tools/call"),
        ("build_input_schema()", "pydantic 的 model_json_schema()"),
    ]
    for mine, real in mapping:
        print(f"    {mine:<32} <->  {real}")
    print()
    print("结论：MCP 的装饰器没有任何黑魔法，就是")
    print("   『装饰器收参数 -> 反射签名 -> 生成 schema -> 存进注册表 -> 按名字派发』")


if __name__ == "__main__":
    for title, fn in [
        ("1. tools/list 的返回内容", demo_01_list_tools),
        ("2. tools/call 的调用过程", demo_02_call_tools),
        ("3. 从迷你实现映射到真正的 MCP", demo_03_what_you_just_built),
    ]:
        print("=" * 70)
        print(title)
        print("=" * 70)
        fn()
        print()
