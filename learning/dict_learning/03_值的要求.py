"""
03 - 值的要求：几乎没有要求，但有三个必须知道的坑

对比 02 的"键必须可哈希"，值这边一句话：

    **值可以是任何东西** —— 可变、不可哈希、None、函数、类的实例、
    甚至字典它自己；多个键也可以指向同一个对象。

由此带来三个真实存在的坑：
    坑 1：fromkeys 用可变值 -> 所有键共享同一个列表；
    坑 2：copy()/dict() 是浅拷贝 -> 嵌套的可变值仍然共享；
    坑 3：值可以是 None，"键不存在"和"键存在但值是 None"必须分清楚。

运行：
    python 03_值的要求.py
"""

print("=" * 68)
print("1) 值可以是任何类型（键就不行）")
print("=" * 68)
d = {
    "int": 1,
    "list": [1, 2, 3],           # 可变 -> 可以
    "dict": {"nested": True},    # 不可哈希 -> 也可以
    "set": {1, 2},               # 不可哈希 -> 也可以
    "none": None,
    "func": lambda x: x * 2,     # 函数
    "type": int,                 # 类本身
}
print("键的类型都合法，值的类型五花八门:", sorted(d))
print("d['list']      =", d["list"])
print("d['func'](21)  =", d["func"](21))
print("→ 值的类型完全不影响字典能否建立，因为**只有键参与哈希**。")

print()
print("=" * 68)
print("2) 值可以被随意修改，字典照样查得到（因为键没变）")
print("=" * 68)
d = {"nums": [1, 2]}
d["nums"].append(3)
print("往值里 append 之后 d =", d, " 查得到:", d["nums"])
d["nums"] = "整个换成字符串也行"
print("整体替换值之后 d =", d)
print("→ 只要键没动，字典结构就完全稳定。")

print()
print("=" * 68)
print("3) 值可以重复，也可以多个键共享同一个对象")
print("=" * 68)
shared = []
d = {"x": shared, "y": shared, "z": [1]}   # 前两个键指向同一个 list
d["x"].append("来自 x")
print("d =", d, " ← 改一个，另一个也跟着变（别名）")
print("d['x'] is d['y'] ->", d["x"] is d["y"], "  d['z'] is d['x'] ->", d["z"] is d["x"])

print()
print("=" * 68)
print("4) 坑 1：fromkeys 的可变值会被所有键共享")
print("=" * 68)
bad = dict.fromkeys(["a", "b", "c"], [])
bad["a"].append(1)
print("bad = dict.fromkeys(['a','b','c'], [])")
print("bad['a'].append(1) 之后 bad =", bad, " ← b、c 也被改了！")
print("正确写法（字典推导式，每个键一份新对象）:")
good = {k: [] for k in ["a", "b", "c"]}
good["a"].append(1)
print("   good =", good, "  good['a'] is good['b'] ->", good["a"] is good["b"])
print("记法：fromkeys 的值只算一次；需要独立副本就用推导式。")

print()
print("=" * 68)
print("5) 坑 2：copy() 是浅拷贝，嵌套的可变值还是共享的")
print("=" * 68)
import copy

orig = {"cfg": {"retry": 3}, "nums": [1, 2]}
shallow = dict(orig)              # 等价于 orig.copy()
shallow["cfg"]["retry"] = 99      # 只改内层
print("浅拷贝改内层后 orig    =", orig, " ← 原始数据被改了")
shallow["nums"] = [7, 7]          # 整个换掉一层，就不影响原字典
print("浅拷贝换掉一层后 orig  =", orig)
deep = copy.deepcopy(orig)
deep["cfg"]["retry"] = 0
deep["nums"].append(8)
print("深拷贝随便改，orig     =", orig, " deep =", deep)
print("→ 想真正独立：copy.deepcopy；只想省内存共享：浅拷贝（但要清楚共享了什么）。")

print()
print("=" * 68)
print("6) 坑 3：值是 None 和键不存在，get 分不出来")
print("=" * 68)
d = {"a": None, "b": 1}
print("d.get('a') =", d.get("a"), "  d.get('zzz') =", d.get("zzz"), " ← 都是 None")
print("用 in 区分     : 'a' in d =", "a" in d, "  'zzz' in d =", "zzz" in d)
missing = object()                       # 哨兵对象：任何合法值都不可能是它
print("用哨兵区分     : d.get('a', missing) is missing ->", d.get("a", missing) is missing)
print("                 d.get('zzz', missing) is missing ->", d.get("zzz", missing) is missing)

print()
print("=" * 68)
print("7) 值也可以是字典自己（自引用）")
print("=" * 68)
tree = {"name": "root"}
tree["self"] = tree
print("tree['self'] is tree ->", tree["self"] is tree)
print("repr 会自动显示成 {...} 防止无限递归: tree =", tree)
print("json.dumps 这种自引用会直接报错，别拿它去序列化。")

print()
print("=" * 68)
print("8) 值用工厂函数现造：defaultdict 与 setdefault")
print("=" * 68)
from collections import defaultdict

groups = defaultdict(list)          # 值 = list() 的返回值
for name, dept in [("Ada", "RD"), ("Bob", "QA"), ("Cara", "RD")]:
    groups[dept].append(name)
print("defaultdict(list) =", dict(groups))
counter = {}
for ch in "aab":
    counter[ch] = counter.setdefault(ch, 0) + 1
print("setdefault 计数   =", counter)
print("注意：setdefault 会**每次都求值**第二个参数，defaultdict 只在缺键时调用工厂。")

print()
print("-" * 68)
print("值的要求速记：")
print("  1. 值不限类型：可变、不可哈希、None、函数、类、字典自身都行；")
print("  2. 值不参与哈希 -> 改值不影响查找，但多个键可能指向同一对象（注意别名）；")
print("  3. fromkeys 的共享坑、copy 的浅拷贝坑、None 与缺键的区分坑，各踩一次就记住了。")
print("-" * 68)
