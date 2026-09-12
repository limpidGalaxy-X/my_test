"""
06 - 练习题（先自己写 10 分钟，再看 07_练习题参考答案.py）

9 道题，覆盖：键值基本操作、值→键反转、分组、合并、路径取值、
按值排序、保序去重、可哈希判断、自定义不可变对象当键。

实现完直接运行本文件，会自动跑一遍自测并打印 PASS / FAIL。

运行：
    python "06_练习题.py"
"""

from collections import defaultdict  # noqa: F401  （练习 2、3 会用到）
from dataclasses import dataclass  # noqa: F401  （练习 9 会用到）

# ---------------------------------------------------------------------------
# 练习 1：字符计数（只用普通 dict，不许用 Counter）
#   count_chars("aab") -> {"a": 2, "b": 1}
#   提示：值默认 0，用 d[ch] = d.get(ch, 0) + 1 或者 setdefault
# ---------------------------------------------------------------------------


def count_chars(text):
    raise NotImplementedError("练习 1 还没实现")


# ---------------------------------------------------------------------------
# 练习 2：反转映射（值 -> 键列表）
#   值可能重复，所以结果是 {值: [键, ...]}，并且保持原字典的插入顺序。
#   invert_map({"a": 1, "b": 2, "c": 1}) -> {1: ["a", "c"], 2: ["b"]}
#   提示：defaultdict(list)
# ---------------------------------------------------------------------------


def invert_map(d):
    raise NotImplementedError("练习 2 还没实现")


# ---------------------------------------------------------------------------
# 练习 3：按首字母分组
#   group_by_initial(["apple", "avocado", "banana"])
#     -> {"a": ["apple", "avocado"], "b": ["banana"]}
#   要求返回普通 dict，不是 defaultdict。
# ---------------------------------------------------------------------------


def group_by_initial(words):
    raise NotImplementedError("练习 3 还没实现")


# ---------------------------------------------------------------------------
# 练习 4：合并多个字典并求和（同键相加，不覆盖）
#   merge_sum({"a": 1}, {"a": 2, "b": 3}, {"b": 4}) -> {"a": 3, "b": 7}
#   提示：遍历每个字典的 items()，累加到结果里
# ---------------------------------------------------------------------------


def merge_sum(*dicts):
    raise NotImplementedError("练习 4 还没实现")


# ---------------------------------------------------------------------------
# 练习 5：安全地按路径取值
#   safe_get({"a": {"b": {"c": 1}}}, "a.b.c") -> 1
#   任何一层缺失、或者中间不是字典，都返回 default（默认 None）。
#   提示：path.split(".")，循环里用 isinstance(cur, dict) 判断
# ---------------------------------------------------------------------------


def safe_get(d, path, default=None):
    raise NotImplementedError("练习 5 还没实现")


# ---------------------------------------------------------------------------
# 练习 6：按值排序取前 n
#   top_n({"Ada": 91, "Bob": 78, "Cara": 95, "Dan": 91}, 2)
#     -> [("Cara", 95), ("Ada", 91)]
#   规则：值降序；值相同时键升序。
# ---------------------------------------------------------------------------


def top_n(d, n):
    raise NotImplementedError("练习 6 还没实现")


# ---------------------------------------------------------------------------
# 练习 7：保序去重
#   dedupe(["b", "a", "b", "c"]) -> ["b", "a", "c"]
#   提示：dict.fromkeys 保持插入顺序，还可以用 dict 做"已见过"的集合
# ---------------------------------------------------------------------------


def dedupe(items):
    raise NotImplementedError("练习 7 还没实现")


# ---------------------------------------------------------------------------
# 练习 8：判断一个对象能不能当字典键
#   can_be_key((1, 2)) -> True      can_be_key([1, 2]) -> False
#   提示：hash() 会抛 TypeError；不要用一堆 isinstance 硬编码
# ---------------------------------------------------------------------------


def can_be_key(obj):
    raise NotImplementedError("练习 8 还没实现")


# ---------------------------------------------------------------------------
# 练习 9：自己造一个能当键的类型
#   make_point(1, 2) 返回的实例要能当字典键，并且"内容相同的两个实例"
#   必须是同一个键：{make_point(1, 2): "v"}[make_point(1, 2)] == "v"
#   提示：@dataclass(frozen=True) 会自动生成配套的 __hash__ 和 __eq__
# ---------------------------------------------------------------------------


def make_point(x, y):
    raise NotImplementedError("练习 9 还没实现")


# ===========================================================================
# 自测（不用改下面）
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
    if passed == total:
        print("全部通过，可以去做 07_练习题参考答案.py 对照写法了。")
    else:
        print("先别急着看答案，对着 FAIL 的提示再想想。")


if __name__ == "__main__":
    run_tests()
