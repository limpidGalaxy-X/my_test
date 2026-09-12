"""
03 - 推导式（comprehension）：lambda + map/filter 的现代替代品

四种形态，长得像，但结果类型不同：

    [表达式 for x in xs if 条件]        -> list    （列表推导式）
    {k: v for x in xs}                  -> dict    （字典推导式）
    {表达式 for x in xs}                 -> set     （集合推导式，自动去重）
    (表达式 for x in xs)                 -> 生成器   （惰性！不占内存，只能遍历一次）

记忆点：
  1) if 放在 for 后面 = 过滤；放在表达式里的三元 = 变换：
         [x for x in xs if x > 0]          过滤
         [x if x > 0 else 0 for x in xs]   变换
  2) 多个 for = 嵌套循环（笛卡尔积），从左到右是从外到内；
  3) 推导式有自己的作用域，循环变量**不会泄漏**到外面；
  4) 生成器表达式是"省内存神器"，sum/max/any/all 这类聚合函数直接吃它；
  5) 超过两层嵌套、或者带副作用 → 老老实实写 for 循环，读得懂最重要。

运行：
    python 03_推导式.py
"""

import sys
import timeit

nums = [1, 2, 3, 4, 5, 6]

print("=" * 68)
print("1) 四种形态")
print("=" * 68)
print("list  :", [x * x for x in nums])
print("dict  :", {x: x * x for x in nums if x % 2 == 0})
print("set   :", {x % 3 for x in nums}, " ← 自动去重")
gen = (x * x for x in nums)
print("gen   :", gen, " ← 只是个生成器对象，还没算")

print()
print("=" * 68)
print("2) 过滤 vs 变换（最容易写混的地方）")
print("=" * 68)
print("过滤 [x for x in nums if x % 2]        =", [x for x in nums if x % 2])
print("变换 [x if x % 2 else 0 for x in nums] =", [x if x % 2 else 0 for x in nums])
print("两者叠加 = 先过滤再变换               =", [x * 10 for x in nums if x % 2])

print()
print("=" * 68)
print("3) 多个 for：嵌套循环 / 展平 / 矩阵转置")
print("=" * 68)
print("笛卡尔积:", [(x, y) for x in "ab" for y in [1, 2]])
matrix = [[1, 2, 3], [4, 5, 6]]
print("展平    :", [n for row in matrix for n in row])
print("转置    :", [[row[i] for row in matrix] for i in range(3)])
print("转置(更地道，用 zip):", [list(col) for col in zip(*matrix)])

print()
print("=" * 68)
print("4) 作用域：循环变量不泄漏（Python 3 的特性）")
print("=" * 68)
i = "外面的 i"
squares = [i * 2 for i in range(3)]
print("推导式结果:", squares, " 外层的 i 还是:", repr(i), " ← 没被覆盖")
try:
    [j for j in range(3)]
    print(j)
except NameError:
    print("推导式里的 j 在外面不可见 -> NameError（推导式有自己的作用域）")

print()
print("=" * 68)
print("5) 海象运算符 := 在推导式里：算一次，用两次")
print("=" * 68)
raw = [" 12 ", "abc", " 34 ", ""]


def parse(s):
    print("      调用 parse:", repr(s))
    s = s.strip()
    return int(s) if s.isdigit() else None


kept = [v for s in raw if (v := parse(s)) is not None]
print("kept =", kept, " ← parse 每个元素只调用一次（不用 := 就得算两遍）")

print()
print("=" * 68)
print("6) 生成器表达式：惰性 + 省内存（实测）")
print("=" * 68)
big_list = [x for x in range(1_000_000)]
big_gen = (x for x in range(1_000_000))
print(f"列表内存 {sys.getsizeof(big_list):>9,} 字节")
print(f"生成器   {sys.getsizeof(big_gen):>9,} 字节  ← 差 5 个数量级")
del big_list
print("sum(x*x for x in range(100)) =", sum(x * x for x in range(100)), "（省掉一层 []）")
print("any(...) / max(...) / min(...) 同理，都直接吃生成器。")

print()
print("=" * 68)
print("7) 实测：推导式 vs for + append（本机 CPython 3.14.7）")
print("=" * 68)
t_cmp = timeit.timeit("[x * 2 for x in range(1000)]", number=5000)
t_loop = timeit.timeit(
    "out = []\nfor x in range(1000):\n    out.append(x * 2)", number=5000
)
print(f"推导式       : {t_cmp * 1000:7.1f} ms")
print(f"for + append : {t_loop * 1000:7.1f} ms")
print("→ 3.12 起推导式被内联（PEP 709），这里差距不大；但推导式仍然更短。")

print()
print("-" * 68)
print("三个高频坑：")
print("  1. 生成器只能遍历一次，遍历第二遍是空的——要复用就先 list() 出来；")
print("  2. 生成器不能 len() / 不能索引，别把它当列表用；")
print("  3. 嵌套超过两层，或者循环体里有 print / 追加副作用，就用普通 for。")
print("-" * 68)
