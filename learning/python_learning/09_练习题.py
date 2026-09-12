"""
09 - 练习题（先自己写 10 分钟，再看 10_练习题参考答案.py）

每题都给了空函数（里面 raise NotImplementedError），实现完直接运行本文件，
会自动跑一遍自测并打印 PASS / FAIL。

覆盖：lambda / key 函数 / 推导式 / 闭包 / 生成器 / 装饰器

运行：
    python "09_练习题.py"
"""

from collections import Counter  # noqa: F401  （练习 2 会用到）
from functools import wraps  # noqa: F401  （练习 8 会用到）

# ---------------------------------------------------------------------------
# 练习 1：多级排序
#   返回按 age 降序、age 相同按 name 升序排好的新列表。
#   要求：不能修改传进来的 people。
#   提示：sorted(people, key=lambda p: (...))
# ---------------------------------------------------------------------------


def sort_people(people):
    raise NotImplementedError("练习 1 还没实现")


# ---------------------------------------------------------------------------
# 练习 2：词频 Top-N
#   返回出现次数最多的前 n 个 (单词, 次数)。
#   排序规则：次数降序；次数相同时按单词升序（保证结果稳定可预期）。
#   提示：Counter(text.split()) 然后 sorted(..., key=lambda kv: (-kv[1], kv[0]))
# ---------------------------------------------------------------------------


def top_words(text, n):
    raise NotImplementedError("练习 2 还没实现")


# ---------------------------------------------------------------------------
# 练习 3：闭包工厂
#   make_discount(0.8) 返回一个函数，输入原价返回打 8 折后的价格（保留 2 位小数）。
#   提示：外层函数接收 rate，内层函数用 nonlocal/闭包引用它，返回内层函数。
# ---------------------------------------------------------------------------


def make_discount(rate):
    raise NotImplementedError("练习 3 还没实现")


# ---------------------------------------------------------------------------
# 练习 4：组合函数
#   compose(f, g) 返回一个新函数 h，满足 h(x) == f(g(x))。
#   提示：直接 return lambda x: ...
# ---------------------------------------------------------------------------


def compose(f, g):
    raise NotImplementedError("练习 4 还没实现")


# ---------------------------------------------------------------------------
# 练习 5：推导式（过滤 + 变换一次完成）
#   从 words 里挑出长度 >= min_len 的，全部转成大写，返回 list。
#   提示：一个列表推导式搞定，用一行。
# ---------------------------------------------------------------------------


def pick_and_upper(words, min_len):
    raise NotImplementedError("练习 5 还没实现")


# ---------------------------------------------------------------------------
# 练习 6：第一个满足条件的元素
#   返回 xs 中第一个大于 limit 的元素；不存在返回 None。
#   要求：找到就立刻停止（不要遍历完），并且 xs 可能是生成器。
#   提示：next((x for x in xs if x > limit), None)
# ---------------------------------------------------------------------------


def first_over(xs, limit):
    raise NotImplementedError("练习 6 还没实现")


# ---------------------------------------------------------------------------
# 练习 7：生成器函数
#   把二维列表展平，并且每个元素乘 2；必须是**生成器**（惰性），不是 list。
#   提示：def 里用 for + yield from，或者双层 for + yield
# ---------------------------------------------------------------------------


def flatten_and_double(matrix):
    raise NotImplementedError("练习 7 还没实现")


# ---------------------------------------------------------------------------
# 练习 8：装饰器 @count_calls
#   给函数加一个 .count 属性，记录被调用次数；调用返回值必须原样返回；
#   并且必须保留原函数的 __name__（用 functools.wraps）。
# ---------------------------------------------------------------------------


def count_calls(func):
    raise NotImplementedError("练习 8 还没实现")


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
    people = [
        {"name": "Ada", "age": 36},
        {"name": "Bob", "age": 25},
        {"name": "Cara", "age": 36},
    ]
    original = [dict(p) for p in people]

    cases = [
        (
            "1  sort_people 多级排序",
            lambda: sort_people(people),
            [
                {"name": "Ada", "age": 36},
                {"name": "Cara", "age": 36},
                {"name": "Bob", "age": 25},
            ],
        ),
        # 先跑一次 sort_people，再检查原列表有没有被改动
        ("1b sort_people 不修改原列表", lambda: (sort_people(people), people == original)[1], True),
        (
            "2  top_words Top-N",
            lambda: top_words("the cat the dog the bird cat", 2),
            [("the", 3), ("cat", 2)],
        ),
        ("3  make_discount 闭包", lambda: make_discount(0.8)(100), 80.0),
        ("4  compose(f, g)", lambda: compose(lambda x: x + 1, lambda x: x * 2)(5), 11),
        (
            "5  pick_and_upper 推导式",
            lambda: pick_and_upper(["hi", "python", "lambda", "go"], 4),
            ["PYTHON", "LAMBDA"],
        ),
        ("6  first_over 命中", lambda: first_over([1, 5, 9], 4), 5),
        ("6b first_over 未命中返回 None", lambda: first_over([1, 2], 4), None),
        ("7  flatten_and_double 结果", lambda: list(flatten_and_double([[1, 2], [3]])), [2, 4, 6]),
        (
            "7b flatten_and_double 真的是生成器",
            lambda: hasattr(flatten_and_double([[1]]), "__next__"),
            True,
        ),
    ]

    passed = sum(_run(*c) for c in cases)
    total = len(cases)

    print()
    print("练习 8：@count_calls")
    try:

        @count_calls
        def greet(name):
            return f"hi {name}"

        r1, r2 = greet("a"), greet("b")
        total += 2
        if r1 == "hi a" and r2 == "hi b" and getattr(greet, "count", None) == 2:
            print("[PASS] 8  count_calls 计数与返回值")
            passed += 1
        else:
            print(f"[FAIL] 8  count_calls 计数与返回值: r1={r1!r} r2={r2!r} count={getattr(greet,'count',None)!r}")
        if greet.__name__ == "greet":
            print("[PASS] 8b count_calls 保留 __name__")
            passed += 1
        else:
            print(f"[FAIL] 8b count_calls 保留 __name__: {greet.__name__!r}")
    except NotImplementedError as e:
        total += 2
        print(f"[ -- ] 练习 8  （{e}）")
    except Exception as e:
        total += 2
        print(f"[FAIL] 练习 8  抛异常 {type(e).__name__}: {e}")

    print()
    print(f"自测结果：{passed}/{total} 通过")
    if passed == total:
        print("全部通过，可以去做 10_练习题参考答案.py 对照写法了。")
    else:
        print("先别急着看答案，对着 FAIL 的提示再想想。")


if __name__ == "__main__":
    run_tests()
