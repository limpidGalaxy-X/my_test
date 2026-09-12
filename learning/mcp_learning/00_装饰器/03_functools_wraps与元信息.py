"""
03 - functools.wraps：别把被装饰函数的"身份证"弄丢

上一节的 timer 装饰器虽然能用，但有一个严重副作用：
被装饰后，函数的 __name__ / __doc__ / __annotations__ 全变成了 wrapper 的。

这在教学 demo 里无所谓，在真实框架里是灾难：
  * 文档工具（help / Sphinx）看到的所有函数都叫 wrapper
  * MCP / FastAPI 这类框架靠 __name__ + __doc__ + 类型注解生成工具描述和 JSON Schema，
    没有 wraps 就生成不出正确的 schema
  * 调试时调用栈里全是 wrapper，定位不到代码

functools.wraps 就是解决这个问题的标准做法。

运行：
    python "03_functools_wraps与元信息.py"
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable

# ---------------------------------------------------------------------------
# 1. 不写 wraps 会坏成什么样
# ---------------------------------------------------------------------------


def naive_timer(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


def proper_timer(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)          # <-- 就这一行
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


@naive_timer
def divide(a: float, b: float) -> float:
    """把 a 除以 b。"""
    return a / b


@proper_timer
def multiply(a: float, b: float) -> float:
    """把 a 乘以 b。"""
    return a * b


def demo_01_why() -> None:
    print(f"{'':10}{'__name__':<12}{'__doc__':<14}{'签名'}")
    print(f"{'naive':10}{divide.__name__:<12}{str(divide.__doc__):<14}{inspect.signature(divide)}")
    print(f"{'wraps':10}{multiply.__name__:<12}{str(multiply.__doc__):<14}{inspect.signature(multiply)}")
    print()
    print("naive 的签名被解析成了 (*args, **kwargs) —— 框架拿不到参数信息，")
    print("自然也就生成不出正确的 JSON Schema（MCP 工具调用会直接失效）。")


# ---------------------------------------------------------------------------
# 2. wraps 到底做了哪几件事
# ---------------------------------------------------------------------------


def demo_02_what_wraps_does() -> None:
    print("functools.WRAPPER_ASSIGNMENTS =", functools.WRAPPER_ASSIGNMENTS)
    print("functools.WRAPPER_UPDATES      =", functools.WRAPPER_UPDATES)
    print()

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return multiply(*args, **kwargs)

    functools.update_wrapper(wrapper, multiply)   # wraps 内部调用的就是这个
    print("update_wrapper 之后 wrapper.__name__      =", wrapper.__name__)
    print("update_wrapper 之后 wrapper.__wrapped__   =", wrapper.__wrapped__)
    print("于是 inspect.signature 会顺着 __wrapped__ 找到原函数:")
    print("   inspect.signature(wrapper) =", inspect.signature(wrapper))
    print("   inspect.unwrap(wrapper)    =", inspect.unwrap(wrapper).__name__)


# ---------------------------------------------------------------------------
# 3. __wrapped__ 链与多层装饰
# ---------------------------------------------------------------------------


def add_bang(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs) + "!"
    return wrapper


def add_question(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs) + "?"
    return wrapper


# 装饰顺序：先 add_bang 包住原函数，再 add_question 包住外层
# 所以调用是 question -> bang -> 原函数，结果是 "hi!?"
@add_question
@add_bang
def say(text: str) -> str:
    return text


def demo_03_chain() -> None:
    print("say('hi') =", say("hi"))
    print("名字穿透两层仍是:", say.__name__)
    print("__wrapped__ 链:")
    node: Any = say
    while hasattr(node, "__wrapped__"):
        print("   ", node.__name__, "->", node.__wrapped__.__name__)
        node = node.__wrapped__
    print("    最底层:", node.__name__)


# ---------------------------------------------------------------------------
# 4. 保留自定义属性（框架经常往函数上挂东西）
# ---------------------------------------------------------------------------

def register(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    # wraps 会复制 __dict__，但如果你在 wraps 之后才挂属性，就没有这个问题
    wrapper.tool_name = func.__name__      # type: ignore[attr-defined]
    return wrapper


@register
def search_docs(keyword: str, limit: int = 10) -> list[str]:
    """搜索文档。"""
    return [f"{keyword}-{i}" for i in range(limit)]


def demo_04_extra_attrs() -> None:
    print("tool_name 属性:", search_docs.tool_name)          # type: ignore[attr-defined]
    print("__doc__ 仍然保留:", search_docs.__doc__)
    print("__dict__:", search_docs.__dict__)


if __name__ == "__main__":
    for title, fn in [
        ("1. 不写 wraps 的后果", demo_01_why),
        ("2. wraps 内部做了什么", demo_02_what_wraps_does),
        ("3. __wrapped__ 链", demo_03_chain),
        ("4. 自定义属性", demo_04_extra_attrs),
    ]:
        print("=" * 70)
        print(title)
        print("=" * 70)
        fn()
        print()
