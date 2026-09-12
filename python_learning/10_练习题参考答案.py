"""
10 - 练习题参考答案

先自己写，再看这里。每题给出写法 + "为什么这么写 / 常见错法"。

运行：
    python "10_练习题参考答案.py"
"""

from collections import Counter
from functools import wraps


# ---------------------------------------------------------------------------
# 练习 1：多级排序
#   key 返回元组 = 依次比较；降序的数字取负，比 reverse=True 更灵活
#   （reverse=True 会把**所有**键一起反向）。
# ---------------------------------------------------------------------------


def sort_people(people):
    return sorted(people, key=lambda p: (-p["age"], p["name"]))


# 常见错法：
#   people.sort(key=...)      原地改，违反了"不修改原列表"，而且返回 None
#   sorted(people, key=..., reverse=True)
#       -> age 降序了，但 age 相同的 name 也变成降序，测试会 FAIL


# ---------------------------------------------------------------------------
# 练习 2：词频 Top-N
#   先 Counter 数数，再用 (-次数, 单词) 排序取前 n。
#   只写 most_common(n) 在"次数相同"时按插入顺序，结果不稳定。
# ---------------------------------------------------------------------------


def top_words(text, n):
    counts = Counter(text.split())
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


# ---------------------------------------------------------------------------
# 练习 3：闭包工厂
#   外层函数的局部变量 rate 被内层函数引用，于是"活"在被返回的函数里。
# ---------------------------------------------------------------------------


def make_discount(rate):
    def apply(price):
        return round(price * rate, 2)

    return apply


# 等价写法：return lambda price: round(price * rate, 2)
# 注意：不要写 def apply(price, rate=rate) 之外忘了返回内层函数。


# ---------------------------------------------------------------------------
# 练习 4：组合函数
#   lambda 最适合这种"一次性小函数"。
# ---------------------------------------------------------------------------


def compose(f, g):
    return lambda x: f(g(x))


# 注意顺序：compose(f, g)(x) == f(g(x))，先 g 后 f。


# ---------------------------------------------------------------------------
# 练习 5：推导式
# ---------------------------------------------------------------------------


def pick_and_upper(words, min_len):
    return [w.upper() for w in words if len(w) >= min_len]


# 常见错法：[w.upper() if len(w) >= min_len for w in words]
#           -> else 分支缺失会得到 None 混进结果里，语法上也必须写成三元。


# ---------------------------------------------------------------------------
# 练习 6：第一个满足条件的元素
#   生成器表达式 + next 的默认值 = 短路 + 兜底，比 for 循环三行都短。
# ---------------------------------------------------------------------------


def first_over(xs, limit):
    return next((x for x in xs if x > limit), None)


# 提示：如果调用方传的是生成器，这个写法同样正确（惰性，不会先 list 出来）。


# ---------------------------------------------------------------------------
# 练习 7：生成器函数
#   函数体里有 yield（或 yield from）就是生成器函数，调用它只是拿到生成器对象。
# ---------------------------------------------------------------------------


def flatten_and_double(matrix):
    for row in matrix:
        yield from (x * 2 for x in row)


# 等价写法：双层 for + yield
#   for row in matrix:
#       for x in row:
#           yield x * 2
# 常见错法：把结果 append 进 list 再 return -> 那返回的是 list，7b 会 FAIL。


# ---------------------------------------------------------------------------
# 练习 8：装饰器 @count_calls
#   状态挂在 wrapper 的函数属性上，代码最短；用 wraps 保住元信息。
# ---------------------------------------------------------------------------


def count_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.count += 1
        return func(*args, **kwargs)

    wrapper.count = 0
    return wrapper


# 也可以把计数存到闭包变量里（需要 nonlocal），或者用类装饰器：
#   class CountCalls: ... 见 06_闭包与装饰器.py


# ===========================================================================
# 自测（和 09_练习题.py 完全一致，用来验证答案）
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


if __name__ == "__main__":
    run_tests()
