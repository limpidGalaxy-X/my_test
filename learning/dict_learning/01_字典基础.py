"""
01 - 字典基础：创建、访问、增删改、遍历

dict = 键值对集合（mapping）。一句话记住它的两条核心性质：
  1) 键 -> 值的映射：用键查找值，**平均 O(1)**（靠哈希表，见 05）；
  2) **插入有序**：3.7 起遍历顺序就是插入顺序（不是排序，排序要自己 sorted）。

本文件只讲"日常必用"的语法，键和值各自的要求在 02、03 里专门讲。

运行：
    python 01_字典基础.py
"""

print("=" * 68)
print("1) 五种常见创建方式")
print("=" * 68)
print("字面量        :", {"a": 1, "b": 2})
print("dict(k=v)     :", dict(a=1, b=2))
print("dict(可迭代)  :", dict([("a", 1), ("b", 2)]))
print("zip 拼         :", dict(zip("ab", [1, 2])))
print("推导式        :", {k: v for k, v in [("a", 1), ("b", 2)]})
print("fromkeys      :", dict.fromkeys("abc", 0), " ← 值会共享，见 03 的坑")
print("空字典        :", {}, " / ", dict())

print()
print("=" * 68)
print("2) 访问：d[k] 会抛异常，get 不会")
print("=" * 68)
d = {"name": "Ada", "age": 36}
print("d['name']              =", d["name"])
print("d.get('city')          =", d.get("city"), " ← 键不存在给 None，不报错")
print("d.get('city', '未知')  =", d.get("city", "未知"))
try:
    d["city"]
except KeyError as e:
    print("d['city']              ->", type(e).__name__, ":", e)
print("'name' in d            =", "name" in d, "  'city' in d =", "city" in d)
print("d.get('name') 和 d['name'] 的区别：一个容错，一个快速失败。")

print()
print("=" * 68)
print("3) 增 / 改 / 删")
print("=" * 68)
d["age"] = 37                     # 键存在 = 改
d["city"] = "London"              # 键不存在 = 增
print("改和增都是 d[k] = v  :", d)
print("del d['city']        :", end=" ")
del d["city"]
print(d)
print("d.pop('age')         =", d.pop("age"), " → ", d)
print("d.pop('没有的键', 0)  =", d.pop("没有的键", 0), " ← 给默认值才不报错")
d.update({"name": "Bob", "lang": "py"})
print("update 批量改/增      :", d)
d2 = {"name": "Bob", "lang": "py"}
d2 |= {"lang": "Py", "lv": 3}      # 3.9+：原地合并，冲突取右边
print("|= 原地合并           :", d2)
print("d2 | {'x': 9}         =", d2 | {"x": 9}, " ← 返回新字典，d2 不变")
print("popitem（删最后一个） =", d2.popitem())

print()
print("=" * 68)
print("4) 遍历：三种视图 + items 解包")
print("=" * 68)
scores = {"Ada": 91, "Bob": 78, "Cara": 95}
print("遍历键   :", [k for k in scores])
print("遍历值   :", [v for v in scores.values()])
print("遍历键值 :", [f"{k}={v}" for k, v in scores.items()])
for name, score in scores.items():
    pass
print("for k, v in d.items() 是最常见的写法（顺便解包）")
print("len(scores) =", len(scores), "  d.keys() 类型 =", type(scores.keys()).__name__)
print("视图是「活的」：改了字典，视图跟着变")
view = scores.keys()
scores["Dan"] = 60
print("   改之前拿到的 view 现在 =", list(view))

print()
print("=" * 68)
print("5) 顺序 = 插入顺序，删掉再插会跑到最后")
print("=" * 68)
order = {}
for k in "cab":
    order[k] = k
print("依次插入 c,a,b ->", list(order))
del order["a"]
order["a"] = "a"
print("删掉 a 再插回来  ->", list(order), " ← 追加到末尾")
print("要排序就自己来：sorted(order) =", sorted(order))

print()
print("=" * 68)
print("6) 嵌套字典：取值链一层层 get")
print("=" * 68)
config = {"db": {"host": "localhost", "port": 5432}}
print("config['db']['host']                  =", config["db"]["host"])
print("config.get('cache', {}).get('ttl', 60) =", config.get("cache", {}).get("ttl", 60))
print("→ 中间层不存在也不会崩：每层给个 {} 兜底。")

print()
print("-" * 68)
print("本节最小记忆：d[k] 快速失败 / get 容错；in 判存在；items() 遍历；插入有序。")
print("-" * 68)
