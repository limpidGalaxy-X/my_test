# 00 · 装饰器（Decorator）

> 这是学 MCP 之前的**必修前置课**。
> 因为 MCP 里你写的第一行代码就是 `@mcp.tool()`，而它就是一个装饰器。

---

## 一、为什么必须先学装饰器

MCP 服务器的全部写法，本质上就是「**给函数贴标签**」：

```python
from mcp.server import MCPServer

mcp = MCPServer("Demo")

@mcp.tool()                    # ← 装饰器：把这个函数登记成"工具"
def add(a: int, b: int) -> int:
    """Add two numbers."""     # ← docstring 变成工具描述
    return a + b
```

这 6 行背后发生了 6 件事，全部由装饰器完成：

| 步骤 | 谁做的 |
| --- | --- |
| 1. 接收 `add` 这个函数对象 | 装饰器 |
| 2. 读取 `a: int, b: int` 类型注解 | 反射（`inspect` / `typing`） |
| 3. 生成 JSON Schema `{"a": "integer", "b": "integer"}` | `pydantic` |
| 4. 取 docstring 当描述 | 函数对象属性 |
| 5. 存进内部注册表 `{"add": (...)}` | 装饰器的闭包/对象状态 |
| 6. 客户端 `tools/list` 时把注册表吐出去 | 注册表 |

**不理解装饰器，这 6 步就是黑魔法；理解了，它就是 40 行代码。**
本目录的 `07_注册表装饰器_连接MCP.py` 会用纯标准库把它实现出来。

---

## 二、学习顺序（按序号读，每个文件都能直接跑）

| 文件 | 内容 | 关键收获 |
| --- | --- | --- |
| `01_函数是一等公民.py` | 函数是对象、元数据、闭包 | 装饰器的物理基础 |
| `02_第一个装饰器.py` | `@deco` 语法糖、装饰时机、叠加顺序 | `f = deco(f)` |
| `03_functools_wraps与元信息.py` | `__name__` / `__doc__` / `__wrapped__` | **不写 wraps 框架就废了** |
| `04_带参数的装饰器.py` | 三层结构、可选参数写法 | `@mcp.tool(name=...)` 的原理 |
| `05_类装饰器与方法装饰器.py` | `__call__`、装饰类、装饰方法 | 有状态装饰器 |
| `06_异步装饰器.py` | `async def` wrapper、同步/异步通吃 | MCP handler 都是 async |
| `07_注册表装饰器_连接MCP.py` | 迷你版 MCP 服务器 | **把前面全部串起来** |
| `08_练习题.py` | 5 道题 + 自测 | 检验是否真会 |
| `09_练习题参考答案.py` | 参考答案 | 对照写法 |

运行任意一个：

```powershell
cd E:\PyTest\mcp_learning\00_装饰器
python "01_函数是一等公民.py"
python "08_练习题.py"          # 未实现时会提示 "还没实现"
```

---

## 三、一页速查

### 1. 最小模板（无参装饰器）

```python
import functools

def deco(func):
    @functools.wraps(func)              # 必须！否则元信息丢失
    def wrapper(*args, **kwargs):       # 必须！否则参数转发不了
        # before ...
        result = func(*args, **kwargs)  # 必须！
        # after ...
        return result                   # 必须！
    return wrapper
```

### 2. 带参数的装饰器（三层）

```python
def deco(arg1, arg2=...):               # 第 1 层：装饰器参数
    def decorator(func):                # 第 2 层：被装饰函数
        @functools.wraps(func)
        def wrapper(*args, **kwargs):   # 第 3 层：调用参数
            return func(*args, **kwargs)
        return wrapper
    return decorator

@deco("x", arg2=1)                      # 注意括号！
def f(): ...
```

### 3. 异步版本

```python
def deco(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)      # async wrapper 里必须 await
    return wrapper
```

### 4. 四个必须记住的坑

| 坑 | 症状 | 解决 |
| --- | --- | --- |
| 不写 `functools.wraps` | `__name__` 全是 `wrapper`，框架生成不出 schema | 永远加上 |
| wrapper 不写 `*args, **kwargs` | `TypeError: wrapper() takes 0 positional arguments` | 永远加上 |
| wrapper 不 `return` | 被装饰函数返回值变成 `None` | 永远 `return` |
| 同步装饰器包 `async def` 函数 | 拿到的是 coroutine 而不是结果 | wrapper 也用 `async def` + `await` |

---

## 四、自测：能答出这 5 题就算过关

1. `@deco` 放在 `def f()` 上面，等价于哪一行普通代码？
2. 装饰器在什么时候执行——函数定义时，还是函数调用时？
3. 下面两段输出一样吗？为什么？
   ```python
   @a
   @b
   def f(): ...
   ```
4. 为什么说"没有 `functools.wraps`，MCP 工具就生成不出正确的参数 Schema"？
5. 写一个 `@mcp.tool()` 风格的注册表装饰器，最小需要哪几个组成部分？

<details>
<summary>参考答案</summary>

1. `f = deco(f)`
2. **定义时**（模块导入时），每个函数只装饰一次；调用时执行的是 wrapper。
3. 不一样。等价于 `f = a(b(f))`，`b` 先包，`a` 后包，所以 `a` 在最外层、最先执行 before 逻辑。
4. 因为框架靠 `inspect.signature()` 读参数名和类型注解来生成 JSON Schema；不写 `wraps` 时 `signature` 只能看到 `(*args, **kwargs)`，Schema 就退化成空对象。
5. ① 一个保存工具的容器（注册表）；② 一个收参数的工厂函数；③ 反射签名 → 生成 Schema；④ 把 `名字 -> 函数/Schema/描述` 存进容器。

</details>

---

下一站：`../01_MCP概念/README.md`
