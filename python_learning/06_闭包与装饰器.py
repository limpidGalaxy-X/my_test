"""
06 - 闭包与装饰器：lambda 的"升级形态"

装饰器 = 接收函数、返回函数的函数。而它能"记住"东西，靠的是**闭包**。

    闭包三要素：① 外层函数；② 内层函数；③ 内层函数引用了外层的变量（并且外层返回内层）。
    Python 把被引用的外层变量存在内层函数的 __closure__ 里（cell 对象），
    所以外层函数即使已经返回，那些变量也不会被销毁。

语法糖一句话：
        @deco
        def f(): ...
    完全等价于
        def f(): ...
        f = deco(f)          # 装饰发生在"函数定义时"，只发生一次

⚠️ 本目录只讲"够用"的部分；想系统学装饰器（类装饰器、异步装饰器、
   注册表装饰器、迷你 MCP），看 ../mcp_learning/00_装饰器/。

运行：
    python 06_闭包与装饰器.py
"""

import functools
import time

print("=" * 68)
print("1) 闭包：内层函数记住了外层的变量")
print("=" * 68)


def counter():
    n = 0

    def step():
        nonlocal n            # 声明"我要改的是外层的 n"，没有它这里会当成新建局部变量
        n += 1
        return n

    return step


c1, c2 = counter(), counter()
print("c1():", c1(), c1(), c1())
print("c2():", c2(), " ← 两次 counter() 各自独立，互不影响")
print("c1.__closure__:", c1.__closure__, "里存的就是 n")
print("当前 n 的值:", c1.__closure__[0].cell_contents)

print()
print("=" * 68)
print("2) 最小可用装饰器模板（背下来）")
print("=" * 68)


def timer(func):
    @functools.wraps(func)                 # 必须：保留 __name__ / __doc__ / 签名
    def wrapper(*args, **kwargs):          # 必须：原样转发参数
        t0 = time.perf_counter()
        result = func(*args, **kwargs)     # 必须：真的调用原函数
        print(f"   [timer] {func.__name__} 耗时 {(time.perf_counter()-t0)*1000:.2f} ms")
        return result                      # 必须：把返回值传出去
    return wrapper


@timer
def slow_add(a, b):
    """加法，但故意慢一点。"""
    time.sleep(0.01)
    return a + b


print("slow_add(1, 2) =", slow_add(1, 2))
print("元信息保住了:", slow_add.__name__, "/", slow_add.__doc__)

print()
print("=" * 68)
print("3) 不带 wraps 会怎样（反面教材）")
print("=" * 68)


def no_wraps(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@no_wraps
def documented(x):
    """我是文档字符串。"""
    return x


print("__name__ =", repr(documented.__name__), "  __doc__ =", repr(documented.__doc__))
print("→ 全变成 wrapper/None：框架（FastAPI / MCP / pytest）靠这些生成文档和 Schema，")
print("  少了 wraps 就会出现一堆同名接口或空 Schema。")

print()
print("=" * 68)
print("4) 带参数的装饰器：多一层函数（三层结构）")
print("=" * 68)


def repeat(times=2, sep=""):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return sep.join(str(func(*args, **kwargs)) for _ in range(times))
        return wrapper
    return decorator


@repeat(3, sep=" | ")
def hello(name):
    return f"hi {name}"


@repeat(2, sep=" & ")          # 括号不能省，否则传进去的是函数而不是参数
def bye(name):
    return f"bye {name}"


print("hello('Ada') =", hello("Ada"))
print("bye('Bob')   =", bye("Bob"))
print("→ 记忆：不带参数 @deco；带参数 @deco(...) 等于 @decorator，多包一层。")

print()
print("=" * 68)
print("5) 类装饰器：用 __call__ 存状态 / 带参数")
print("=" * 68)


class CountCalls:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.func(*args, **kwargs)


@CountCalls
def ping():
    return "pong"


print("ping() 第一次 =", ping())
print("ping() 第二次 =", ping())
print("累计调用次数 =", ping.count, " ← 状态就存在装饰器实例里")
print("→ 类装饰器的好处：状态就存在实例属性里，不用 nonlocal 折腾。")

print()
print("=" * 68)
print("6) 实战：重试装饰器（异常处理也常见在装饰器里做）")
print("=" * 68)


def retry(times=3, exc=Exception):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exc as e:
                    print(f"   第 {attempt} 次失败：{e}")
                    if attempt == times:
                        raise
        return wrapper
    return decorator


calls = {"n": 0}


@retry(times=3)
def flaky():
    calls["n"] += 1
    if calls["n"] < 3:
        raise RuntimeError("网络抖动")
    return "第 3 次成功"


print("flaky() =", flaky())

print()
print("-" * 68)
print("四个必须记住的坑：")
print("  1. 不写 functools.wraps -> 元信息丢失；")
print("  2. wrapper 不写 *args/**kwargs -> 被装饰的函数一传参就 TypeError；")
print("  3. wrapper 忘了 return -> 被装饰函数的返回值变成 None；")
print("  4. 用同步装饰器包 async def -> 拿到的是协程对象，得用 async def wrapper + await。")
print("-" * 68)
