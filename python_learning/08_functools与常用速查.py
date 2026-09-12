"""
08 - functools / operator / 常用内置速查（背下这张表，代码短一半）

这一节不打算讲透，只求"知道有这个工具，用的时候能想起来"。

    functools.partial         冻结部分参数，造一个新函数（回调里常用）
    functools.lru_cache       自动缓存函数结果（比手写 memo 快且省事）
    functools.cache           = lru_cache(maxsize=None)，简单的记忆化
    functools.reduce          累积（详见 02）
    functools.wraps           装饰器必备（详见 06）
    functools.cmp_to_key      把"两两比较函数"变成 key（详见 04）
    functools.singledispatch  按第一个参数类型分派（代替 if isinstance 长链）

运行：
    python 08_functools与常用速查.py
"""

import math
import sys
from collections import Counter, defaultdict, deque
from functools import cache, lru_cache, partial, singledispatch
from operator import add, attrgetter, itemgetter, methodcaller

print("=" * 68)
print("1) partial：把参数「冻」住，生成新函数")
print("=" * 68)
to_bin = partial(int, base=2)          # 相当于 def to_bin(s): return int(s, base=2)
print("partial(int, base=2)('1010') =", to_bin("1010"))
print("partial(int, base=16)('ff')  =", partial(int, base=16)("ff"))
log_info = partial(print, "[INFO]")    # 固定前缀，写日志/回调很方便
log_info("服务已启动")

print()
print("=" * 68)
print("2) lru_cache / cache：一行搞定记忆化")
print("=" * 68)
call_count = 0


@lru_cache(maxsize=None)
def fib(n):
    global call_count
    call_count += 1
    return n if n < 2 else fib(n - 1) + fib(n - 2)


print("fib(30) =", fib(30), " 真正计算的次数 =", call_count, "（不加缓存是百万级）")
print("cache_info:", fib.cache_info())
fib.cache_clear()
print("clear 之后:", fib.cache_info())


@cache
def square(x):
    return x * x


print("cache 版 square(9) =", square(9))
try:
    square([1, 2])                      # 参数必须可哈希
except TypeError as e:
    print("传列表给带缓存的函数 →", type(e).__name__, ":", e)
print("【坑】缓存返回的是同一个对象：可变返回值被改动会污染缓存。")

print()
print("=" * 68)
print("3) singledispatch：按类型分派，替代一长串 isinstance")
print("=" * 68)


@singledispatch
def render(x):
    return f"未知类型({type(x).__name__})"


@render.register(int)
@render.register(float)
def _(x):
    return f"数字 {x}"


@render.register(str)
def _(x):
    return f"字符串 {x!r}"


@render.register(list)
def _(x):
    return "列表[" + ", ".join(render(i) for i in x) + "]"


print(render(3), "|", render(3.5), "|", render("hi"), "|", render([1, "a"]))

print()
print("=" * 68)
print("4) operator：让 map/sorted/min 不用写 lambda")
print("=" * 68)
rows = [("b", 2), ("a", 3), ("c", 1)]
print("itemgetter(0) 排序   :", sorted(rows, key=itemgetter(0)))
print("itemgetter(1) 排序   :", sorted(rows, key=itemgetter(1)))
print("attrgetter 用法见 04")
print("methodcaller('strip') :", list(map(methodcaller("strip"), [" a ", " b "])))
print("reduce(add, [1,2,3])  = 见 02")

print()
print("=" * 68)
print("5) collections：Counter / defaultdict / deque")
print("=" * 68)
text = "abracadabra"
print("Counter(text).most_common(3) =", Counter(text).most_common(3))
print("Counter 支持算术       =", Counter("aab") + Counter("abb"))
groups = defaultdict(list)
for name, dept in [("Ada", "RD"), ("Bob", "QA"), ("Cara", "RD")]:
    groups[dept].append(name)           # 不用先判断 key 在不在
print("defaultdict(list) 分组 =", dict(groups))
window = deque(maxlen=3)                # 定长滑窗：满了自动丢最老的
for i in range(1, 6):
    window.append(i)
print("deque(maxlen=3) 滑窗   =", list(window))

print()
print("=" * 68)
print("6) 常用内置/字符串小抄（都是高频「少写十行」的）")
print("=" * 68)
print("zip(strict=True) 长度不等会报错:", end=" ")
try:
    list(zip([1, 2], "abc", strict=True))
except ValueError as e:
    print("ValueError:", e)
print("enumerate(xs, start=1) =", list(enumerate("ab", start=1)))
d = {}
d.setdefault("k", []).append(1)
print("dict.setdefault 建默认值 =", d)
print("' - '.join(['a','b'])    =", " - ".join(["a", "b"]))
print("math.prod([1,2,3,4])     =", math.prod([1, 2, 3, 4]))
print("sum([[1],[2]], [])       =", sum([[1], [2]], []), " ← 列表拼接（慢，仅限小数据）")
print("divmod(17, 5)            =", divmod(17, 5))
print("'a.txt'.removeprefix('a.') =", "a.txt".removeprefix("a."))
print("next(iter([]), '兜底')   =", next(iter([]), "兜底"))
print("f-string 调试 {x=}       =", f"{text[:3]=}")
print("int/float 格式化         =", f"{3.14159:.2f} / {1234567:,} / {0.256:.1%}")

print()
print("=" * 68)
print("7) 和 lambda 搭配最紧密的一句：sorted + key + itemgetter/lambda")
print("=" * 68)
scores = {"Ada": 91, "Bob": 78, "Cara": 95}
print("按分数降序取前 2:", [n for n, _ in sorted(scores.items(), key=itemgetter(1), reverse=True)[:2]])

print()
print("-" * 68)
print("选择顺序：内置函数 > operator > lambda > 手写 for")
print("  能用 sum/max/min/sorted/Counter 就别自己循环；能不用 lambda 就别用。")
print("-" * 68)
