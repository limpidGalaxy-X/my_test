"""
01 - lambda 基础：它就是一个"没有名字的函数表达式"

一句话：
    lambda 参数1, 参数2: 表达式        ≈ 一个匿名函数对象

和 def 的区别只有两点：
  1) def 是**语句**，lambda 是**表达式** —— 因为它是表达式，才能塞进参数里、
     字典里、列表里；
  2) lambda 的"函数体"只能是**一个表达式**，不能写语句：
         lambda x: x + 1                  ✅
         lambda x: y = x + 1              ❌ 语法错误（赋值是语句）
         lambda x: x + 1 if x else 0      ✅ 三元表达式可以
     参数部分倒是和 def 一样：默认值、*args、仅关键字、**kwargs 全都支持。

⚠️ PEP 8 的明确建议：
    add = lambda a, b: a + b      # ❌ 给匿名函数起名字，不如直接 def 清楚
    lambda 的正当用途 = 传给别的函数的一次性小函数（key=、map、filter、回调）

运行：
    python 01_lambda基础.py
"""

import pickle

print("=" * 68)
print("1) def 和 lambda 行为完全一致，只是写法和元信息不同")
print("=" * 68)


def add_def(a, b):
    return a + b


add_lambda = lambda a, b: a + b  # noqa: E731 （这行是反面教材）

print("普通调用结果一样 :", add_def(2, 3), add_lambda(2, 3))
print("__name__         :", repr(add_def.__name__), "/", repr(add_lambda.__name__))
print("__doc__          :", repr(add_def.__doc__), "/", repr(add_lambda.__doc__))
try:
    pickle.dumps(add_lambda)
except Exception as e:  # PicklingError
    print("能否被 pickle    : lambda 不行 ->", type(e).__name__)
print("→ 结论：装饰器/框架要靠 __name__ 和 __doc__ 生成文档时，别用 lambda。")

print()
print("=" * 68)
print("2) 因为它是表达式，所以能「写完立刻调用」")
print("=" * 68)
print("(lambda n: n * 2)(21) =", (lambda n: n * 2)(21))
print("常用来做一次性的初始化或分支表。")

print()
print("=" * 68)
print("3) 参数写法和 def 一样：默认值 / *args / 仅关键字 / **kwargs")
print("=" * 68)
f = lambda x=1, *args, k=10, **kw: (x, args, k, kw)
print("f(1, 2, 3, k=4, z=5) =", f(1, 2, 3, k=4, z=5))
print("f()                 =", f())
print("→ x 吃第一个位置参数，args 收剩下的，k 是仅关键字，kw 收多余的关键字。")

print()
print("=" * 68)
print("4) 一个表达式 = 三元表达式可以，语句不行")
print("=" * 68)
clean = lambda s: s.strip().lower() if isinstance(s, str) else None
print("clean('  PyThon ') =", clean("  PyThon "))
print("clean(42)         =", clean(42))

print()
print("=" * 68)
print("5) 当作「函数工厂」：lambda 返回 lambda")
print("=" * 68)
make_power = lambda n: (lambda x: x**n)  # 闭包：内层记住了 n
square, cube = make_power(2), make_power(3)
print("square(5) =", square(5), " cube(3) =", cube(3))

print()
print("=" * 68)
print("6) 【最大的坑】循环里的 lambda 是「延迟绑定」")
print("=" * 68)
bad = [lambda: i for i in range(3)]
print("bad  = [lambda: i for i in range(3)]  ->", [fn() for fn in bad])
print("     期望 [0, 1, 2]，实际全是 2：lambda 只记住变量 i，调用时才去取值，")
print("     而此时循环早已结束，i 停在最后一个值。")
good = [lambda i=i: i for i in range(3)]  # 用默认参数把当前值"固化"进去
print("good = [lambda i=i: i ...]            ->", [fn() for fn in good])

print()
print("-" * 68)
print("记住这 4 条就算过关：")
print("  1. lambda 就是没名字的函数，@deco、key=、回调 里到处是它；")
print("  2. 只能写一个表达式，不能有语句（所以不能写 assert/赋值/多行逻辑）；")
print("  3. 别 `名字 = lambda ...`，要复用就 def（PEP 8）；")
print("  4. 循环里创建 lambda 且用到循环变量时，用 `lambda x=x:` 固化。")
print("-" * 68)
