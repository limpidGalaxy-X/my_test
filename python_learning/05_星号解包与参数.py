"""
05 - 星号 * 与 **：参数、解包、合并，一次讲清

同一个符号，四个位置，四种含义：

  定义函数时：
      def f(*args, **kwargs)      * 收集位置参数成 tuple，** 收集关键字参数成 dict
      def f(a, *, b)              * 后面的参数**只能**用关键字传
      def f(a, /, b)              / 前面的参数**只能**用位置传（3.8+）

  调用函数时：
      f(*seq, **mapping)          * 把序列摊开成位置参数，** 把字典摊开成关键字参数

  赋值时：
      a, *rest = [1, 2, 3]        收集剩下的（结果永远是 list，可以是空列表）
      first, *_, last = seq       常用来"掐头去尾"

  字面量里：
      [*a, *b]  (*a, *b)  {*a, *b}  用 * 展开迭代器
      {**d1, **d2}  d1 | d2         用 ** / | 合并字典（后者键冲突取右边）

运行：
    python 05_星号解包与参数.py
"""

print("=" * 68)
print("1) 定义处：*args 收位置参数，**kwargs 收关键字参数")
print("=" * 68)


def show(a, *args, **kwargs):
    print(f"   a={a!r}  args={args!r}  kwargs={kwargs!r}")


show(1, 2, 3, x=4, y=5)
show(1)
print("→ args 是 tuple，kwargs 是 dict，名字随意（args/kwargs 只是约定）。")


def wrapper_forward(*args, **kwargs):
    """装饰器/中间层里最标准的转发写法。"""
    return show(*args, **kwargs)


print("   转发：")
wrapper_forward(9, 8, k=7)

print()
print("=" * 68)
print("2) 定义处：* 和 / 限制传参方式（写库时非常有用）")
print("=" * 68)


def strict(a, b, /, c, *, d):
    print(f"   a={a} b={b} c={c} d={d}")


strict(1, 2, 3, d=4)
try:
    strict(a=1, b=2, c=3, d=4)
except TypeError as e:
    print("   strict(a=1, ...) →", type(e).__name__, ":", e)
try:
    strict(1, 2, 3, 4)
except TypeError as e:
    print("   strict(1, 2, 3, 4) →", type(e).__name__, ":", e)
print("   → / 左边的 a、b 只能位置传；* 右边的 d 只能关键字传。")

print()
print("=" * 68)
print("3) 调用处：* 摊开序列，** 摊开字典")
print("=" * 68)
nums = [3, 1, 2]
print("print(*nums, sep=' | ') = ", end="")
print(*nums, sep=" | ")
print("max(*nums)              =", max(*nums), " ← 等价于 max(3, 1, 2)")
info = {"c": 3, "d": 4}
strict(1, 2, **info)     # 位置参数照常传，关键字那部分用 ** 摊开
print("矩阵转置 zip(*matrix)   =", list(zip(*[[1, 2, 3], [4, 5, 6]])))
try:
    max(*nums, **{"k": 1})
except TypeError as e:
    print("给不认识的关键字 →", type(e).__name__, ":", e)

print()
print("=" * 68)
print("4) 赋值处：带星号的解包（结果一定是 list）")
print("=" * 68)
a, *rest = [1, 2, 3, 4]
print("a, *rest = [1,2,3,4]     ->", a, rest)
first, *middle, last = "abcdef"
print("first, *middle, last     ->", first, middle, last)
*init, tail = [1]
print("*init, tail = [1]        ->", init, tail, " ← 空的那边是 []")
(x, y), z = (1, 2), 3
print("嵌套解包 (x, y), z       ->", x, y, z)
print("【坑】head, *rest = [] 会报错：至少要有元素喂给 head")
try:
    head, *rest = []
except ValueError as e:
    print("   实际报错 ->", type(e).__name__, ":", e)

print()
print("=" * 68)
print("5) 字面量里合并 / 展开")
print("=" * 68)
print("[*[1, 2], *[3, 4]]        =", [*[1, 2], *[3, 4]])
print("(*[1, 2], *'ab')          =", (*[1, 2], *"ab"))
print("{*[1, 1, 2]}              =", {*[1, 1, 2]}, " ← set 自动去重")
d1, d2 = {"a": 1, "x": 0}, {"a": 2, "b": 3}
print("{**d1, **d2}              =", {**d1, **d2}, " ← 右边覆盖左边")
print("d1 | d2                   =", d1 | d2, " ← 3.9+ 的写法，等价")
print("→ 原字典 d1、d2 都没变：", d1, d2)

print()
print("=" * 68)
print("6) 【最大的坑】默认参数是可变对象")
print("=" * 68)


def bad_append(x, acc=[]):     # 默认值只在定义时创建一次，被所有调用共享
    acc.append(x)
    return acc


print("bad_append(1) =", bad_append(1))
print("bad_append(2) =", bad_append(2), " ← 上一次的结果还在里面！")


def good_append(x, acc=None):
    if acc is None:
        acc = []
    acc.append(x)
    return acc


print("good_append(1) =", good_append(1))
print("good_append(2) =", good_append(2), " ← 正确写法：None 占位，函数内新建")

print()
print("-" * 68)
print("最容易记混的一条：")
print("  定义处 f(*args) = 收集；调用处 f(*args) = 摊开。看到 * 先问：这是哪一边？")
print("-" * 68)
