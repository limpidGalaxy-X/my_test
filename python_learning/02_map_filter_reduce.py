"""
02 - map / filter / reduce：函数式三件套，以及"什么时候别用它们"

    map(f, xs)            把 f 依次作用到每个元素上       -> 迭代器
    filter(f, xs)         f 返回真值的元素留下            -> 迭代器
    reduce(f, xs, init)   从左到右"累积"成一个值           -> 单个值（functools）

关键认知：
  1) map / filter 返回的是**惰性迭代器**，不是列表：要看结果得 list() 一下，
     而且**只能消费一次**；
  2) 现代 Python 里，能用推导式的地方**优先用推导式**（更快、更短、更好读），
     map/filter 主要留给"已经有现成函数"的场景，例如 map(int, ...)、
     map(str.strip, lines)；
  3) reduce 很少用，常见替代：
         求和 -> sum(xs)      求积/字符串拼接 -> 推导式或 math.prod
         最值 -> max/min       分组 -> collections.defaultdict

运行：
    python 02_map_filter_reduce.py
"""

import timeit
from functools import reduce
from operator import add, mul, itemgetter

nums = [1, 2, 3, 4, 5]

print("=" * 68)
print("1) map：把函数作用到每个元素")
print("=" * 68)
print("list(map(lambda x: x*x, nums)) =", list(map(lambda x: x * x, nums)))
print("list(map(str, nums))          =", list(map(str, nums)))
print("再消费一次同一个 map 对象     =", list(map(lambda x: x * x, nums))[:2], "(这是新对象)")

m = map(str, nums)
print("m = map(str, nums) ->", list(m))
print("第二次 list(m)     ->", list(m), " ← 空！迭代器是一次性的")

print()
print("=" * 68)
print("2) map 可以同时吃多个可迭代对象（长度取最短 / 3.14 起可开 strict）")
print("=" * 68)
print("list(map(add, [1,2,3], [10,20,30])) =", list(map(add, [1, 2, 3], [10, 20, 30])))
print("长度不等时默认按最短截断         =", list(map(add, [1, 2, 3], [10, 20])))
try:
    list(map(add, [1, 2, 3], [10, 20], strict=True))  # Python 3.14 新增
except ValueError as e:
    print("map(..., strict=True) 长度不等 →", type(e).__name__, ":", e)

print()
print("=" * 68)
print("3) filter：按条件筛选（f 为 None 时直接筛掉假值）")
print("=" * 68)
print("list(filter(lambda x: x % 2, nums)) =", list(filter(lambda x: x % 2, nums)))
mixed = [0, "", "a", None, 3, [], "b"]
print("list(filter(None, mixed))           =", list(filter(None, mixed)), " ← 去掉所有假值")

print()
print("=" * 68)
print("4) reduce：把一串值累积成一个值")
print("=" * 68)
print("reduce(add, nums)        =", reduce(add, nums), "（= 1+2+3+4+5）")
print("reduce(mul, nums)        =", reduce(mul, nums), "（= 5!）")
print("reduce(mul, nums, 10)    =", reduce(mul, nums, 10), "（第 3 个参数是初始值）")
print("reduce(add, [], 100)     =", reduce(add, [], 100), " ← 空序列必须给初始值")
try:
    reduce(add, [])
except TypeError as e:
    print("reduce(add, []) 无初始值 →", type(e).__name__, ":", e)

print()
print("=" * 68)
print("5) any / all：短路求值（写条件判断极其常用）")
print("=" * 68)


def noisy_positive(n):
    print("      检查", n)
    return n > 2


print("   any(n > 2 for n in [1,2,3,4])：")
print("   结果 =", any(noisy_positive(n) for n in [1, 2, 3, 4]), " ← 到 3 就停了，4 没被检查")
print("   all(n > 0 for n in [1,2,3]) =", all(n > 0 for n in [1, 2, 3]))
print("   any([]) =", any([]), " all([]) =", all([]), " ← 空集合：any 假、all 真（真空真）")

print()
print("=" * 68)
print("6) 实测：map/filter 与推导式谁快？（本机 CPython 3.14.7）")
print("=" * 68)
setup = "nums = list(range(1000))"
t_map = timeit.timeit("list(map(lambda x: x * 2, nums))", setup=setup, number=2000)
t_cmp = timeit.timeit("[x * 2 for x in nums]", setup=setup, number=2000)
t_fil_map = timeit.timeit("list(filter(lambda x: x % 2, nums))", setup=setup, number=2000)
t_fil_cmp = timeit.timeit("[x for x in nums if x % 2]", setup=setup, number=2000)
print(f"map + lambda   : {t_map * 1000:7.1f} ms")
print(f"推导式         : {t_cmp * 1000:7.1f} ms")
print(f"filter+lambda  : {t_fil_map * 1000:7.1f} ms")
print(f"带 if 的推导式 : {t_fil_cmp * 1000:7.1f} ms")
print("→ 推导式通常更快（少了每轮一次的函数调用），可读性也更稳。")

print()
print("=" * 68)
print("7) map/filter 真正的舒适区：已经有现成函数，不用写 lambda")
print("=" * 68)
raw = [" 12 ", "34", " 56"]
print('map(int, ...)        =', list(map(int, raw)), " ← 注意 int 能容忍空白和换行")
print('map(str.strip, ...)  =', list(map(str.strip, raw)))
words = ["apple", "Banana", "cherry"]
print("sorted 大小写无关    =", sorted(words, key=str.lower))
print("operator.itemgetter  =", sorted([("b", 2), ("a", 3)], key=itemgetter(1)))

print()
print("-" * 68)
print("选型口诀：")
print("  要列表结果 → 推导式；  已有函数 → map/filter；  要累积成一个值 → 先想 sum/max/join")
print("-" * 68)
