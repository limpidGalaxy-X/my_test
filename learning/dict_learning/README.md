# 字典（dict）学习：键和值各自的要求

一份**只说必备知识**的中文小课程，重点是那句最容易含糊的话：
**键必须可哈希（≈ 不可变），值什么都可以。**

```
E:\PyTest\dict_learning\
├── README.md                    ← 你在这里（路线 + 键值要求对照 + 速查 + 自查）
├── 01_字典基础.py                创建/访问/增删改/遍历/顺序/嵌套
├── 02_键的要求.py                可哈希是什么、黑白名单、1 与 True、NaN、自定义类（重点）
├── 03_值的要求.py                值不限类型 + fromkeys/浅拷贝/None 三个坑（重点）
├── 04_常用惯用法.py              合并、反转、排序、分组、快照、分支表
├── 05_性能与原理.py              哈希表 O(1)、最坏 O(n)、内存开销（实测）
├── 06_练习题.py                  9 道题 + 自测（打印 PASS/FAIL）
└── 07_练习题参考答案.py           参考答案 + 常见错法
```

---

## 一、环境与运行

本机验证环境：**Python 3.14.7**（`E:\PyTest\.venv`），只用标准库。

```powershell
cd E:\PyTest\dict_learning
..\.venv\Scripts\python.exe "01_字典基础.py"
..\.venv\Scripts\python.exe "06_练习题.py"     # 未实现时会提示"还没实现"
```

---

## 二、核心：键和值的要求对照

| 维度 | 键（key） | 值（value） |
| --- | --- | --- |
| 类型限制 | **必须可哈希**（有 `__hash__`） | **没有限制** |
| 能否是可变对象 | ❌ 不行（哈希必须一辈子不变） | ✅ 随便改 |
| list / dict / set / bytearray | ❌ `TypeError: unhashable type` | ✅ 完全可以 |
| 能否重复 | ❌ 必须唯一，重复即覆盖 | ✅ 随便重复 |
| 能否是 `None` | ✅ 可以 | ✅ 可以 |
| 是否参与哈希 | ✅ 是（决定放在哪个桶） | ❌ 否 |
| "相等"怎么算 | `==` 为真 **且** `hash()` 相等；`1`、`1.0`、`True` 是同一个键 | 不影响字典结构 |
| 顺序 | 插入顺序（3.7+），删掉再插跑到最后 | 跟着键走 |
| 能否用它查找 | ✅ `d[k]`，平均 O(1) | ❌ 不能按值查键，要反查得自己建索引 |
| 改动会怎样 | 改掉参与哈希的属性 → **这条记录失联**（查不到也删不掉） | 改值不影响查找 |
| 特例 | `NaN` 可以共存多个（`nan != nan`）；str 的哈希每个进程都不同 | `fromkeys` 的同一个可变值会被所有键共享 |

一句话记忆：**键是不可变的"身份证"，值是随身的"行李"。**

### 键的黑白名单（实测）

| 能当键 | 不能当键 |
| --- | --- |
| `int` `float` `bool` `str` `bytes` `None` | `list` `dict` `set` `bytearray` |
| `tuple`（元素也必须可哈希） | 含 list 的 tuple：`(1, [2])` |
| `frozenset`、`enum`、`date`、函数、类 | 定义了 `__eq__` 但没定义 `__hash__` 的类（`__hash__` 会变成 `None`） |
| `@dataclass(frozen=True)` 的实例 | 普通 `@dataclass` 的实例（`__hash__` 被设为 `None`，不可哈希） |
| 自己写了配套 `__hash__` + `__eq__` 的不可变对象 | 插进字典后又去改属性的对象 |

---

## 三、学习路线（3~4 小时，按序号读）

| # | 文件 | 学到什么 | 大约 |
| --- | --- | --- | --- |
| 1 | `01_字典基础.py` | 五种建法；`d[k]` 快速失败 vs `get` 容错；增删改查；视图是"活的"；插入有序 | 25 min |
| 2 | `02_键的要求.py` | 可哈希的两条契约；黑白名单；`1`/`1.0`/`True` 同键；NaN；自定义类当键的正确与错误写法 | 45 min |
| 3 | `03_值的要求.py` | 值不限类型；`fromkeys` 共享坑；浅拷贝坑；`None` 值与缺键的区分；自引用字典 | 30 min |
| 4 | `04_常用惯用法.py` | 合并 `\|`/`\|=`、反转映射、按值排序 Top-N、分组、键视图集合运算、遍历时改字典、分支表 | 35 min |
| 5 | `05_性能与原理.py` | 哈希表 → O(1)；哈希全冲突退化 O(n)；哈希调用次数；内存开销实测 | 30 min |
| 6 | `06_练习题.py` → `07_练习题参考答案.py` | 9 道题覆盖上面全部内容，自测到 13/13 过关 | 40 min |

**配套**：`lambda 等必备知识` 在 `..\python_learning\`（那边 03 讲推导式、04 讲 `key` 函数、
08 讲 `Counter`/`defaultdict`，和本目录互为补充）。

---

## 四、一页速查

### 1. 键的要求（可哈希）

```python
{1: "a", 1.0: "b", True: "c"}     # -> {1: 'c'}   三者是同一个键
{(1, "a"): 1}                     # ✅ tuple 可以（元素都可哈希）
{frozenset({1, 2}): 1}            # ✅ frozenset 可以
{[1, 2]: 1}                       # ❌ TypeError: unhashable type: 'list'

class P:                          # ✅ 想当键就成对写、且不可变
    __slots__ = ("v",)
    def __init__(self, v): self.v = v
    def __hash__(self): return hash(self.v)
    def __eq__(self, o): return isinstance(o, P) and self.v == o.v

@dataclass(frozen=True)           # ✅ 等价、更省事：只读 + 自动 __eq__ + __hash__
class Point:
    x: int
    y: int
```

### 2. 值的要求（没有要求）

```python
d = {"list": [1, 2], "dict": {"a": 1}, "set": {1}, "none": None, "f": lambda x: x}
d["list"].append(3)               # ✅ 随便改，查找不受影响
{k: [] for k in "abc"}            # ✅ 每个键一份新列表
dict.fromkeys("abc", [])          # ❌ 三个键共享同一个列表！
d.get("a")                        # ⚠️ 分不清"值是 None"和"键不存在" -> 用 in 或哨兵
```

### 3. 八个高频操作

```python
a | b                                  # 合并（右边赢），a |= b 是原地
{k: v for k, v in d.items() if ...}    # 过滤重建（比边遍历边删安全）
sorted(d.items(), key=itemgetter(1))   # 按值排序；值降序键升序用 (-v, k)
defaultdict(list)[k].append(v)         # 分组
Counter(xs)                            # 计数
list(dict.fromkeys(xs))                # 保序去重
d.keys() & other.keys()                # 键视图支持集合运算（values() 不支持）
for k in list(d): del d[k]             # 边遍历边删：先做快照
```

---

## 五、实测结论（都在本机跑出来的）

| 结论 | 在哪看 |
| --- | --- |
| 3.14 的报错写得很直白：`cannot use 'list' as a dict key (unhashable type: 'list')` | `02` |
| 写了 9 个键值对、`len` 只有 8：`True` 和 `1` 是同一个键 | `02` |
| `hash(1) == hash(1.0) == hash(True)`，`hash(0) == hash(False) == hash(0.0)` | `02` |
| `NaN` 作为键：自己查自己成功（先比 id），`float('nan')` 查不到，且多个 NaN 键能共存 | `02` |
| 类里只写 `__eq__` → `__hash__` 变成 `None` → 直接不可哈希 | `02` |
| 当键的对象插入后再改属性 → 查是 `KeyError`，`del` 也是 `KeyError`（记录变孤儿） | `02` |
| 相等但哈希不同 → 永远查不到（自造 bug 第一名） | `02` |
| str 的哈希**每个进程都不同**（哈希随机化），别把 `hash(s)` 持久化 | `02` |
| `dict.fromkeys("abc", [])` 三个键共享同一个列表，append 一个全都变 | `03` |
| `dict(d)` / `d.copy()` 是浅拷贝，改嵌套值会连带改到原字典；`deepcopy` 才独立 | `03` |
| `d.get(k)` 返回 `None` 时无法区分"值是 None"和"键不存在" | `03` |
| 字典可以自引用（`d["self"] = d`），repr 显示成 `{...}`，但 json 序列化会报错 | `03` |
| 键视图支持 `& \| - ^`，值视图不支持 | `04` |
| 遍历时增删 → `RuntimeError: dictionary changed size during iteration` | `04` |
| 同样在 1000 个元素里判断"在不在" ×20000 次：dict 约 0.29 ms，list 约 69 ms（**差 200 多倍**） | `05` |
| 哈希全冲突时一次查找要比较 **1000 次**（= 元素个数），2000 次查找从 0.1 ms 涨到 112 ms | `05` |
| 插入 n 个键调用 n 次 `__hash__`，一次查找只调用 1 次 | `05` |
| 内存：空字典 64 字节、`{'a':1}` 184 字节；100 万条 int→int 字典 40 MB（表本身）、70 MB（含键对象） | `05` |
| 逐个 `del` 不缩容（1000 条撑到 36952 字节后删剩 1 条仍是 36952），`clear()` 才重置回 64 字节 | `05` |

---

## 六、过没过关，自查这 10 条

- [ ] 我能一句话说清"键必须可哈希，值没有要求"
- [ ] 我能列出至少 4 种不能当键的类型，并知道 `tuple` 什么情况下也不行
- [ ] 我知道 `{1: 'a', 1.0: 'b', True: 'c'}` 的结果，并能解释为什么
- [ ] 我能说清只写 `__eq__` 的类为什么不能当键，以及两种修法
- [ ] 我知道键"插入后不能再改"的真正原因（哈希变了就找不回桶）
- [ ] 我知道 `fromkeys` 传可变值的坑，以及正确写法
- [ ] 我能区分"值是 None"和"键不存在"，并说出两种判断办法
- [ ] 我会用 `defaultdict(list)` 分组、`Counter` 计数、`(-v, k)` 做值降序键升序
- [ ] 我知道遍历字典时不能改它，要改就先 `list(d)` 快照或用推导式重建
- [ ] `python 06_练习题.py` 自测能到 **13/13**

---

## 七、跑一遍全部文件（冒烟测试）

```powershell
cd E:\PyTest\dict_learning
Get-ChildItem *.py | ForEach-Object { ..\.venv\Scripts\python.exe $_.FullName | Out-Null; "OK $($_.Name)" }
```

`01`~`05` 是讲解脚本（跑完应无报错），`06` 未做题时显示"还没实现"，
`07` 应打印 `自测结果：13/13 通过`。
