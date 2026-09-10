"""
05 - 类装饰器 与 装饰类

"类装饰器"有两个完全不同的意思，别混：

  A. 用类做装饰器：类实现 __call__，实例就是可调用对象，可以当装饰器用。
     好处是能把"状态"存在实例属性上，比闭包更好读。

  B. 装饰一个类：@deco 放在 class 上面，收到的是类对象，
     可以在类上加方法/属性，或者返回一个全新的类。

MCP / FastAPI 这类框架通常用 (A) 来做"路由器"或"注册器"。

运行：
    python "05_类装饰器与方法装饰器.py"
"""

from __future__ import annotations

import functools
from typing import Any, Callable

# ---------------------------------------------------------------------------
# A. 用类做装饰器：把状态放进实例
# ---------------------------------------------------------------------------


class CountCalls:
    """统计被装饰函数被调用了几次（状态存在实例上，不依赖 nonlocal）。"""

    def __init__(self, func: Callable[..., Any]) -> None:
        functools.update_wrapper(self, func)   # 让实例看起来像那个函数
        self.func = func
        self.count = 0

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.count += 1
        print(f"    [CountCalls] {self.func.__name__} 第 {self.count} 次调用")
        return self.func(*args, **kwargs)


@CountCalls
def ping() -> str:
    return "pong"


def demo_a_stateful_class_decorator() -> None:
    ping()
    ping()
    ping()
    print("    统计结果 count =", ping.count)      # type: ignore[attr-defined]
    print("    __name__ 被 update_wrapper 保住了:", ping.__name__)  # type: ignore[attr-defined]


class RateLimit:
    """带参数的类装饰器：限制每秒调用次数（这里只打印提示，不真的阻塞）。"""

    def __init__(self, per_second: int) -> None:
        self.per_second = per_second

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        calls = 0

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal calls
            calls += 1
            print(f"    [RateLimit] {func.__name__} 第 {calls} 次调用，限额 {self.per_second}/s")
            return func(*args, **kwargs)

        return wrapper


@RateLimit(per_second=2)
def fetch(url: str) -> str:
    return f"<html of {url}>"


def demo_a_param_class_decorator() -> None:
    fetch("https://a.example")
    fetch("https://b.example")


# ---------------------------------------------------------------------------
# B. 装饰一个类
# ---------------------------------------------------------------------------


def add_repr(cls: type) -> type:
    """给类自动补一个 __repr__（演示：装饰器收到的是类对象）。"""

    def __repr__(self: Any) -> str:
        fields = ", ".join(f"{k}={v!r}" for k, v in vars(self).items())
        return f"{type(self).__name__}({fields})"

    cls.__repr__ = __repr__            # 直接改类
    return cls


@add_repr
class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


def singleton(cls: type) -> Callable[..., Any]:
    """把类替换成"永远返回同一个实例"的工厂函数（返回的不再是类）。"""
    instances: dict[type, Any] = {}

    @functools.wraps(cls, updated=())
    def get_instance(*args: Any, **kwargs: Any) -> Any:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class Config:
    def __init__(self) -> None:
        self.debug = True


def demo_b_decorate_class() -> None:
    print("    Point(1, 2) =", Point(1, 2))
    print("    Config() is Config() ?", Config() is Config())
    print("    Config 现在其实是函数:", type(Config))


# ---------------------------------------------------------------------------
# C. 装饰实例方法 / 类方法 / 静态方法
# ---------------------------------------------------------------------------


def require_positive(func: Callable[..., Any]) -> Callable[..., Any]:
    """装饰实例方法时，wrapper 收到的第一个参数就是 self，正常转发即可。"""

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        for value in args:
            if isinstance(value, (int, float)) and value <= 0:
                raise ValueError(f"{func.__name__} 只接受正数，收到 {value}")
        return func(self, *args, **kwargs)

    return wrapper


class Account:
    def __init__(self, balance: float = 0.0) -> None:
        self.balance = balance

    @require_positive
    def deposit(self, amount: float) -> float:
        self.balance += amount
        return self.balance

    @classmethod
    @require_positive                      # 顺序：先让 classmethod 包住被装饰的函数
    def open_with(cls, initial: float) -> "Account":
        return cls(initial)

    @staticmethod
    @require_positive
    def is_valid(amount: float) -> bool:
        return True


def demo_c_methods() -> None:
    acc = Account()
    print("    deposit(100) ->", acc.deposit(100))
    try:
        acc.deposit(-1)
    except ValueError as exc:
        print("    预期报错:", exc)
    print("    Account.open_with(50).balance =", Account.open_with(50).balance)

    print()
    print("    注意装饰顺序：")
    print("      @classmethod 必须写在最外层（最上面），否则装饰器拿到的")
    print("      只是 classmethod 描述符对象而不是函数，会直接报错。")


if __name__ == "__main__":
    for title, fn in [
        ("A1. 有状态的类装饰器", demo_a_stateful_class_decorator),
        ("A2. 带参数的类装饰器", demo_a_param_class_decorator),
        ("B.  装饰类本身", demo_b_decorate_class),
        ("C.  装饰方法", demo_c_methods),
    ]:
        print("=" * 70)
        print(title)
        print("=" * 70)
        fn()
        print()
