"""
01 - 函数是一等公民（First-class function）

装饰器（decorator）之所以能存在，只有一个原因：
    在 Python 里，函数本身也是"对象"。
可以赋值给变量、可以当参数传、可以当返回值返回、可以放进列表和字典。

只要理解了这一点，装饰器就不是魔法，只是"用函数加工函数"而已。

运行：
    python "01_函数是一等公民.py"
"""

from __future__ import annotations

import inspect


# ---------------------------------------------------------------------------
# 1. 函数可以被赋值、被传递、被返回
# ---------------------------------------------------------------------------

def greet(name: str) -> str:
    """打招呼。"""
    return f"你好，{name}！"


def demo_01_function_is_object() -> None:
    # (a) 赋值给变量：greet 和 say_hi 指向同一个函数对象
    say_hi = greet
    print("a) 赋值:", say_hi("小明"))
    print("   同一个对象吗?", say_hi is greet)

    # (b) 作为参数传递
    def call_twice(func, value):
        return func(value) + " | " + func(value)

    print("b) 作为参数:", call_twice(greet, "小红"))

    # (c) 作为返回值返回
    def pick(language: str):
        def py(name: str) -> str:
            return f"print('hi {name}')"

        def js(name: str) -> str:
            return f"console.log('hi {name}')"

        return py if language == "py" else js

    print("c) 作为返回值:", pick("js")("Tom"))

    # (d) 放进容器
    handlers = {"greet": greet, "shout": lambda n: f"{n}!!!".upper()}
    for key, handler in handlers.items():
        print(f"d) 容器里的函数 [{key}]:", handler("Bob"))


# ---------------------------------------------------------------------------
# 2. 函数对象身上带着哪些"元数据"
# ---------------------------------------------------------------------------

def demo_02_function_metadata() -> None:
    print("名称 __name__        :", greet.__name__)
    print("文档 __doc__         :", greet.__doc__)
    print("注解 __annotations__ :", greet.__annotations__)
    print("模块 __module__      :", greet.__module__)
    print("自定义属性 __dict__  :", greet.__dict__)

    # 函数对象是可以挂"自定义属性"的，这一点在 07 号文件里非常关键：
    # MCP 的 @mcp.tool() 就是给函数挂上描述信息后再收进注册表。
    greet.category = "social"          # type: ignore[attr-defined]
    greet.version = 1                  # type: ignore[attr-defined]
    print("挂上属性后 __dict__  :", greet.__dict__)
    del greet.category, greet.version

    # 签名（参数名、类型、默认值）可以被反射出来
    sig = inspect.signature(greet)
    print("签名 inspect.signature:", sig)
    for name, param in sig.parameters.items():
        print(f"  参数 {name!r}: 注解={param.annotation!r} 默认值={param.default!r}")


# ---------------------------------------------------------------------------
# 3. 闭包：装饰器"记住"东西的唯一手段
# ---------------------------------------------------------------------------

def make_counter() -> "callable":
    """外层函数的局部变量 count 被内层函数记住 -> 闭包。"""

    count = 0

    def inner() -> int:
        nonlocal count  # 声明我要改的是外层变量，而不是新建一个
        count += 1
        return count

    return inner


def demo_03_closure() -> None:
    c1 = make_counter()
    c2 = make_counter()  # 每次调用 make_counter 都会得到独立的一份 count
    print("闭包 c1:", c1(), c1(), c1())
    print("闭包 c2:", c2())

    # 闭包保存的东西放在 __closure__ 里
    names = c1.__code__.co_freevars
    values = [cell.cell_contents for cell in (c1.__closure__ or ())]
    print("自由变量:", dict(zip(names, values)))


# ---------------------------------------------------------------------------
# 4. 手动包装一次函数：装饰器的雏形
# ---------------------------------------------------------------------------

def greet_loud(name: str) -> str:
    return f"你好，{name}！"


def demo_04_manual_wrap() -> None:
    original = greet_loud

    def wrapper(name: str) -> str:
        print("   [before] 准备调用", original.__name__)
        result = original(name)
        print("   [after ] 调用完成")
        return result.upper()

    greet_loud_wrapped = wrapper
    print("手动包装结果:", greet_loud_wrapped("小李"))
    print("注意：现在 greet_loud_wrapped 这个名字其实指向 wrapper 函数")


if __name__ == "__main__":
    for title, fn in [
        ("1. 函数是对象", demo_01_function_is_object),
        ("2. 函数元数据", demo_02_function_metadata),
        ("3. 闭包", demo_03_closure),
        ("4. 手动包装（装饰器雏形）", demo_04_manual_wrap),
    ]:
        print("=" * 70)
        print(title)
        print("=" * 70)
        fn()
        print()
