"""
05 - 性能与原理：为什么字典查找是 O(1)

一句话原理：dict 内部是一张**哈希表**。
    hash(key) -> 桶的下标 -> 基本一步到位；桶被别人占了（冲突）就再探测下一个。
    所以平均 O(1)，最坏 O(n)（所有键哈希相同，退化成链表式逐个比较）。

这一节用实测数据说话，让你对"什么时候该用字典"有量化的感觉：
  1) 查找速度：dict / set / list 对比；
  2) 哈希冲突时的最坏情况（数一数 __eq__ 被调用了多少次）；
  3) 内存开销：字典是"用空间换时间"的典型；
  4) 哈希函数被调用几次（自定义 __hash__ 写慢了会拖慢一切）。

运行：
    python 05_性能与原理.py
"""

import sys
import timeit
import tracemalloc

print("=" * 68)
print("1) 实测：在 1000 个元素里判断「某个值在不在」× 20000 次")
print("=" * 68)
setup = "nums = list(range(1000)); d = {i: i for i in nums}; s = set(nums)"
n = 20000
t_dict = timeit.timeit("999 in d", setup=setup, number=n)
t_set = timeit.timeit("999 in s", setup=setup, number=n)
t_list = timeit.timeit("999 in nums", setup=setup, number=n)
print(f"dict   : {t_dict * 1000:9.4f} ms   （每次 {t_dict / n * 1e9:8.1f} ns）")
print(f"set    : {t_set * 1000:9.4f} ms   （每次 {t_set / n * 1e9:8.1f} ns）")
print(f"list   : {t_list * 1000:9.4f} ms   （每次 {t_list / n * 1e9:8.1f} ns）")
print(f"→ list 比 dict 慢约 {t_list / t_dict:.0f} 倍：list 是逐个比较，dict 是一次哈希。")
print("  所以：频繁「在不在」-> 用 dict/set；只在末尾追加、按位置访问 -> 用 list。")

print()
print("=" * 68)
print("2) 最坏情况：哈希全冲突，O(1) 退化成 O(n)")
print("=" * 68)
eq_calls = 0


class Bad:
    """哈希恒为 0 —— 所有键都挤在同一个桶里。"""

    def __init__(self, v):
        self.v = v

    def __hash__(self):
        return 0

    def __eq__(self, other):
        global eq_calls
        eq_calls += 1
        return isinstance(other, Bad) and self.v == other.v


class Good:
    """哈希按内容分散 —— 正常情况。"""

    def __init__(self, v):
        self.v = v

    def __hash__(self):
        return hash(self.v)

    def __eq__(self, other):
        global eq_calls
        eq_calls += 1
        return isinstance(other, Good) and self.v == other.v


size = 1000
bad_dict = {Bad(i): i for i in range(size)}
good_dict = {Good(i): i for i in range(size)}

probe_bad, probe_good = Bad(-1), Good(-1)     # 都查一个不存在的键
eq_calls = 0
_ = probe_bad in bad_dict
bad_calls = eq_calls
eq_calls = 0
_ = probe_good in good_dict
good_calls = eq_calls

t_bad = timeit.timeit(lambda: probe_bad in bad_dict, number=2000)
t_good = timeit.timeit(lambda: probe_good in good_dict, number=2000)
print(f"全部冲突的字典：一次查找比较了 {bad_calls} 次（= 元素个数），2000 次查找耗时 {t_bad * 1000:.3f} ms")
print(f"正常分散的字典：一次查找比较了 {good_calls} 次，2000 次查找耗时 {t_good * 1000:.3f} ms")
print("→ 这就是 O(n) 与 O(1) 的差距。危险点：故意造成大量哈希冲突可以拖垮服务")
print("  （哈希碰撞攻击），这也是字符串哈希随机化存在的原因（见 02）。")

print()
print("=" * 68)
print("3) 实测：哈希函数被调用几次（自定义 __hash__ 越慢，字典就越慢）")
print("=" * 68)
hash_calls = 0


class Counted:
    def __init__(self, v):
        self.v = v

    def __hash__(self):
        global hash_calls
        hash_calls += 1
        return hash(self.v)

    def __eq__(self, other):
        return isinstance(other, Counted) and self.v == other.v


keys = [Counted(i) for i in range(3)]
hash_calls = 0
d = {k: i for i, k in enumerate(keys)}      # 插入 3 个键
insert_calls = hash_calls
hash_calls = 0
_ = d[keys[1]]                              # 一次查找
lookup_calls = hash_calls
print(f"插入 3 个键：__hash__ 被调用 {insert_calls} 次（每个键一次）")
print(f"一次查找    ：__hash__ 被调用 {lookup_calls} 次")
print("→ 查找只算一次哈希，剩下的都比较 __eq__；所以把 __hash__ 写成大计算会拖慢整张表。")
print("  提示：CPython 会把 str 的哈希缓存在字符串对象里，自定义类没有这种待遇，")
print("        真需要可以自己缓存（例如 __slots__ + 首次计算后记住）。")

print()
print("=" * 68)
print("4) 实测：内存开销（空间换时间）")
print("=" * 68)
print("空字典          :", sys.getsizeof({}), "字节")
print("{'a': 1}        :", sys.getsizeof({"a": 1}), "字节")
print("list 1000 个 int:", sys.getsizeof(list(range(1000))), "字节")
tracemalloc.start()
big = {i: 0 for i in range(1_000_000)}
peak_before_stop = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()
print("100 万条 dict   :", f"{sys.getsizeof(big) / 1024 / 1024:.1f} MB（只算哈希表本身）")
print("                  ", f"{peak_before_stop / 1024 / 1024:.1f} MB（tracemalloc 统计，含键对象）")
del big
print("→ 同样的数据，dict 比 list 占内存明显更多。只为「去重/判存在」就别用 dict，")
print("  用 set；需要有序 + 省内存就用 list/tuple。")

print()
print("=" * 68)
print("5) 三条不用背但要信的性质")
print("=" * 68)
d = {}
for k in "cab":
    d[k] = 1
print("① 顺序 = 插入顺序（不是排序）:", list(d), " sorted 之后:", sorted(d))
print("② 增/删/查 都是均摊 O(1)：容量不够时整表扩容重排，所以个别插入会突然慢一下")
d.clear()
d["x"] = 1
small = sys.getsizeof(d)
for i in range(1000):
    d[i] = i
grown = sys.getsizeof(d)
for i in range(999):
    del d[i]
after_del = sys.getsizeof(d)
empty_again = None
d.clear()
empty_again = sys.getsizeof(d)
print(f"   1 条 {small} 字节 -> 1000 条 {grown} 字节 -> 逐条 del 到剩 1 条仍占 {after_del} 字节")
print(f"   逐个 del 不会缩容；只有 clear() 才会把表重置回 {empty_again} 字节")
print("③ 键必须可哈希（见 02）、值随便（见 03）——这两条决定了字典能怎么用")

print()
print("-" * 68)
print("选型速记：")
print("  频繁按键查值 -> dict；    只判存在/去重 -> set；")
print("  按位置/顺序处理 -> list； 固定结构的小对象 -> tuple / dataclass / __slots__")
print("-" * 68)
