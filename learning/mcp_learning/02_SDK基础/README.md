# 02 · Python SDK 基础（动手篇）

> 前置：已读完 `01_MCP概念/`，且已理解装饰器（`00_装饰器/`）。
> 本篇所有代码基于 **MCP Python SDK v2**（`mcp>=2.2.0`，2026-09 当前稳定版）。

---

## 一、先记住这三条（v1 教程会把你带偏）

| 你以为 | 实际上是 |
| --- | --- |
| `from mcp.server.fastmcp import FastMCP` | **已删除**。用 `from mcp.server import MCPServer` |
| `from mcp import FastMCP` | 从来没有过 |
| `ctx.info()` / `ctx.progress()` | `ctx.info()` 已废弃（用标准库 `logging`）；进度是 `await ctx.report_progress(...)` |

> **FastMCP 改名为 MCPServer** 是 v2 最大的破坏性变更。
> 你在网上搜到的 90% 教程还是 v1 写法（`FastMCP`）。看到 `FastMCP` 就知道那篇是旧文。

完整的 v1 → v2 对照见 `../03_进阶/05_v1到v2迁移对照.md`。

---

## 二、环境准备

```powershell
# 在 E:\PyTest 下（工作区已有 .venv）
.\.venv\Scripts\python.exe -m pip install "mcp[cli]"

# 验证
.\.venv\Scripts\python.exe -c "import mcp; from mcp.server import MCPServer; print('ok')"
```

- 需要 **Python 3.10+**（本机 3.14.7 ✔）
- `[cli]` extra 提供 `mcp` 命令行工具（`mcp dev` / `mcp run` / `mcp install`）
- 验证脚本见 `01_安装与环境.md`

---

## 三、文件导航

| 文件 | 学什么 |
| --- | --- |
| `01_安装与环境.md` | 安装、验证、目录约定、CLI 工具 |
| `02_最小服务器.py` | 15 行写出一个能跑的 Server，并自测 |
| `03_工具Tool.py` | 参数 Schema、`Annotated`/`Field`、错误处理、结构化输出、注解 |
| `04_资源Resource.py` | 静态资源、URI 模板、二进制/JSON 返回 |
| `05_提示Prompt.py` | 提示词模板、多轮消息 |
| `06_上下文Context.py` | `Context` 注入、进度上报、日志、读取其他资源、elicitation |
| `07_客户端Client.py` | 内存连接 / stdio 子进程 / Streamable HTTP 三种客户端 |
| `08_测试与pytest.py` | 用 `Client(mcp)` 写单元测试 |
| `09_运行与调试.md` | `mcp dev` / `mcp run` / `mcp install`、Inspector、常见故障 |

---

## 四、每个示例文件都能独立运行

所有 `.py` 示例都遵循同一个约定：

```powershell
python "02_最小服务器.py"          # 默认：内存自测，打印结果后退出（安全）
python "02_最小服务器.py" --serve  # 真正以 stdio 启动服务器（会阻塞等待 Host 连接）
```

这样你不装任何 Host（Claude Desktop / Inspector）也能验证代码对不对。

---

## 五、SDK 的核心 API（一页记住）

```python
from mcp.server import MCPServer           # 服务器
from mcp.server.mcpserver import Context   # 处理器上下文（类型注解即注入）
from mcp import Client                     # 客户端

mcp = MCPServer("名字", instructions="给模型的系统级提示")

@mcp.tool()                                # 工具：模型可调用
def f(x: int) -> int: ...

@mcp.resource("scheme://{param}")          # 资源：可读取的数据
def r(param: str) -> str: ...

@mcp.prompt()                              # 提示词模板
def p(topic: str) -> str: ...

mcp.run()                                  # stdio（默认）/ transport="streamable-http"
```

| 协议方法 | SDK 侧（服务端） | SDK 侧（客户端） |
| --- | --- | --- |
| `tools/list` | `@mcp.tool()` 注册的东西 | `await client.list_tools()` |
| `tools/call` | 被注册的 handler | `await client.call_tool(name, args)` |
| `resources/list` | `@mcp.resource("a://b")` | `await client.list_resources()` |
| `resources/templates/list` | `@mcp.resource("a://{x}")` | `await client.list_resource_templates()` |
| `resources/read` | 模板资源 handler | `await client.read_resource(uri)` |
| `prompts/list` | `@mcp.prompt()` | `await client.list_prompts()` |
| `prompts/get` | 提示词 handler | `await client.get_prompt(name, args)` |

---

## 六、写在最后

SDK 帮你做掉了这些事（所以你的代码才这么短）：

1. 反射函数签名 → JSON Schema
2. 校验入参（pydantic）
3. JSON-RPC 报文收发、请求 id 匹配
4. initialize 握手与能力协商
5. stdio / HTTP 传输
6. 异常 → 协议错误对象
7. 把返回值包装成 `content` + `structured_content`

**你只负责业务逻辑**：一个带类型注解的函数 + 一句 docstring。
