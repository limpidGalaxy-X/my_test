"""
04 - 常用惯用法：合并、反转、排序、分组、快照

这些是实际写代码时反复出现的 8 个套路，背下来能省大量 for 循环。

运行：
    python 04_常用惯用法.py
"""

from collections import Counter, defaultdict
from heapq import nlargest
from operator import itemgetter

print("=" * 68)
print("1) 合并：update / | / |=（冲突一律「右边赢」）")
print("=" * 68)
a, b = {"x": 1, "y": 2}, {"y": 20, "z": 30}
print("a | b            =", a | b, " ← 新字典，a、b 都不变")
merged = dict(a)
merged |= b
print("dict(a) 后 |= b  =", merged, " ← 原地合并")
merged.update({"w": 40})
print("update           =", merged)
print("要「保留左边」怎么办？先 b 后 a：", b | a)

print()
print("=" * 68)
print("2) 值可重复时统计合并：Counter 相加")
print("=" * 68)
c1, c2 = Counter("aab"), Counter("abb")
print("Counter('aab') + Counter('abb') =", c1 + c2)
print("还可以 - & | 求差集/交集/并集取大")

print()
print("=" * 68)
print("3) 反转（值 -> 键）：值唯一才能直接反，重复必须先分组")
print("=" * 68)
name2id = {"Ada": 1, "Bob": 2, "Cara": 3}
print("值唯一时: {v: k for k, v in d.items()} =", {v: k for k, v in name2id.items()})
dup = {"a": 1, "b": 2, "c": 1}
print("值重复时直接反会丢数据     =", {v: k for k, v in dup.items()}, " ← b 消失了")
idx = defaultdict(list)
for k, v in dup.items():
    idx[v].append(k)
print("正确做法 defaultdict(list) =", dict(idx))
try:
    {[1, 2]: "x"}
except TypeError as e:
    print("注意：反转后「值变成了键」，所以值本身必须可哈希：", e)

print()
print("=" * 68)
print("4) 按值排序 / 取 Top-N")
print("=" * 68)
# 故意让"插入顺序"和"键的字母序"不一致（Dan 在 Ada 前面），好看出下面两者的区别
scores = {"Dan": 91, "Bob": 78, "Cara": 95, "Ada": 91}
print("只排键        :", sorted(scores))
print("按值降序      :", sorted(scores.items(), key=itemgetter(1), reverse=True),
      " ← 91 分里 Dan 在前（保持插入顺序）")
print("值降序+键升序 :", sorted(scores.items(), key=lambda kv: (-kv[1], kv[0])),
      " ← 91 分里 Ada 在前")
print("Top-2（heapq，数据量大时更省内存）:", nlargest(2, scores.items(), key=itemgetter(1)))
print("→ reverse=True 只反转排序键，相等元素仍按插入顺序；要「稳定可控」就用负号+元组。")

print()
print("=" * 68)
print("5) 分组与计数：defaultdict / Counter / setdefault")
print("=" * 68)
rows = [("RD", "Ada"), ("QA", "Bob"), ("RD", "Cara"), ("QA", "Dan")]
by_dept = defaultdict(list)
for dept, name in rows:
    by_dept[dept].append(name)
print("defaultdict(list) 分组 =", dict(by_dept))
print("Counter 计数          =", Counter(dept for dept, _ in rows).most_common())
print("setdefault 也能分组   =", {d: [n for dd, n in rows if dd == d] for d in {dd for dd, _ in rows}})
print("普通写法（每个 key 都要先判断）:")
plain = {}
for dept, name in rows:
    plain.setdefault(dept, []).append(name)
print("   ", plain)

print()
print("=" * 68)
print("6) 键视图支持集合运算（因为键可哈希、必然唯一）")
print("=" * 68)
k1, k2 = {"a": 1, "b": 2, "c": 3}.keys(), {"b": 1, "c": 1, "d": 1}.keys()
print("交集 k1 & k2 =", k1 & k2)
print("并集 k1 | k2 =", k1 | k2)
print("差集 k1 - k2 =", k1 - k2)
print("对称差 k1 ^ k2 =", k1 ^ k2)
print("→ 值视图（values()）不支持集合运算，因为值可能重复、可能不可哈希。")

print()
print("=" * 68)
print("7) 遍历时不能改字典（RuntimeError），要改先做快照")
print("=" * 68)
d = {"a": 1, "b": 2, "c": 3}
try:
    for k in d:
        if k == "a":
            del d[k]
except RuntimeError as e:
    print("直接删 ->", type(e).__name__, ":", e)
d = {"a": 1, "b": 2, "c": 3}
for k in list(d):                 # list(d) 是快照
    if k == "a":
        del d[k]
print("用 list(d) 快照后删除 ->", d)
print("另一种更干净的写法（推导式重建）:")
d = {"a": 1, "b": 2, "c": 3}
d = {k: v for k, v in d.items() if k != "a"}
print("   ", d)

print()
print("=" * 68)
print("8) 两个高频小技巧：保序去重 / 用字典当分支表")
print("=" * 68)
items = ["b", "a", "b", "c", "a"]
print("list(dict.fromkeys(items)) 保序去重 =", list(dict.fromkeys(items)))
ops = {"add": lambda x, y: x + y, "mul": lambda x, y: x * y}
print("分支表 ops['add'](2, 3) =", ops["add"](2, 3))
print("未知命令加兜底          =", ops.get("pow", lambda *a: "未知操作")(2, 3))
print("→ 比一长串 if/elif 更快也更清晰；键就是「命令名」。")

print()
print("-" * 68)
print("套路小结：合并用 |、统计用 Counter、分组用 defaultdict(list)、")
print("          排序用 sorted(items, key=itemgetter(1))、动态删改用 list(d) 快照。")
print("-" * 68)
