"""
04 - 带参数的装饰器（装饰器工厂）

@timer             -> 装饰器
@repeat(3)         -> 先调用 repeat(3)，拿到的返回值才是装饰器

所以"带参数的装饰器"其实是三层结构：

    def repeat(times):                      # 第 1 层：收装饰器参数
        def decorator(func):                # 第 2 层：收被装饰的函数
            @functools.wraps(func)
            def wrapper(*args, **kwargs):   # 第 3 层：收调用参数
                ...
            return wrapper
        return decorator

MCP 里的 @mcp.tool(name=..., description=...) 就是这种结构。

运行：
    python "04_带参数的装饰器.py"
"""

from __future__ import annotations

import functools
import time
from typing import Any, Callable

# ---------------------------------------------------------------------------
# 1. 最简单的三层装饰器
# ---------------------------------------------------------------------------


def repeat(times: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """把函数重复执行 times 次，返回结果的列表。"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> list[Any]:
            return [func(*args, **kwargs) for _ in range(times)]

        wrapper.times = times            # type: ignore[attr-defined]
        return wrapper

    return decorator


@repeat(3)
def shout(text: str) -> str:
    """把文字变成大写并加感叹号。"""
    return text.upper() + "!"


def demo_01_repeat() -> None:
    print("shout('hi') =", shout("hi"))
    print("shout.__name__ =", shout.__name__, " times =", shout.times)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. 更实用的例子：retry
# ---------------------------------------------------------------------------


def retry(
    times: int = 3,
    delay: float = 0.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """失败自动重试。可配置次数、间隔、要捕获的异常类型。"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last: BaseException | None = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last = exc
                    print(f"    [retry] {func.__name__} 第 {attempt}/{times} 次失败: {exc!r}")
                    if attempt < times and delay:
                        time.sleep(delay)
            raise last  # type: ignore[misc]

        return wrapper

    return decorator


_attempts = {"n": 0}


@retry(times=4, delay=0.01, exceptions=(ValueError,))
def unstable() -> str:
    _attempts["n"] += 1
    if _attempts["n"] < 3:
        raise ValueError(f"模拟故障 {_attempts['n']}")
    return f"第 {_attempts['n']} 次成功"


def demo_02_retry() -> None:
    print("结果:", unstable())
    print("注意：只有 ValueError 会被重试，其它异常会直接抛出。")


# ---------------------------------------------------------------------------
# 3. 可以"带参也可以不带参"的装饰器
# ---------------------------------------------------------------------------

def logged(
    _func: Callable[..., Any] | None = None,
    *,
    level: str = "INFO",
) -> Any:
    """
    同时支持两种写法：

        @logged
        def f(): ...

        @logged(level="DEBUG")
        def g(): ...

    技巧：把第一个位置参数留给"被装饰的函数本身"。
    如果它是可调用的，说明用户写的是 @logged 这种不带参形式，立刻装饰。
    否则说明用户写的是 @logged(level=...)，返回真正的装饰器。
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            print(f"    [{level}] -> {func.__name__}{args}")
            result = func(*args, **kwargs)
            print(f"    [{level}] <- {func.__name__} 返回 {result!r}")
            return result

        return wrapper

    if _func is not None:          # 不带参写法：@logged
        return decorator(_func)
    return decorator               # 带参写法：@logged(level="DEBUG")


@logged
def free_style(x: int) -> int:
    return x * 2


@logged(level="DEBUG")
def configured(x: int) -> int:
    return x + 1


def demo_03_optional_args() -> None:
    print("free_style(21) =", free_style(21))
    print("configured(41) =", configured(41))


# ---------------------------------------------------------------------------
# 4. 两个必须记住的坑
# ---------------------------------------------------------------------------

def must_be_called(times: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> list[Any]:
            return [func(*args, **kwargs) for _ in range(times)]

        return wrapper

    return decorator


# 坑 1：忘了写括号，把"装饰器工厂"当成了装饰器
@must_be_called            # type: ignore[arg-type]  # 少写了 () ；times 收到的是函数对象
def oops(text: str) -> str:
    return text


def demo_04_pitfalls() -> None:
    print("坑 1：@must_be_called 少写括号时，times 变成了函数对象：")
    print("   oops 现在是什么:", oops)
    try:
        oops("x")          # type: ignore[operator]
    except TypeError as exc:
        print("   调用时报错:", exc)
    print("   -> 带参数的装饰器几乎总是要写成 @deco(...)，加括号更安全。")

    print()
    print("坑 2：在 wrapper 里用错了绑定时机（经典闭包陷阱）")
    funcs = []
    for i in range(3):
        funcs.append(lambda: i)          # 晚绑定：都读到最后的 i
    print("   晚绑定:", [f() for f in funcs])
    funcs2 = []
    for i in range(3):
        funcs2.append(lambda i=i: i)     # 默认参数：立刻绑定
    print("   默认参数绑定:", [f() for f in funcs2])


if __name__ == "__main__":
    for title, fn in [
        ("1. 三层结构：repeat(3)", demo_01_repeat),
        ("2. 可配置的 retry", demo_02_retry),
        ("3. 带参/不带参两用", demo_03_optional_args),
        ("4. 常见坑", demo_04_pitfalls),
    ]:
        print("=" * 70)
        print(title)
        print("=" * 70)
        fn()
        print()
