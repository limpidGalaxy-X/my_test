"""
07 - 练习题参考答案

先自己写，再看这里。每题给出写法 + "为什么这么写 / 常见错法"。

运行：
    python "07_练习题参考答案.py"
"""

from collections import defaultdict
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 练习 1：字符计数
#   普通 dict 做累加，键是字符（str，可哈希），值是次数（int）。
# ---------------------------------------------------------------------------


def count_chars(text):
    counts = {}
    for ch in text:
        counts[ch] = counts.get(ch, 0) + 1
    return counts


# 等价写法：counts[ch] = counts.setdefault(ch, 0) + 1
# 更省事    ：from collections import Counter; Counter(text)
# 常见错法  ：counts[ch] += 1  -> 第一次遇到该字符就 KeyError


# ---------------------------------------------------------------------------
# 练习 2：反转映射
#   注意"值 -> 键"反转后，原来的**值成了键**，所以要求值本身可哈希；
#   值重复不能覆盖，必须用 list 收集。
# ---------------------------------------------------------------------------


def invert_map(d):
    out = defaultdict(list)
    for k, v in d.items():
        out[v].append(k)
    return dict(out)


# 常见错法：{v: k for k, v in d.items()}  -> 值重复时前面的键被丢掉


# ---------------------------------------------------------------------------
# 练习 3：按首字母分组
# ---------------------------------------------------------------------------


def group_by_initial(words):
    out = defaultdict(list)
    for w in words:
        out[w[0]].append(w)
    return dict(out)


# 返回 dict(out) 是为了去掉 defaultdict 的"缺键自动建"行为，
# 避免调用方拿到一个会偷偷长出新键的字典。


# ---------------------------------------------------------------------------
# 练习 4：合并求和
#   不能用 |= 或 dict(a, **b)，那些是"覆盖"而不是"相加"。
# ---------------------------------------------------------------------------


def merge_sum(*dicts):
    out = {}
    for d in dicts:
        for k, v in d.items():
            out[k] = out.get(k, 0) + v
    return out


# 变体：值不是数字而是列表时，用 out.setdefault(k, []).extend(v)


# ---------------------------------------------------------------------------
# 练习 5：按路径安全取值
#   每一层都要确认"当前是字典"且"键存在"，否则直接返回默认值。
# ---------------------------------------------------------------------------


def safe_get(d, path, default=None):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


# 常见错法：d.get(part).get(...) 链 -> 中间是 None 时 AttributeError；
#           try: ... except KeyError -> 中间是 list 时又漏了 TypeError。


# ---------------------------------------------------------------------------
# 练习 6：按值排序取前 n
#   值降序用 -kv[1]（不要用 reverse=True，否则"值相同时键升序"会变成降序）。
# ---------------------------------------------------------------------------


def top_n(d, n):
    return sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


# 数据量特别大时用 heapq.nlargest(n, d.items(), key=itemgetter(1)) 更省内存。


# ---------------------------------------------------------------------------
# 练习 7：保序去重
#   dict 的键天然唯一且保持插入顺序，所以 dict.fromkeys 就是"保序去重"。
# ---------------------------------------------------------------------------


def dedupe(items):
    return list(dict.fromkeys(items))


# 元素必须可哈希（不可哈希的话用 [x for i, x in enumerate(items) if x not in items[:i]]，
# 但那是 O(n²)，一般说明数据结构选错了）。


# ---------------------------------------------------------------------------
# 练习 8：判断能否当字典键
#   直接问 Python：hash() 会抛 TypeError 就是不能。
# ---------------------------------------------------------------------------


def can_be_key(obj):
    try:
        hash(obj)
    except TypeError:
        return False
    return True


# 注意：这里只判断"可哈希"，不判断"哈希是否稳定"。
# 一个定义了自己 __hash__、但属性可变的类，能通过这个检查，
# 然而插入后再改属性照样查不到（见 02 的第 8 节）。


# ---------------------------------------------------------------------------
# 练习 9：能当键的自定义类型
#   frozen=True 同时做三件事：属性只读、自动生成 __eq__、自动生成 __hash__。
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Point:
    x: int
    y: int


def make_point(x, y):
    return Point(x, y)


# 手写等价物（不想用 dataclass 时）：
#   class Point:
#       __slots__ = ("x", "y")
#       def __init__(self, x, y): self.x, self.y = x, y
#       def __hash__(self): return hash((self.x, self.y))
#       def __eq__(self, o): return isinstance(o, Point) and (self.x, self.y) == (o.x, o.y)
# 常见错法：@dataclass 不加 frozen -> __hash__ 是 None -> TypeError: unhashable type


# ===========================================================================
# 自测（和 06_练习题.py 完全一致，用来验证答案）
# ===========================================================================


def _run(label, thunk, expected):
    try:
        got = thunk()
    except NotImplementedError as e:
        print(f"[ -- ] {label}  （{e}）")
        return False
    except Exception as e:
        print(f"[FAIL] {label}  抛异常 {type(e).__name__}: {e}")
        return False
    if got == expected:
        print(f"[PASS] {label}")
        return True
    print(f"[FAIL] {label}\n        期望: {expected!r}\n        实际: {got!r}")
    return False


def run_tests():
    cases = [
        ("1  count_chars", lambda: count_chars("aab"), {"a": 2, "b": 1}),
        (
            "2  invert_map 值可重复",
            lambda: invert_map({"a": 1, "b": 2, "c": 1}),
            {1: ["a", "c"], 2: ["b"]},
        ),
        (
            "3  group_by_initial",
            lambda: group_by_initial(["apple", "avocado", "banana"]),
            {"a": ["apple", "avocado"], "b": ["banana"]},
        ),
        (
            "4  merge_sum 同键相加",
            lambda: merge_sum({"a": 1}, {"a": 2, "b": 3}, {"b": 4}),
            {"a": 3, "b": 7},
        ),
        ("5  safe_get 命中", lambda: safe_get({"a": {"b": {"c": 1}}}, "a.b.c"), 1),
        ("5b safe_get 中间缺失", lambda: safe_get({"a": {"b": {}}}, "a.x.y"), None),
        ("5c safe_get 自定义默认值", lambda: safe_get({}, "a.b", default=-1), -1),
        (
            "6  top_n 值降序键升序",
            lambda: top_n({"Ada": 91, "Bob": 78, "Cara": 95, "Dan": 91}, 2),
            [("Cara", 95), ("Ada", 91)],
        ),
        ("7  dedupe 保序去重", lambda: dedupe(["b", "a", "b", "c"]), ["b", "a", "c"]),
        ("8  can_be_key 元组", lambda: can_be_key((1, 2)), True),
        ("8b can_be_key 列表", lambda: can_be_key([1, 2]), False),
        ("8c can_be_key 字典", lambda: can_be_key({"a": 1}), False),
        ("9  make_point 可作键", lambda: {make_point(1, 2): "v"}[make_point(1, 2)], "v"),
    ]

    passed = sum(_run(*c) for c in cases)
    total = len(cases)

    print()
    print(f"自测结果：{passed}/{total} 通过")


if __name__ == "__main__":
    run_tests()
