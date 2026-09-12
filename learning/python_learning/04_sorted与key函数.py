"""
04 - sorted / key 函数：lambda 出现频率最高的地方

    sorted(可迭代对象, key=取一个值, reverse=True)   -> 新列表，原数据不动
    list.sort(key=..., reverse=True)                -> 原地排序，返回 None！

三条铁律：
  1) key 不是"比较函数"，而是"**给每个元素算一个排序用的值**"的函数：
         key=lambda s: s.lower()        ✅ 返回一个可比较的值
         key=lambda a, b: a - b         ❌ 参数写错了，key 只收到 1 个元素
     要比两个元素？用 functools.cmp_to_key 包一层。
  2) key 每个元素**只调用一次**（内部先算好 key 再排序），所以
     key 里放稍微耗时的计算是可以接受的。
  3) Python 的排序是**稳定排序**：值相等的元素保持原来的相对顺序。
     利用这一点，"先按次要键排一次，再按主要键排一次"就能实现多级排序。

运行：
    python 04_sorted与key函数.py
"""

from functools import cmp_to_key
from operator import attrgetter, itemgetter

words = ["banana", "Apple", "cherry", "apricot"]
people = [
    {"name": "Ada", "age": 36, "city": "London"},
    {"name": "Bob", "age": 25, "city": "Paris"},
    {"name": "Cara", "age": 36, "city": "Berlin"},
]

print("=" * 68)
print("1) 基本用法 + 最常见的 bug")
print("=" * 68)
print("sorted(words)                     =", sorted(words))
print("sorted(words, key=str.lower)      =", sorted(words, key=str.lower))
print("sorted(words, key=lambda s: len(s), reverse=True) =",
      sorted(words, key=lambda s: len(s), reverse=True))
copy = words.copy()
result = copy.sort()
print("copy.sort() 的返回值              =", result, " ← None！原地改的是 copy：", copy)
print("words 没被动过                    =", words)

print()
print("=" * 68)
print("2) 对字典排序：默认排键，排值要 items() + itemgetter")
print("=" * 68)
score = {"Ada": 91, "Bob": 78, "Cara": 91}
print("sorted(score)                      =", sorted(score), " ← 只排键")
print("按值降序:", sorted(score.items(), key=itemgetter(1), reverse=True))
print("按值降序(第二个键按名字):",
      sorted(score.items(), key=lambda kv: (-kv[1], kv[0])))

print()
print("=" * 68)
print("3) 多级排序：key 返回元组（最常用）")
print("=" * 68)
print("按 age 升序、age 相同按 name 升序:")
for p in sorted(people, key=lambda p: (p["age"], p["name"])):
    print("   ", p["age"], p["name"])
print("按 age 降序、age 相同按 name 升序（降序键取负）:")
for p in sorted(people, key=lambda p: (-p["age"], p["name"])):
    print("   ", p["age"], p["name"])
print("→ 数字取负最简单；字符串/不支持取负的值，就分两次稳定排序。")

print()
print("=" * 68)
print("4) 稳定排序：reverse=True 也不会打乱相等元素的原顺序")
print("=" * 68)
data = [("a", 1), ("b", 1), ("c", 1)]
print("sorted(data, key=itemgetter(1), reverse=True) =",
      sorted(data, key=itemgetter(1), reverse=True), " ← a,b,c 顺序没变")
two_pass = sorted(people, key=lambda p: p["name"])            # 先按次要键
two_pass = sorted(two_pass, key=lambda p: p["age"], reverse=True)  # 再按主要键
print("两次排序实现多级:", [(p["age"], p["name"]) for p in two_pass])

print()
print("=" * 68)
print("5) key 只算一次（实测：key 函数被调用几次）")
print("=" * 68)
calls = []


def slow_key(p):
    calls.append(p["name"])
    return p["age"]


sorted(people, key=slow_key)
print("len(people) =", len(people), " key 被调用次数 =", len(calls), " 顺序 =", calls)

print()
print("=" * 68)
print("6) min / max 也吃 key，还有 default 兜底")
print("=" * 68)
print("max(people, key=itemgetter('age')) =", max(people, key=itemgetter("age"))["name"])
print("min(words, key=len)                =", min(words, key=len))
print("max([], default='空')              =", max([], default="空"), " ← 空序列必须给 default")
try:
    max([])
except ValueError as e:
    print("max([]) 不给 default →", type(e).__name__, ":", e)

print()
print("=" * 68)
print("7) 对象属性排序 & 自定义比较函数 cmp_to_key")
print("=" * 68)


class User:
    def __init__(self, name, age):
        self.name, self.age = name, age

    def __repr__(self):
        return f"User({self.name},{self.age})"


users = [User("Ada", 36), User("Bob", 25)]
print("attrgetter('age')      =", sorted(users, key=attrgetter("age")))
print("attrgetter('age','name') 也是元组多级排序 =",
      sorted(users + [User("Zoe", 25)], key=attrgetter("age", "name")))


def by_age_desc(a, b):
    return b.age - a.age   # 正数表示 a 排后面；这种"两两比较"才需要 cmp_to_key


print("cmp_to_key(by_age_desc)=", sorted(users, key=cmp_to_key(by_age_desc)))

print()
print("=" * 68)
print("8) 先分组再排（itertools.groupby 要求输入已排序）")
print("=" * 68)
from itertools import groupby

for age, group in groupby(sorted(people, key=itemgetter("age")), key=itemgetter("age")):
    print(f"   age={age}: {[p['name'] for p in group]}")

print()
print("-" * 68)
print("记住：key= 只收到一个元素 -> 返回排序依据；要降序就给数字取负或用 reverse=True；")
print("      要两两比较 -> cmp_to_key（很少用，优先改写成 key）。")
print("-" * 68)
