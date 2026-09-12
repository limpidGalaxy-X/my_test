"""
07 - 生成器与 itertools：处理"大/无限/流式"数据的基本功

生成器函数 = 函数体里有 yield 的函数。调用它**不会执行函数体**，
只是拿到一个生成器对象；每次 next() 才执行到下一个 yield 并**暂停**在那里。

    def gen():
        print("开始")
        yield 1          # 执行到这里就交回控制权，状态全部保留
        yield 2

关键认知：
  1) 惰性：不 next（或不等价地遍历）就不干活 —— 这是处理超大文件/无限序列的基础；
  2) 一次性：遍历完就空了，要复用必须先 list()；
  3) 不能 len() / 不能索引；但可以 for、next()、sum()、any()、list()；
  4) yield from 别的可迭代对象 = 把它的元素一个个转出去（不用写 for）；
  5) 无限生成器一定要配 islice / break / takewhile 截断，否则程序卡死。

运行：
    python 07_生成器与itertools.py
"""

import itertools
import sys
import time

print("=" * 68)
print("1) 生成器函数：调用时不执行，next 才执行")
print("=" * 68)


def gen():
    print("   [函数体开始执行]")
    yield 1
    print("   [恢复执行]")
    yield 2
    print("   [准备结束]")
    return "收尾值"          # return 的值会放进 StopIteration.value


g = gen()
print("g = gen() 之后什么都没打印，说明函数体还没跑:", g)
print("next(g) =", next(g))
print("next(g) =", next(g))
try:
    next(g)
except StopIteration as e:
    print("第三次 next -> StopIteration，value =", e.value)

print()
print("=" * 68)
print("2) 惰性与省内存：一个 100 万行的「文件」不用读进内存")
print("=" * 68)


def fake_lines(n):
    """模拟逐行读大文件：这里是生成器，真读文件就是 for line in f。"""
    for i in range(n):
        yield f"line-{i}"


total = sum(1 for _ in fake_lines(1_000_000))
print("统计 100 万行条数:", total, " → 全程内存里只有 1 行")
print("生成器对象大小:", sys.getsizeof(fake_lines(1_000_000)), "字节")

print()
print("=" * 68)
print("3) yield from：把子可迭代对象「转接」出去")
print("=" * 68)


def chain_manual(*iterables):
    for it in iterables:
        for x in it:
            yield x


def chain_yield_from(*iterables):
    for it in iterables:
        yield from it          # 等价于上面那两行，但更快、更短


print("手写嵌套 :", list(chain_manual([1, 2], "ab", (3,))))
print("yield from:", list(chain_yield_from([1, 2], "ab", (3,))))

print()
print("=" * 68)
print("4) send / 协程雏形（了解即可，日常很少手写）")
print("=" * 68)


def accumulator():
    total = 0
    while True:
        x = yield total        # yield 的返回值 = 下一次 send 进来的值
        if x is None:
            break
        total += x


acc = accumulator()
next(acc)                      # 先"预热"到第一个 yield
print("send(10) =", acc.send(10))
print("send(5)  =", acc.send(5))
acc.close()

print()
print("=" * 68)
print("5) itertools 必备清单（都是惰性的）")
print("=" * 68)
print("count(10, 3) + islice  ->", list(itertools.islice(itertools.count(10, 3), 5)))
print("cycle('ab') + islice   ->", list(itertools.islice(itertools.cycle("ab"), 5)))
print("repeat('x', 3)         ->", list(itertools.repeat("x", 3)))
print("chain([1,2],[3])       ->", list(itertools.chain([1, 2], [3])))
print("accumulate([1,2,3,4])  ->", list(itertools.accumulate([1, 2, 3, 4])))
print("accumulate(..., mul)   ->",
      list(itertools.accumulate([1, 2, 3, 4], lambda a, b: a * b)))
print("pairwise([1,2,3,4])    ->", list(itertools.pairwise([1, 2, 3, 4])), " ← 3.10+")
print("batched('abcdef', 2)   ->", list(itertools.batched("abcdef", 2)), " ← 3.12+")
print("takewhile(<3)          ->", list(itertools.takewhile(lambda x: x < 3, [1, 2, 3, 1])))
print("dropwhile(<3)          ->", list(itertools.dropwhile(lambda x: x < 3, [1, 2, 3, 1])))
print("compress               ->", list(itertools.compress("abcd", [1, 0, 1, 0])))
print("product('ab',[1,2])    ->", list(itertools.product("ab", [1, 2])))
print("permutations('abc',2)  ->", ["".join(p) for p in itertools.permutations("abc", 2)])
print("combinations('abc',2)  ->", ["".join(c) for c in itertools.combinations("abc", 2)])
print("groupby（必须先排序）  ->")
rows = [("a", 1), ("b", 2), ("a", 3)]
for key, grp in itertools.groupby(sorted(rows), key=lambda r: r[0]):
    print(f"      {key}: {[r[1] for r in grp]}")

print()
print("=" * 68)
print("6) 无限序列的坑：不截断就会卡死")
print("=" * 68)
start = time.perf_counter()
first_five = list(itertools.islice(itertools.count(), 5))
print("islice(count(), 5) =", first_five, f"耗时 {(time.perf_counter()-start)*1000:.3f} ms")
print("如果写成 list(itertools.count()) —— 内存会一路涨到进程被杀，别试。")

print()
print("=" * 68)
print("7) 生成器只能消费一次（本目录最常踩的坑）")
print("=" * 68)
gen2 = (x for x in [1, 2, 3])
print("第一次 list(gen2) =", list(gen2))
print("第二次 list(gen2) =", list(gen2), " ← 空的！")

print()
print("-" * 68)
print("用一句话判断该不该用生成器：")
print("  数据大到不想一次性放进内存，或者根本是无限的 —— 用生成器；")
print("  需要反复遍历、随机访问、len —— 用 list。")
print("-" * 68)
