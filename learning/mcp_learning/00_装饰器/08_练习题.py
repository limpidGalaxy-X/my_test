"""
08 - 练习题（先自己写，再看 09_练习题参考答案.py）

每题都有 TODO。实现完之后运行：

    python "08_练习题.py"

就会跑一遍自测并给出 PASS / FAIL。没实现的题会提示 "还没实现"。
参考答案在 09_练习题参考答案.py —— 但请先自己写 10 分钟，效果完全不同。

运行：
    python "08_练习题.py"
"""

from __future__ import annotations

from typing import Any, Callable

# ---------------------------------------------------------------------------
# 练习 1：@debug 装饰器
#   打印 "调用 <函数名>(<位置参数>, <关键字参数>)"，然后返回原函数结果。
#   要求用 functools.wraps 保留元信息。
# ---------------------------------------------------------------------------

# TODO: 在这里定义 debug


# ---------------------------------------------------------------------------
# 练习 2：带参数的 @repeat_n(n, collect=True)
#   n 为重复次数；collect=True 返回结果列表，False 返回最后一次的结果。
# ---------------------------------------------------------------------------

# TODO: 在这里定义 repeat_n


# ---------------------------------------------------------------------------
# 练习 3：@cache_result
#   用字典缓存 (args, kwargs) -> 结果，相同参数复用缓存，不重复执行函数。
#   提示：把 kwargs 排序后转成 tuple 才能当字典的 key。
# ---------------------------------------------------------------------------

# TODO: 在这里定义 cache_result


# ---------------------------------------------------------------------------
# 练习 4：@validate_types
#   按类型注解检查实参，不符抛 TypeError。
#   提示：typing.get_type_hints(func)、inspect.signature(func)、isinstance。
#   注意：不要检查名为 ctx 的参数，也不要检查返回值。
# ---------------------------------------------------------------------------

# TODO: 在这里定义 validate_types


# ---------------------------------------------------------------------------
# 练习 5：@tool 注册表（MCP 味道）
#   实现 ToolRegistry 类：
#     - tool(name=None)  装饰器方法，登记到 self.tools（保持登记顺序）
#     - describe()       返回 [{"name":..., "description":..., "parameters":[参数名...]}]
#     - call(name, **kwargs)  按名字调用，未注册抛 KeyError
#   描述取 docstring（strip 后）。parameters 为位置参数名（跳过 self/cls/ctx）。
# ---------------------------------------------------------------------------

# TODO: 在这里定义 ToolRegistry


# ===========================================================================
# 以下为自测代码：不要修改
# ===========================================================================

_calls = {"n": 0}


def _build_cases() -> dict[str, Any]:
    """在这里定义被装饰的示例函数。如果练习还没实现，会抛 NameError。"""

    @debug                                            # noqa: F821
    def add(a: int, b: int = 1) -> int:
        return a + b

    @repeat_n(3)                                      # noqa: F821
    def greet(name: str) -> str:
        return f"hi {name}"

    @repeat_n(2, collect=False)                       # noqa: F821
    def last_only(x: int) -> int:
        return x * 10

    @cache_result                                     # noqa: F821
    def expensive(x: int) -> int:
        _calls["n"] += 1
        return x * x

    @validate_types                                   # noqa: F821
    def takes_int(x: int, name: str = "a") -> str:
        return f"{x}-{name}"

    registry = ToolRegistry()                         # noqa: F821

    @registry.tool()
    def echo(text: str) -> str:
        """回显文本。"""
        return text

    @registry.tool(name="sum_all")
    def total(numbers: list[int]) -> int:
        """求和。"""
        return sum(numbers)

    return {
        "add": add, "greet": greet, "last_only": last_only,
        "expensive": expensive, "takes_int": takes_int, "registry": registry,
    }


def run_tests() -> None:
    try:
        c = _build_cases()
    except NameError as exc:
        print(f"[待完成] 还没实现：{exc}")
        print("   请先完成 08 文件顶部的 5 个 TODO，然后重新运行。")
        return

    failures: list[str] = []

    def check(label: str, condition: bool, extra: str = "") -> None:
        print(f"  [{'PASS' if condition else 'FAIL'}] {label} {extra if not condition else ''}")
        if not condition:
            failures.append(label)

    check("1 debug 返回值正确", c["add"](1) == 2)
    check("1 debug 保留函数名", getattr(c["add"], "__name__", "") == "add",
          f"实际 {getattr(c['add'], '__name__', None)!r}")

    check("2 repeat_n collect=True", c["greet"]("tom") == ["hi tom"] * 3)
    check("2 repeat_n collect=False", c["last_only"](3) == 30)

    first, second = c["expensive"](4), c["expensive"](4)
    check("3 缓存命中只执行一次", _calls["n"] == 1, f"实际执行 {_calls['n']} 次")
    check("3 缓存结果正确", first == second == 16)

    check("4 类型正确可通过", c["takes_int"](1) == "1-a")
    try:
        c["takes_int"]("not-int")
        check("4 类型错误应抛 TypeError", False)
    except TypeError:
        check("4 类型错误应抛 TypeError", True)

    check("5 describe 内容", c["registry"].describe() == [
        {"name": "echo", "description": "回显文本。", "parameters": ["text"]},
        {"name": "sum_all", "description": "求和。", "parameters": ["numbers"]},
    ], f"实际 {c['registry'].describe()}")
    check("5 call 正确", c["registry"].call("sum_all", numbers=[1, 2, 3]) == 6)

    print()
    if failures:
        print(f"[失败] {len(failures)} 项未通过：{failures}")
        raise SystemExit(1)
    print("[通过] 全部通过！去看 09_练习题参考答案.py 对照一下写法差异。")


if __name__ == "__main__":
    run_tests()
