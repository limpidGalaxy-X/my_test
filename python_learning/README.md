# lambda 与 Python 必备基础知识

一套**只说必备知识**的中文小课程：以 `lambda` 为线索，把函数式写法、
推导式、`key` 函数、星号解包、闭包装饰器、生成器一次串起来。

每个 `.py` 都能**直接运行**（`python 文件名.py`），输出是脚本自己打印的，
注释里的结论都来自在本机的真实运行结果。

```
E:\PyTest\python_learning\
├── README.md                    ← 你在这里（学习路线 + 速查 + 自查）
├── 01_lambda基础.py              lambda 是什么、什么不能做、延迟绑定坑
├── 02_map_filter_reduce.py      函数式三件套 + any/all + 与推导式的性能实测
├── 03_推导式.py                  list/dict/set/生成器表达式 + 惰性省内存实测
├── 04_sorted与key函数.py         key 函数（lambda 出现最多的地方）+ 稳定排序
├── 05_星号解包与参数.py          *args/**kwargs、/ 与 *、解包、合并、可变默认值坑
├── 06_闭包与装饰器.py            闭包、最小装饰器模板、带参数/类装饰器
├── 07_生成器与itertools.py       yield、yield from、itertools 必备清单
├── 08_functools与常用速查.py     partial/lru_cache/Counter/defaultdict/小抄
├── 09_练习题.py                  8 道题 + 自测（打印 PASS/FAIL）
└── 10_练习题参考答案.py           参考答案 + 常见错法
```

---

## 一、环境与运行

本机验证环境：**Python 3.14.7**（虚拟环境 `E:\PyTest\.venv`），只用标准库，无需安装任何包。

```powershell
cd E:\PyTest\python_learning
..\.venv\Scripts\python.exe "01_lambda基础.py"
..\.venv\Scripts\python.exe "09_练习题.py"      # 未实现时会提示"还没实现"
```

---

## 二、学习路线（4~5 小时，按序号读）

| # | 文件 | 学到什么 | 大约 |
| --- | --- | --- | --- |
| 1 | `01_lambda基础.py` | lambda 就是"没有名字的函数表达式"；只能写一个表达式；`add = lambda ...` 是反模式；循环里 lambda 的延迟绑定 | 25 min |
| 2 | `02_map_filter_reduce.py` | `map/filter/reduce` 都是什么、返回什么；`any/all` 短路；**什么时候该改用推导式** | 30 min |
| 3 | `03_推导式.py` | 列表/字典/集合/生成器推导式；过滤 vs 变换；`:=`；生成器省内存 | 35 min |
| 4 | `04_sorted与key函数.py` | `key=` 只收到一个元素；多级排序、降序取负、稳定排序、`itemgetter`、`cmp_to_key` | 35 min |
| 5 | `05_星号解包与参数.py` | 定义处"收集"、调用处"摊开"；`/` 与 `*`；`*rest` 解包；可变默认参数坑 | 30 min |
| 6 | `06_闭包与装饰器.py` | 闭包三要素、`nonlocal`、装饰器四个必须、三层结构 | 40 min |
| 7 | `07_生成器与itertools.py` | `yield` 的暂停/恢复、惰性、一次性、`yield from`、itertools 必备清单 | 35 min |
| 8 | `08_functools与常用速查.py` | `partial/lru_cache/singledispatch`、`Counter/defaultdict/deque`、内置小抄 | 30 min |
| 9 | `09_练习题.py` → `10_练习题参考答案.py` | 8 道题覆盖上面全部内容，自测到 12/12 就算过关 | 40 min |

**想深入装饰器**（类装饰器、异步装饰器、注册表装饰器、迷你 MCP）→ 看
`..\mcp_learning\00_装饰器\`，那边的 `07_注册表装饰器_连接MCP.py` 是进阶版。

---

## 三、一页速查

### 1. lambda 的"能"与"不能"

```python
f = lambda a, b=1, *args, k=2, **kw: a + b     # ✅ 参数写法和 def 一样
f = lambda x: x + 1 if x > 0 else 0            # ✅ 三元表达式
f = lambda x: y = x + 1                        # ❌ 赋值是语句，语法错误

sorted(xs, key=lambda s: s.lower())            # ✅ 正当用途：一次性小函数
add = lambda a, b: a + b                       # ❌ PEP 8：要名字就 def
```

### 2. key 函数（lambda 最高频的用法）

```python
sorted(people, key=lambda p: (-p["age"], p["name"]))   # 多级：降序键取负
sorted(rows, key=itemgetter(1))                        # 取元组第 2 项，不写 lambda
max(xs, key=len, default=None)                         # 空序列给 default
xs.sort(key=..., reverse=True)                         # 原地改，返回 None
```

### 3. 推导式 vs map/filter

```python
[x * 2 for x in xs if x > 0]        # 首选：可读、快
list(map(f, xs))                    # 已有现成函数时（map(int, ...)、map(str.strip, ...)）
sum(x * x for x in xs)              # 聚合直接用生成器，省一次 list
{k: v for k, v in pairs}            # 字典；{x % 3 for x in xs} 是集合（去重）
```

### 4. 星号 `*` 一句话分辨

```python
def f(*args, **kw): ...   # 定义处 = 收集
f(*seq, **mapping)        # 调用处 = 摊开
a, *rest = [1, 2, 3]      # 解包赋值，rest 一定是 list
[*a, *b] / {**d1, **d2}   # 字面量合并（字典也可用 d1 | d2）
def f(a, /, b, *, c)      # / 左只能位置传；* 右只能关键字传
```

### 5. 装饰器骨架

```python
def deco(func):
    @wraps(func)                        # 不写就丢 __name__/__doc__
    def wrapper(*args, **kwargs):       # 不写就转发不了参数
        return func(*args, **kwargs)    # 忘了 return 就变 None
    return wrapper
```

### 6. 生成器

```python
def gen():                 # 函数体里有 yield 就是生成器函数，调用不执行
    yield from other       # 把另一个可迭代对象转接出去
list(islice(count(), 5))   # 无限序列必须截断
```

---

## 四、本套资料的"实测结论"（都在本机跑出来的）

| 结论 | 在哪看 |
| --- | --- |
| 循环里 `[lambda: i for i in range(3)]` 全是 2，要用 `lambda i=i:` 固化 | `01` |
| `pickle` 不了 lambda，`__name__` 是 `<lambda>`、`__doc__` 是 None | `01` |
| `map` / `filter` 返回迭代器，**只能消费一次**，第二次 `list()` 是空的 | `02` |
| Python **3.14 起 `map()` 也支持 `strict=True`**（长度不等直接 `ValueError`） | `02` |
| 同样 1000 个元素 ×2000 轮：`map+lambda` 约 65 ms，推导式约 31 ms | `02` |
| `any()` 到第一个真值就停（后面的元素不会被求值） | `02` |
| 100 万个 int 的列表约 **8.4 MB**，同长度的生成器只要 **200 字节** | `03` |
| 推导式有自己的作用域，循环变量不会泄漏（3.12+ 还被内联，和 for 差距很小） | `03` |
| `key=` 函数**每个元素只调用一次**，所以 key 里放轻量计算是安全的 | `04` |
| `reverse=True` 依然稳定（相等元素保持原顺序），可以拿来做多级排序 | `04` |
| `name.sort()` 返回 `None`，`sorted()` 才返回新列表 | `04` |
| `head, *rest = []` 抛 `ValueError`（星号解包也需要至少一个元素） | `05` |
| `def f(x, acc=[])` 会跨调用累积数据 —— 改用 `acc=None` | `05` |
| 位置限定参数（`/` 左边）**不能**用 `**dict` 传进去 | `05` |
| 不写 `functools.wraps` 时，`__name__` 变成 `wrapper`、`__doc__` 变成 `None` | `06` |
| `lru_cache` 版 `fib(30)` 只真正计算 31 次；参数必须可哈希，传 list 直接 `TypeError` | `08` |
| 生成器遍历第二遍是空的，且不能 `len()` / 索引 | `07` |
| 中文 Windows 控制台是 GBK，**打印 emoji（⚠️✅❌）在输出被重定向时会 `UnicodeEncodeError`**，所以本套资料的 `print` 只用 GBK 能编码的字符（`【坑】`、`→` 都可以） | 全部文件 |

---

## 五、过没过关，自查这 10 条

- [ ] 我能说出 lambda 和 def 的区别，以及为什么 `add = lambda ...` 不好
- [ ] 我知道 `map/filter` 返回迭代器，且只能消费一次
- [ ] 我能一眼看出"该用推导式还是该用 map/filter"
- [ ] 我能写多级排序的 `key`，也知道 `reverse=True` 仍然稳定
- [ ] 我分得清 `*` 在"定义处收集"和"调用处摊开"
- [ ] 我知道可变默认参数的坑和正确写法
- [ ] 我能默写装饰器骨架，并说清 `wraps` / `*args` / `return` 各自少了会怎样
- [ ] 我能解释生成器"惰性 + 一次性"，并知道什么时候不该用它
- [ ] 我用 `next((x for x in xs if 条件), None)` 写过"取第一个满足条件的元素"
- [ ] `python 09_练习题.py` 自测能到 **12/12**

---

## 六、跑一遍全部文件（冒烟测试）

```powershell
cd E:\PyTest\python_learning
Get-ChildItem *.py | ForEach-Object { ..\.venv\Scripts\python.exe $_.FullName | Out-Null; "OK $($_.Name)" }
```

`01`~`08` 是讲解脚本（跑完应无报错），`09` 未做题时显示"还没实现"，
`10` 应打印 `自测结果：12/12 通过`。
