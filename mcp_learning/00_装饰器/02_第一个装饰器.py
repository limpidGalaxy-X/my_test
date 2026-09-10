"""
02 - 第一个装饰器

装饰器 = 一个"接收函数、返回函数"的函数。
@deco 只是语法糖：

    @deco
    def f(): ...

完全等价于：

    def f(): ...
    f = deco(f)

记住三件事：
  1) 装饰发生在"函数定义时"（模块导入时），不是在调用时；
  2) 装饰器返回的东西会替换掉原来的名字；
  3) 所以被装饰后，f 这个名字指向的其实是 wrapper。

运行：
    python "02_第一个装饰器.py"
"""

from __future__ import annotations

import time
from typing import Any, Callable

# ---------------------------------------------------------------------------
# 1. 手写一个计时装饰器
# ---------------------------------------------------------------------------


def timer(func: Callable[..., Any]) -> Callable[..., Any]:
    """打印 func 的执行耗时。"""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)   # 用 *args/**kwargs 原样转发所有参数
        cost = (time.perf_counter() - start) * 1000
        print(f"    [timer] {func.__name__} 耗时 {cost:.2f} ms")
        return result

    return wrapper


@timer
def slow_add(a: int, b: int) -> int:
    """慢速加法。"""
    time.sleep(0.05)
    return a + b


def demo_01_sugar() -> None:
    print("调用 slow_add(1, 2) ->", slow_add(1, 2))

    # 等价写法（不使用语法糖）
    def raw_add(a: int, b: int) -> int:
        time.sleep(0.05)
        return a + b

    timed_raw_add = timer(raw_add)
    print("等价写法 timed_raw_add(1, 2) ->", timed_raw_add(1, 2))

    # 关键证据：slow_add 已经不是原来那个函数了
    print("slow_add 现在指向 :", slow_add)
    print("原始函数被保存在闭包里:", slow_add.__closure__[0].cell_contents)


# ---------------------------------------------------------------------------
# 2. 装饰时机 vs 调用时机
# ---------------------------------------------------------------------------

def trace(func: Callable[..., Any]) -> Callable[..., Any]:
    print(f"    >>> [定义期] 装饰器正在包装 {func.__name__}")

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"    >>> [调用期] 真正执行 {func.__name__}{args}")
        return func(*args, **kwargs)

    return wrapper


print("导入模块时就会打印这一行下面的内容（装饰发生在定义期）")


@trace
def hello(name: str) -> str:
    return f"hello {name}"


def demo_02_timing() -> None:
    print("现在才第一次调用 hello():")
    hello("world")
    print("再调用一次（不会再打印『定义期』）:")
    hello("again")


# ---------------------------------------------------------------------------
# 3. 装饰器是一种"横切关注点"的复用手段
# ---------------------------------------------------------------------------

def log_call(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"    [log] 调用 {func.__name__} args={args} kwargs={kwargs}")
        return func(*args, **kwargs)

    return wrapper


def with_retry(func: Callable[..., Any]) -> Callable[..., Any]:
    """极简重试：失败最多重试 3 次。"""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - 教学示例，故意抓宽
                last_error = exc
                print(f"    [retry] 第 {attempt} 次失败: {exc}")
        raise last_error  # type: ignore[misc]

    return wrapper


@log_call
@with_retry
def flaky(threshold: int) -> str:
    """前两次必然失败，第三次成功。"""
    flaky.calls += 1                     # type: ignore[attr-defined]
    if flaky.calls < threshold:          # type: ignore[attr-defined]
        raise RuntimeError(f"随机故障 #{flaky.calls}")  # type: ignore[attr-defined]
    return "成功！"


flaky.calls = 0  # type: ignore[attr-defined]


def demo_03_stacking() -> None:
    print("多个装饰器 = 从下往上包裹（洋葱模型）:")
    print("   flaky = log_call(with_retry(flaky))")
    print("结果:", flaky(3))


# ---------------------------------------------------------------------------
# 4. 反面教材：不转发参数 / 不保留返回值
# ---------------------------------------------------------------------------

def bad_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper() -> None:           # 没有 *args/**kwargs -> 只能装饰零参函数
        func()                       # 没有 return -> 吞掉了原函数返回值
    return wrapper


@bad_decorator
def add(a: int, b: int) -> int:
    return a + b


def demo_04_pitfall() -> None:
    try:
        add(1, 2)                    # type: ignore[call-arg]
    except TypeError as exc:
        print("    预期内的报错:", exc)
    print("    结论：wrapper 必须写成 (*args, **kwargs) 并且 return func(...)")


if __name__ == "__main__":
    for title, fn in [
        ("1. 语法糖与等价展开", demo_01_sugar),
        ("2. 装饰时机 ≠ 调用时机", demo_02_timing),
        ("3. 装饰器叠加（洋葱模型）", demo_03_stacking),
        ("4. 常见坑", demo_04_pitfall),
    ]:
        print("=" * 70)
        print(title)
        print("=" * 70)
        fn()
        print()
