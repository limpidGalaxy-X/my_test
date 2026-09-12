"""
02 - 键的要求：可哈希（hashable）到底是什么

一句话：**键必须是可哈希的**，而"可哈希"在日常使用中就等于"不可变"。

可哈希 = 满足两条：
  ① 有 __hash__() 能算出一个整数，并且这个值在对象存活期间**不能变**；
  ② 相等（==）的对象，哈希值必须相等（哈希契约）。
不满足第一条 -> 放不进字典（TypeError）；不满足第二条 -> 能放进去但**永远查不到**。

所以：
    可以当键：int / float / bool / str / bytes / None / tuple(元素都可哈希) /
              frozenset / 函数 / 类 / 枚举 / date / 你自己实现了 __hash__ 的不可变对象
    不能当键：list / dict / set / bytearray / 任何"插入后还能被改"的对象

值没有任何这类要求（见 03）。

运行：
    python 02_键的要求.py
"""

print("=" * 68)
print("1) 黑名单实测：这些类型当键直接 TypeError")
print("=" * 68)
for bad in ([1, 2], {"a": 1}, {1, 2}, bytearray(b"x"), (1, [2])):
    try:
        {bad: "值"}
    except TypeError as e:
        print(f"   {type(bad).__name__:<10} -> {e}")
print("→ 注意最后一行：tuple 本身可以当键，但里面套了 list 就整体不可哈希（按内容逐层检查）。")

print()
print("=" * 68)
print("2) 白名单实测：这些都可以当键")
print("=" * 68)
allowed = {
    1: "int",
    3.14: "float",
    True: "bool",
    "s": "str",
    b"b": "bytes",
    None: "None",
    (1, "a"): "tuple",
    frozenset({1, 2}): "frozenset",
    len: "内置函数",
}
print("   一共写进去 9 个键值对，len 却是", len(allowed), "：因为 True 和 1 是同一个键（见第 3 节）")
print("   剩下的键类型有：", sorted({type(k).__name__ for k in allowed}))
print("   (1, 'a') 查得到:", allowed[(1, "a")], " frozenset({2,1}) 也查得到:", allowed[frozenset({1, 2})])
print("→ tuple 按内容比较，frozenset 无视顺序，所以它们都能当键。")

print()
print("=" * 68)
print("3) 数字形键会自动合并：1 / 1.0 / True 是同一个键")
print("=" * 68)
print("{1: 'int', 1.0: 'float', True: 'bool'} =", {1: "int", 1.0: "float", True: "bool"})
print("hash(1) == hash(1.0) == hash(True)   =", hash(1) == hash(1.0) == hash(True))
print("hash(0) == hash(False) == hash(0.0)  =", hash(0) == hash(False) == hash(0.0))
print("{True: 'a', 2: 'b'}[1]              =", {True: "a", 2: "b"}[1])
print("→ 因为 1 == 1.0 == True，字典认为它们是同一个键，后写的覆盖先写的。")
print("  坑：用 0/1 当键、用 False/True 当键混在一起时，会互相踩。")

print()
print("=" * 68)
print("4) 怪例：NaN 作键（自己查自己行，别的 NaN 查不到）")
print("=" * 68)
nan = float("nan")
d = {nan: "第一个 nan"}
print("d[nan] 查得到（同一个对象，字典先比 id）:", d[nan])
try:
    d[float("nan")]
except KeyError:
    print("d[float('nan')] -> KeyError（因为 nan != nan）")
d[float("nan")] = "第二个 nan"
print("于是字典里可以同时存在多个 nan 键，len =", len(d), " 值 =", list(d.values()))
print("→ 结论：别用 NaN/复杂浮点当键。")

print()
print("=" * 68)
print("5) 自定义类当键：默认按 id 哈希（两个内容相同的实例是两个键）")
print("=" * 68)


class Box:
    def __init__(self, v):
        self.v = v


b1, b2 = Box(1), Box(1)
d = {b1: "x"}
print("b1 == b2 ?", b1 == b2, " b1 in d:", b1 in d, " b2 in d:", b2 in d)

print()
print("=" * 68)
print("6) 只定义了 __eq__ 的类：__hash__ 自动变成 None，直接不可哈希")
print("=" * 68)


class EqBox:
    def __init__(self, v):
        self.v = v

    def __eq__(self, other):
        return isinstance(other, EqBox) and self.v == other.v


print("EqBox.__hash__ =", EqBox.__hash__)
try:
    {EqBox(1): "x"}
except TypeError as e:
    print("   ->", e)
print("→ 原因：可变对象改了内容后哈希会变，Python 干脆把 __hash__ 置空，")
print("  逼你明确表态。两种修法：自己写 __hash__，或用 @dataclass(frozen=True)。")

from dataclasses import dataclass


@dataclass(frozen=True)
class FrozenPoint:
    x: int
    y: int


print("   修法演示（frozen dataclass）：", {FrozenPoint(1, 2): "v"}[FrozenPoint(1, 2)],
      " ← 属性只读 + 自动生成配套的 __eq__ 和 __hash__")
try:
    FrozenPoint(1, 2).x = 9
except Exception as e:
    print("   想改属性 ->", type(e).__name__, ":", e, " ← 想变哈希也变不了，天然安全")

print()
print("=" * 68)
print("7) 正确写法：内容相同即同一个键（不可变 + 一致的 __hash__/__eq__）")
print("=" * 68)


class KeyBox:
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __hash__(self):
        return hash(self.v)

    def __eq__(self, other):
        return isinstance(other, KeyBox) and self.v == other.v


k = KeyBox((1, 2))
d = {k: "值"}
print("用等值的另一个实例查:", d[KeyBox((1, 2))])
print("→ 契约：__eq__ 说相等，__hash__ 就必须给出同一个哈希。")

print()
print("=" * 68)
print("8) 键的哈希必须「不变」：插入后改掉参与哈希的属性会失联")
print("=" * 68)
k.v = (9, 9)
try:
    d[k]
except KeyError:
    print("改了 k.v 之后再查 k -> KeyError（哈希变了，找不回原来那个桶）")
try:
    del d[k]
except KeyError:
    print("想删也删不掉 -> KeyError（这条记录成了孤儿，但 len(d) 仍然是", len(d), "）")
print("→ 这就是「键必须不可变」的真正含义：不是语法限制，是哈希表的物理要求。")

print()
print("=" * 68)
print("9) 相等但哈希不同 = 永远查不到（最常见的自造 bug）")
print("=" * 68)


class Broken:
    def __init__(self, v):
        self.v = v

    def __eq__(self, other):
        return isinstance(other, Broken) and self.v == other.v

    __hash__ = object.__hash__      # 故意只按 id 哈希，违反契约


x, y = Broken(1), Broken(1)
print("x == y =", x == y, "  hash(x) == hash(y) =", hash(x) == hash(y))
d = {x: "x 的值"}
try:
    d[y]
except KeyError:
    print("d[y] -> KeyError：明明相等，却因为哈希不同被分到别的桶里")
print("→ 排查口诀：自定义类要当键 __eq__ 和 __hash__ 必须成对写、且同源。")

print()
print("=" * 68)
print("10) 字符串哈希每次进程都不一样（哈希随机化），别持久化 hash 值")
print("=" * 68)
import subprocess
import sys

outs = [
    subprocess.run(
        [sys.executable, "-c", "print(hash('abc'))"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    for _ in range(2)
]
print("本文件所在进程的 hash('abc') =", hash("abc"))
print("另起两个 Python 进程算出来的 =", outs[0], "和", outs[1])
print("两次一样吗？", outs[0] == outs[1], " ← 不一样，这是防哈希碰撞攻击的设计")
print("→ 所以：不要把 hash(s) 存进数据库/文件当标识，换进程就失效。")

print()
print("-" * 68)
print("键的要求速记：")
print("  1. 可哈希 = 不可变 + 一致；list/dict/set/bytearray 一律不行；")
print("  2. 元组可以，但元素必须都可哈希；frozenset 可以；")
print("  3. 1 / 1.0 / True 是同一个键，0 / 0.0 / False 也是；")
print("  4. 自定义类当键：__hash__ 与 __eq__ 必须同源，且属性别再改；")
print("  5. 拿不准就用 str/int/tuple/frozenset 这类内置不可变类型当键。")
print("-" * 68)
