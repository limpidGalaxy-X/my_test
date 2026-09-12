"""
09 - 练习题参考答案

先自己写完 08，再来看这里。每道题都给了「实现」+「要点说明」。
本文件可以直接运行，会跑完整套自测：

    python "09_练习题参考答案.py"
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, get_type_hints

# ===========================================================================
# 练习 1：@debug
# ===========================================================================


def debug(func: Callable[..., Any]) -> Callable[..., Any]:
    """要点：无参装饰器 = 两层；wrapper 必须转发并 return。"""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        rendered = ", ".join(
            [*(repr(a) for a in args), *(f"{k}={v!r}" for k, v in kwargs.items())]
        )
        print(f"  -> 调用 {func.__name__}({rendered})")
        result = func(*args, **kwargs)
        print(f"  <- {func.__name__} 返回 {result!r}")
        return result

    return wrapper


# ===========================================================================
# 练习 2：@repeat_n(n, collect=True)
# ===========================================================================


def repeat_n(n: int, collect: bool = True) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """要点：带参装饰器 = 三层；n 和 collect 被闭包记住。

    注意签名必须是 (n, collect=True) 而不是 (*args, **kwargs)，
    这样 @repeat_n(3) 和 @repeat_n(2, collect=False) 两种写法都能用。
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            results = [func(*args, **kwargs) for _ in range(n)]
            return results if collect else results[-1]

        return wrapper

    return decorator


# ===========================================================================
# 练习 3：@cache_result
# ===========================================================================


def cache_result(func: Callable[..., Any]) -> Callable[..., Any]:
    """要点：
    * 缓存字典放在装饰器闭包里（每个被装饰函数一份）；
    * kwargs 顺序不固定，必须排序后转 tuple 才能当 key；
    * 不想让调用方看见 cache 属性的话，可以不用 functools.wraps 的 __dict__ 更新。
    """
    cache: dict[tuple[Any, ...], Any] = {}

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        key = (args, tuple(sorted(kwargs.items())))
        if key not in cache:
            print(f"  [cache MISS] {func.__name__}{args}")
            cache[key] = func(*args, **kwargs)
        else:
            print(f"  [cache HIT ] {func.__name__}{args}")
        return cache[key]

    wrapper.cache = cache              # type: ignore[attr-defined]
    wrapper.cache_clear = cache.clear  # type: ignore[attr-defined]
    return wrapper


# ===========================================================================
# 练习 4：@validate_types
# ===========================================================================


def validate_types(func: Callable[..., Any]) -> Callable[..., Any]:
    """要点：用 get_type_hints 解析注解，用 signature 把实参绑定成名字 -> 值。"""

    hints = get_type_hints(func)
    sig = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        for name, value in bound.arguments.items():
            if name in ("self", "cls", "ctx"):
                continue
            expected = hints.get(name)
            if expected is None or value is None:
                continue
            if not isinstance(value, expected):
                raise TypeError(
                    f"{func.__name__}() 参数 {name!r} 期望 {expected}, 实际 {type(value).__name__}"
                )
        return func(*args, **kwargs)

    return wrapper


# ===========================================================================
# 练习 5：ToolRegistry
# ===========================================================================


class ToolRegistry:
    """要点：装饰器方法 = 实例方法返回 decorator；用 dict 保序（Python 3.7+）。"""

    def __init__(self) -> None:
        self.tools: dict[str, dict[str, Any]] = {}

    def tool(self, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            tool_name = name or func.__name__
            self.tools[tool_name] = {
                "name": tool_name,
                "description": (func.__doc__ or "").strip(),
                "parameters": [
                    p.name
                    for p in inspect.signature(func).parameters.values()
                    if p.name not in ("self", "cls", "ctx")
                    and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
                ],
                "handler": func,
            }
            return func

        return decorator

    def describe(self) -> list[dict[str, Any]]:
        return [
            {k: v for k, v in tool.items() if k != "handler"}
            for tool in self.tools.values()
        ]

    def call(self, name: str, **kwargs: Any) -> Any:
        if name not in self.tools:
            raise KeyError(f"未注册的工具: {name}")
        return self.tools[name]["handler"](**kwargs)


# ===========================================================================
# 自测（与 08 一致，装饰器换成上面的实现）
# ===========================================================================

_calls = {"n": 0}


@debug
def add(a: int, b: int = 1) -> int:
    return a + b


@repeat_n(3)
def greet(name: str) -> str:
    return f"hi {name}"


@repeat_n(2, collect=False)
def last_only(x: int) -> int:
    return x * 10


@cache_result
def expensive(x: int) -> int:
    _calls["n"] += 1
    return x * x


@validate_types
def takes_int(x: int, name: str = "a") -> str:
    return f"{x}-{name}"


registry = ToolRegistry()


@registry.tool()
def echo(text: str) -> str:
    """回显文本。"""
    return text


@registry.tool(name="sum_all")
def total(numbers: list[int]) -> int:
    """求和。"""
    return sum(numbers)


def run_tests() -> None:
    failures: list[str] = []

    def check(label: str, condition: bool, extra: str = "") -> None:
        print(f"  [{'PASS' if condition else 'FAIL'}] {label} {extra if not condition else ''}")
        if not condition:
            failures.append(label)

    print("自测开始（注意 debug / cache_result 打印的中间输出）")
    check("1 debug 返回值正确", add(1) == 2)
    check("1 debug 保留函数名", add.__name__ == "add")

    check("2 repeat_n collect=True", greet("tom") == ["hi tom"] * 3)
    check("2 repeat_n collect=False", last_only(3) == 30)

    first, second = expensive(4), expensive(4)
    check("3 缓存命中只执行一次", _calls["n"] == 1, f"实际执行 {_calls['n']} 次")
    check("3 缓存结果正确", first == second == 16)

    check("4 类型正确可通过", takes_int(1) == "1-a")
    try:
        takes_int("not-int")           # type: ignore[arg-type]
        check("4 类型错误应抛 TypeError", False)
    except TypeError as exc:
        print(f"  [预期 TypeError] {exc}")
        check("4 类型错误应抛 TypeError", True)

    check("5 describe 内容", registry.describe() == [
        {"name": "echo", "description": "回显文本。", "parameters": ["text"]},
        {"name": "sum_all", "description": "求和。", "parameters": ["numbers"]},
    ], f"实际 {registry.describe()}")
    check("5 call 正确", registry.call("sum_all", numbers=[1, 2, 3]) == 6)

    print()
    if failures:
        print(f"[失败] {len(failures)} 项未通过：{failures}")
        raise SystemExit(1)
    print("[通过] 全部通过。")


if __name__ == "__main__":
    run_tests()
