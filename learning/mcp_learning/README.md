# MCP + Python SDK 学习资料

一套**从装饰器讲到实战服务器**的中文学习材料。所有 Python 示例都在本机**实际跑通**过，
代码里的注释、输出、坑点记录都来自真实运行结果，而不是抄文档。

```
E:\PyTest\mcp_learning\
├── README.md                ← 你在这里（学习路线图）
├── 00_装饰器\                前置课：不理解装饰器，看 MCP 就是黑魔法
├── 01_MCP概念\               概念篇：先建心智模型，再动手
├── 02_SDK基础\               动手篇：从 15 行服务器到完整客户端
├── 03_进阶\                  进阶篇：结构化输出、lifespan、传输、认证、排错
└── 04_实战项目\              实战：一个完整可用的「个人笔记库」服务器
```

---

## 一、先确认你的环境（已在本机验证）

| 项目 | 值 |
| --- | --- |
| Python | **3.14.7**（`E:\PyTest\.venv`） |
| MCP Python SDK | **2.2.0** |
| 默认协商到的协议版本 | **2026-07-28** |
| 支持的协议版本 | `2024-11-05` / `2025-03-26` / `2025-06-18` / `2025-11-25` / `2026-07-28` |

验证一下：

```powershell
cd E:\PyTest
.\.venv\Scripts\python.exe "mcp_learning\02_SDK基础\00_环境体检.py"
```

看到 `[OK] 端到端冒烟测试通过，环境可用。` 就可以开始了。

如果 `mcp` 没装：

```powershell
.\.venv\Scripts\python.exe -m pip install "mcp[cli]"
```

---

## 二、⚠️ 开始之前必须知道的一件事

**`FastMCP` 已经改名为 `MCPServer`。**

网上 90% 的中文教程还停留在 v1（`from mcp.server.fastmcp import FastMCP`），
照抄会直接报 `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`。

```python
# ✅ v2（本套资料用的，也是你现在装的）
from mcp.server import MCPServer
mcp = MCPServer("Demo")

# ❌ v1（已删除，搜到的老教程都是这个）
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Demo")
```

完整对照见 `03_进阶/05_v1到v2迁移对照.md`。

---

## 三、学习路线（建议按顺序，约 6~10 小时）

### 第 0 站 · 装饰器（1.5 小时）→ `00_装饰器/`

**为什么必须先学**：MCP 里你写的第一行就是 `@mcp.tool()`。
不理解为"装饰器 = 收函数、返回函数"，后面就只是在抄代码。

| 顺序 | 文件 | 学到什么 |
| --- | --- | --- |
| 1 | `01_函数是一等公民.py` | 函数是对象、闭包 —— 装饰器的物理基础 |
| 2 | `02_第一个装饰器.py` | `@deco` 就是 `f = deco(f)`；装饰发生在定义期 |
| 3 | `03_functools_wraps与元信息.py` | 不写 `wraps`，框架就生成不出 JSON Schema |
| 4 | `04_带参数的装饰器.py` | 三层结构 —— `@mcp.tool(name=...)` 的原理 |
| 5 | `05_类装饰器与方法装饰器.py` | 有状态装饰器、装饰类、装饰方法 |
| 6 | `06_异步装饰器.py` | `async def` wrapper，MCP handler 全是 async |
| 7 | **`07_注册表装饰器_连接MCP.py`** | **用纯标准库实现一个迷你 MCP，把前面全串起来** |
| 8 | `08_练习题.py` / `09_练习题参考答案.py` | 5 道题自测 |

### 第 1 站 · MCP 概念（1.5 小时）→ `01_MCP概念/`

| 顺序 | 文件 | 学到什么 |
| --- | --- | --- |
| 1 | `01_MCP是什么.md` | MCP 解决什么问题、和 function calling / LSP 的区别 |
| 2 | `02_架构与协议基础.md` | Host/Client/Server、JSON-RPC 2.0、能力协商、生命周期 |
| 3 | `03_三大原语与传输.md` | **Tools vs Resources vs Prompts 怎么选**、stdio vs HTTP |
| 4 | `04_安全与最佳实践.md` | 用户同意、token 透传禁令、confused deputy |
| 5 | `05_术语速查表.md` | 161 个术语中英对照 |
| 6 | `06_规范版本演进_2026-07-28.md` | 无状态时代改了什么 |
| 附 | `参考_规范逐字摘要.md` | 官方规范逐字中文摘要（写作素材，可当字典查） |

### 第 2 站 · SDK 基础（2~3 小时）→ `02_SDK基础/`

每个 `.py` 都能直接跑：`python 文件名.py` 是**内存自测**，加 `--serve` 才真正启动服务器。

| 顺序 | 文件 | 学到什么 |
| --- | --- | --- |
| 0 | `00_环境体检.py` | 端到端冒烟测试 |
| 1 | `01_安装与环境.md` | 安装、验证、目录约定 |
| 2 | `02_最小服务器.py` | 15 行写出第一个服务器 |
| 3 | `03_工具Tool.py` | 参数 Schema、`Field` 约束、错误处理、注解 |
| 4 | `04_资源Resource.py` | 静态 / 模板 / 二进制 / JSON 资源 |
| 5 | `05_提示Prompt.py` | 单轮 / 多轮提示词、可选参数 |
| 6 | `06_上下文Context.py` | Context 注入、进度、日志、elicitation |
| 7 | `07_客户端Client.py` | 内存 / stdio / HTTP 三种客户端 |
| 8 | `08_测试与pytest.py` | 用 `Client(mcp)` 写测试 |
| 9 | `09_运行与调试.md` | CLI 工具、Inspector、接入 Host |

### 第 3 站 · 进阶（2 小时）→ `03_进阶/`

| 顺序 | 文件 | 学到什么 |
| --- | --- | --- |
| 1 | `01_结构化输出与pydantic.py` | 返回类型 → `structured_content` 实测对照 |
| 2 | `02_lifespan与依赖注入.py` | 数据库连接等重资源的正确姿势 |
| 3 | `03_传输与ASGI挂载.py` | stdio / HTTP / 挂进 FastAPI |
| 4 | `04_认证与授权.md` | OAuth 2.1 + `TokenVerifier` |
| 5 | `05_v1到v2迁移对照.md` | 18 条破坏性变更逐条修法 |
| 6 | `06_调试与排错.md` | 30 行报错速查表 |

### 第 4 站 · 实战（1~2 小时）→ `04_实战项目/`

一个完整的「个人笔记库」服务器：lifespan + 6 工具 + 2 资源模板 + 2 提示词 + 11 个测试。

```powershell
cd E:\PyTest\mcp_learning\04_实战项目
..\..\.venv\Scripts\python.exe server.py          # 看完整流程
..\..\.venv\Scripts\python.exe client.py          # 客户端怎么用
..\..\.venv\Scripts\python.exe test_server.py     # 11 个测试
```

---

## 四、快速开始（30 秒版）

```powershell
cd E:\PyTest\mcp_learning\02_SDK基础
..\..\.venv\Scripts\python.exe "02_最小服务器.py"
```

你会看到 SDK 自动为这个函数生成的 JSON Schema：

```python
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
```

```
input_schema: {'type': 'object',
               'properties': {'a': {'title': 'A', 'type': 'integer'},
                              'b': {'title': 'B', 'type': 'integer'}},
               'required': ['a', 'b'],
               'title': 'addArguments'}
```

**这就是整个 MCP 的核心**：两个类型注解 + 一句 docstring，
框架自动搞定 schema、校验、协议收发。剩下的一切都是围绕它的扩展。

---

## 五、本套资料的"实测结论"清单

这些结论都来自在本机真跑一遍，而不是转述文档 —— 也是最容易踩坑的地方：

| 结论 | 在哪看 |
| --- | --- |
| `MCPServer("x", port=9000)` 直接 TypeError，传输参数只能在 `run()` 里 | `03_进阶/03` |
| 没有 `mcp.http_app()`，正确的是 `streamable_http_app()` | `03_进阶/03` |
| 静态资源（URI 无 `{}`）**不能**注入 `Context`，导入期就报错 | `04_实战项目/README.md` |
| 裸列表/标量返回会被包一层 `{"result": ...}`，pydantic 模型不会 | `03_进阶/01` |
| `ToolError` 的消息原样给模型；未捕获异常被吞成 `Error executing tool x` | `02_SDK基础/03` |
| `progress_callback` 必须是 `async def`，同步函数会在第二次通知时崩 | `02_SDK基础/06` |
| 内存连接**不支持** elicitation（无反向通道），必须 stdio/HTTP + `mode="legacy"` | `02_SDK基础/06` |
| 没配 lifespan 时 `lifespan_context` 是 `{}` 而不是 `None` | `03_进阶/02` |
| 每次 `Client` 连接都会重跑一遍 lifespan | `03_进阶/02` |
| prompt 缺必填参数，客户端只看到 `Internal server error`，真相在服务端 stderr | `02_SDK基础/05` |

---

## 六、学习进度自查

- [ ] 我能解释 `@deco` 展开后是什么
- [ ] 我知道为什么必须写 `functools.wraps`
- [ ] 我能说清 Host / Client / Server 的区别
- [ ] 我能判断一个需求该用 Tool、Resource 还是 Prompt
- [ ] 我能写出一个带参数校验和错误处理的工具
- [ ] 我知道 `content` 和 `structured_content` 的区别
- [ ] 我会用 `Client(mcp)` 给服务器写测试
- [ ] 我知道 stdio 下为什么不能 `print()`
- [ ] 我能把服务器挂进 FastAPI
- [ ] 我读得懂 SDK 的报错日志并知道去哪找原因

---

## 七、官方资源

| 资源 | 链接 |
| --- | --- |
| MCP 官方文档 | https://modelcontextprotocol.io |
| MCP 规范（最新） | https://modelcontextprotocol.io/specification/latest |
| 规范 2025-06-18（多数教程基于此） | https://modelcontextprotocol.io/specification/2025-06-18 |
| Python SDK 文档 | https://py.sdk.modelcontextprotocol.io/ |
| Python SDK v1 文档（旧） | https://py.sdk.modelcontextprotocol.io/v1/ |
| Python SDK 仓库 | https://github.com/modelcontextprotocol/python-sdk |
| MCP Inspector | https://github.com/modelcontextprotocol/inspector |

> 看官方文档时注意页面左上角的**版本选择器** —— 不同版本的协议差异很大，
> 混着看会相互矛盾。
