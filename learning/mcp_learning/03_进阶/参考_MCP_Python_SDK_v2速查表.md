# MCP Python SDK v2 速查表（官方文档抓取日期：2026-09-10）

来源：https://py.sdk.modelcontextprotocol.io/ + https://pypi.org/pypi/mcp/json
规则：只写文档中确证的内容；不确定处标注 UNVERIFIED。代码块为文档原文。

---

## 0. 版本与事实核对（PyPI JSON API）

- `info.version` = **2.2.0**（`release_url` = https://pypi.org/project/mcp/2.2.0/）
- `info.requires_python` = **`>=3.10`**
- 2.2.0 wheel 上传时间：**2026-09-07T16:06:19Z**（`mcp-2.2.0-py3-none-any.whl`）；sdist `2026-09-07T14:34:15Z`
- 2.x 全部版本：`2.0.0a1`(2026-06-11)、`2.0.0a2`、`2.0.0a3`、`2.0.0b1`、`2.0.0b2`、`2.0.0rc1`(2026-07-27)、`2.0.0`(2026-07-28)、`2.1.0`(2026-08-24)、`2.1.1`(2026-08-25)、`2.0.1`(2026-08-26)、**`2.2.0`(2026-09-07)**
- **1.x 仍然可用**：1.x 在 `v1.x` 分支继续接收关键 bug/安全修复，文档在 https://py.sdk.modelcontextprotocol.io/v1/ 。1.x 最新为 `1.30.0`（2026-09-07T14:34:14Z），另有 `1.29.1`（2026-08-24）。
- v2 关键依赖（来自 wheel metadata）：`mcp-types==2.2.0`、`httpx2>=2.5.0`、`pydantic>=2.12.0`、`anyio>=4.9/4.10`、`starlette`、`uvicorn`、`jsonschema>=4.20.0`、`pyjwt[crypto]`、`opentelemetry-api>=1.28.0`、`sse-starlette>=3.0.0`、`typing-inspection`、`python-multipart`、`pywin32>=311`(win)。

---

## 1. 安装与 Python 版本、`<2` pin 警告

文档原文（installation 页）：

```
uv add "mcp[cli]"
pip install "mcp[cli]"
```

- **Python 3.10+**（原文："It requires **Python 3.10+**"）。
- `mcp[cli]` 额外带来 `typer` + `python-dotenv`，即 `mcp` 命令行（`mcp dev` / `mcp run` / `mcp install`）。`mcp[rich]` 带来更漂亮的日志（rich）。
- 一次性运行无需项目：`uv run --with "mcp[cli]" mcp ...`
- **`<2` pin 警告（原文）**：`pip install mcp` 现在装的是 2.x。若你的**包**依赖 `mcp` 且尚未迁移，请加上上界，例如 `mcp>=1.28,<2`，以免未固定的解析跑到 1.x 之外……原文："Since `pip install mcp` now installs 2.x, keep a `<2` upper bound on your requirement (for example `mcp>=1.28,<2`) until you've migrated."

---

## 2. 导入路径 / 类名（v2 真实 API）

| 用途 | v2 正确写法 | 备注 |
|---|---|---|
| 高层服务器 | `from mcp.server import MCPServer` | 原 `from mcp.server.fastmcp import FastMCP` 已**不存在**（非 deprecated，是删除） |
| 低层服务器 | `from mcp.server import Server, ServerRequestContext` | v2 重建，非改名 |
| 客户端 | `from mcp import Client` | ✅ 正确 |
| stdio 参数 | `from mcp import Client, StdioServerParameters` | |
| Context | `from mcp.server.mcpserver import Context` | 也见 `mcp.server.mcpserver.context` |
| 提示消息类 | `from mcp.server.mcpserver import Message, UserMessage, AssistantMessage`（另有 import 自 `mcp.server.mcpserver.prompts.base` 的写法） | 文档两种写法都出现 |
| 异常 | `from mcp import MCPError`；`from mcp.server.mcpserver.exceptions import ToolError, ResourceError, ResourceNotFoundError` | |
| 协议类型 | `import mcp.types as types` / `from mcp.types import Tool` | `mcp.types` 是 `mcp_types` 包的**永久别名**（同一对象） |
| 错误码常量 | `from mcp.types import INVALID_PARAMS, INVALID_REQUEST, INTERNAL_ERROR, METHOD_NOT_FOUND, MISSING_REQUIRED_CLIENT_CAPABILITY` | |
| 图片/音频工具 | `from mcp.server.mcpserver import Image, Audio`（`Audio` 同页出现） | |
| 依赖注入 | `from mcp.server.mcpserver import Resolve, Elicit, Sample, ListRoots, ElicitationResult` | |
| 路径安全 | `from mcp.shared.path_security import safe_join, contains_path_traversal, is_absolute_path` | |
| URI 模板 | `from mcp.shared.uri_template import UriTemplate, InvalidUriTemplate` | |
| 协议版本常量 | `from mcp.types.version import LATEST_PROTOCOL_VERSION, ...` | `mcp.shared.version` 已**删除** |

**关键事实**
- `FastMCP` 在 v2 **没有别名**。`mcp.server.fastmcp.*` 全部迁到 `mcp.server.mcpserver.*`。
- `from mcp import MCPServer` **不存在**。文档原文 Tip："The two halves of the SDK have two import paths: `from mcp import Client` and `from mcp.server import MCPServer`. There is no `from mcp import MCPServer`."
- `mcp.server.__init__` 的 `__all__`（源码核实）= `["CacheHint", "Server", "ServerRequestContext", "MCPServer", "NotificationOptions", "InitializationOptions"]`。
- `mcp.__all__`（源码核实）包含 `Client`、`ClientSession`、`ClientSessionGroup`、`StdioServerParameters`、`stdio_client`、`stdio_server`、`MCPError`、`MCPDeprecationWarning`、`UrlElicitationRequiredError`、`UriTemplate`、`InvalidUriTemplate`、`InputRequiredRoundsExceededError`、`ServerSession` 等；**不含** `MCPServer`。
- 构造服务器：`mcp = MCPServer("Demo")`。

### MCPServer 构造函数（源码逐字，`src/mcp/server/mcpserver/server.py`）

```python
def __init__(
    self,
    name: str | None = None,
    title: str | None = None,
    description: str | None = None,
    instructions: str | None = None,
    website_url: str | None = None,
    icons: list[Icon] | None = None,
    version: str = "",
    auth_server_provider: OAuthAuthorizationServerProvider[Any, Any, Any] | None = None,
    token_verifier: TokenVerifier | None = None,
    *,
    tools: list[Tool] | None = None,
    resources: list[Resource] | None = None,
    extensions: Sequence[Extension] | None = None,
    debug: bool = False,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    warn_on_duplicate_resources: bool = True,
    warn_on_duplicate_tools: bool = True,
    warn_on_duplicate_prompts: bool = True,
    dependencies: list[str] | None = None,
    lifespan: Callable[[MCPServer[LifespanResultT]], AbstractAsyncContextManager[LifespanResultT]] | None = None,
    auth: AuthSettings | None = None,
    resource_security: ResourceSecurity = DEFAULT_RESOURCE_SECURITY,
    request_state_security: RequestStateSecurity | None = None,
    cache_hints: Mapping[CacheableMethod, CacheHint] | None = None,
    subscriptions: SubscriptionBus | None = None,
    middleware: Sequence[ServerMiddleware[Any]] | None = None,
):
```

- 默认服务器名从 `FastMCP` 改为 **`"mcp-server"`**（`name or "mcp-server"`）。
- 未指定 version 时报告**空字符串**。
- **transport 参数不在构造器**：`MCPServer("x", port=9000)` → `TypeError: MCPServer.__init__() got an unexpected keyword argument 'port'`。`mount_path=` 已删除。
- `log_level=` 会立刻调用 `logging.basicConfig()`（配置 root logger）；`debug=` 传给 Starlette。
- `token_verifier=` 与 `auth=` 必须成对出现，否则构造时 `ValueError`。
- MCP_* 环境变量与 `.env` 不再被读取（由 CLI/宿主负责）。

---

## 3. 注册装饰器（逐字签名）

### `@mcp.tool(...)`

```python
def tool(
    self,
    name: str | None = None,
    title: str | None = None,
    description: str | None = None,
    annotations: ToolAnnotations | None = None,
    icons: list[Icon] | None = None,
    meta: dict[str, Any] | None = None,
    structured_output: bool | None = None,
) -> Callable[[_CallableT], _CallableT]:
```

- 名称/描述/输入 schema 来自函数名、docstring、类型注解。
- `structured_output`: `None`=按返回注解自动检测；`True`=强制结构化（否则 import 期报错）；`False`=纯文本（`structured_content` 为 `None`）。
- 运行期注册：`mcp.add_tool(fn, name=..., title=..., description=..., annotations=..., icons=..., meta=..., structured_output=...)`；`mcp.remove_tool(name)`（不存在时抛 `ToolError`）。
- 文档提示：`name=`、`description=`、`title=`、`annotations=` 均可覆盖推断值。

```python
from mcp.server import MCPServer
from mcp.types import ToolAnnotations

mcp = MCPServer("Bookshop")

@mcp.tool(
    title="Search the catalog",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def search_books(query: str) -> str:
    """Search the catalog by title or author."""
    return f"Found 3 books matching {query!r}."
```

约束/富 schema（文档原文）：

```python
@mcp.tool()
def search_books(
    query: Annotated[str, Field(description="Title or author to search for.")],
    limit: Annotated[int, Field(ge=1, le=50, description="Maximum number of results.")] = 10,
    genre: Literal["fiction", "non-fiction", "poetry"] | None = None,
) -> str:
    ...
```

### `@mcp.resource(...)`

```python
def resource(
    self,
    uri: str,
    *,
    name: str | None = None,
    title: str | None = None,
    description: str | None = None,
    mime_type: str | None = None,
    icons: list[Icon] | None = None,
    annotations: Annotations | None = None,
    meta: dict[str, Any] | None = None,
    security: ResourceSecurity | None = None,
) -> Callable[[_CallableT], _CallableT]:
```

- URI 里带 `{param}` → 注册为 **template**（出现在 `resources/templates/list`）；无变量 → **static resource**（出现在 `resources/list`）。
- 静态 resource **不允许**函数参数，也**不允许** `Context` 参数（源码里显式 `ValueError`）。
- placeholder 名必须与函数参数名一致，否则 **import 期** `ValueError: Mismatch between URI parameters {...} and function parameters {...}`。
- 绑定到 `{?...}`/`{&...}` query 变量的参数**必须有 Python 默认值**，否则装饰时 `ValueError`。
- 返回值：`str`→文本；`bytes`→base64 `BlobResourceContents`；其他→JSON 文本。默认 `mime_type="text/plain"`。
- 现成 Resource 类：`mcp.server.mcpserver.resources` 的 `TextResource`、`BinaryResource`、`FileResource`、`HttpResource`、`DirectoryResource`，用 `mcp.add_resource(...)` 注册。
- `ResourceSecurity` 字段（默认值）：`reject_path_traversal=True`、`reject_absolute_paths=True`、`reject_null_bytes=True`、`exempt_params`（空集）。

### `@mcp.prompt(...)`

```python
def prompt(
    self,
    name: str | None = None,
    title: str | None = None,
    description: str | None = None,
    icons: list[Icon] | None = None,
) -> Callable[[_CallableT], _CallableT]:
```

- 返回 `str` → 一条 user 消息；返回 `list[Message]`（`UserMessage`/`AssistantMessage`）→ 多轮。
- prompt 参数是**扁平的命名字符串列表**，没有 JSON Schema；缺必填参数会让整个请求失败（JSON-RPC 错误，文档写作 `-32603`，日志里有 `Missing required arguments: {...}`）。
- 运行期：`mcp.add_prompt(Prompt.from_function(fn, name=..., description=...))`、`mcp.remove_prompt(name)`。
- `add_prompt` 对同名条目是"保留已有"而非覆盖，示例先 `remove_prompt` 再 `add_prompt`。

### `@mcp.completion()`

存在（客户端示例用到）。签名 **UNVERIFIED**（API 页面只列出 `def completion(self):`）。文档示例：

```python
@mcp.completion()
async def complete_genre(
    ref: PromptReference | ResourceTemplateReference,
    argument: CompletionArgument,
    context: CompletionContext | None,
) -> Completion | None:
    return Completion(values=[genre for genre in GENRES if genre.startswith(argument.value)])
```

### Context 注入

- 参数**类型注解**为 `Context` 即注入；**参数名任意**（`ctx`/`context`/`c` 均可）。
- `ctx` 永远不会出现在 input schema 里（模型看不到）。
- 工具里可写 `ctx: Context[AppContext]` 以获得 `lifespan_context` 的类型；**resource / prompt 里只能写裸 `Context`**，否则每次调用失败，日志：`Context is not available outside of a request`。
- `ctx.fastmcp` → **`ctx.mcp_server`**；`get_context()` **已删除**（改为声明 `ctx: Context` 参数）。
- 注入只发生在被注册的那个函数上；helper 函数不会自动获得 `Context`，需普通传参。

### `Context` 上的 API（API reference 逐字摘录）

```python
async def report_progress(self, progress: float, total: float | None = None, message: str | None = None) -> None:
```

属性/方法清单（API reference 目录）：`mcp_server`、`request_context`、`report_progress`、`notify_tools_changed`、`notify_prompts_changed`、`notify_resources_changed`、`notify_resource_updated`、`read_resource`、`elicit`、`elicit_url`、`log`、`headers`、`request_id`、`protocol_version`、`input_responses`、`request_state`、`client_capabilities`、`session`、`close_sse_stream`、`close_standalone_sse_stream`、`debug`、`info`、`warning`、`error`。

使用方式（docs 原文 + API 原文）：

```python
await ctx.report_progress(50, 100)
[contents] = await ctx.read_resource("catalog://genres")
contents.content    # 'fiction, non-fiction, poetry'
contents.mime_type  # 'text/plain'
ctx.request_id
ctx.request_context.lifespan_context
ctx.headers         # 或 None（stdio）
await ctx.session.send_tool_list_changed()
await ctx.session.send_resource_list_changed()
await ctx.session.send_prompt_list_changed()
await ctx.session.send_resource_updated(uri)
await ctx.notify_tools_changed()      # 2026-07-28 subscriptions/listen 客户端
await ctx.notify_prompts_changed()
await ctx.notify_resources_changed()
await ctx.notify_resource_updated(uri)
```

- `ctx.read_resource(uri)` 返回可迭代的 `ReadResourceContents`（每个内容块一个）：`.content`、`.mime_type`（还有 `.meta`）。
- `ctx.request_context.lifespan_context` 总是存在；没有 `lifespan=` 时是空 `dict`，**不是 `None`**。
- **`ctx.info()` / `ctx.debug()` / `ctx.warning()` / `ctx.error()` / `ctx.log()` 已被 2026-07-28 规范废弃（SEP-2577）**，调用会发 `MCPDeprecationWarning`（`UserWarning` 子类，默认打印）。⚠️ 文档自身不一致：mcpserver `Context` 的 API 页面 docstring 仍展示 `await ctx.info(...)`，而 `handlers/logging` 与 `deprecated` 页面明确说该能力已废弃且不推荐使用。以 `logging` 模块为准。MIGRATION 也记录：`Context` 日志的 `message` 参数改名为 `data`，`extra` 被移除。

---

## 4. 完整 server.py 示例（v2 合法，可直接运行）

综合 docs 中 `MCPServer` + lifespan + Context + tool/resource/prompt 的写法，未引入任何未文档化的 API：

```python
"""server.py — MCP Python SDK v2 (mcp>=2.2.0, Python 3.10+)."""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, Field
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError, ResourceNotFoundError

logger = logging.getLogger(__name__)


class Database:
    def __init__(self) -> None:
        self.connected = False

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    def count_books(self, genre: str) -> int:
        return 3


@dataclass
class AppContext:
    db: Database


@asynccontextmanager
async def app_lifespan(server: MCPServer) -> AsyncIterator[AppContext]:
    db = Database()
    await db.connect()
    try:
        yield AppContext(db=db)
    finally:
        await db.disconnect()


mcp = MCPServer(
    "Bookshop",
    title="Bookshop",
    description="A tiny catalog server.",
    instructions="Search the catalog before recommending a book.",
    lifespan=app_lifespan,
    log_level="INFO",
)

CATALOG = {"Dune": "Frank Herbert", "Neuromancer": "William Gibson"}


class Book(BaseModel):
    title: str
    author: str
    year: int = Field(ge=1450, description="Year of first publication.")


@mcp.tool(title="Search the catalog")
def search_books(
    query: Annotated[str, Field(description="Title or author to search for.")],
    limit: Annotated[int, Field(ge=1, le=50, description="Maximum number of results.")] = 10,
) -> str:
    """Search the catalog by title or author."""
    logger.info("searching for %r", query)
    return f"Found 3 books matching {query!r} (showing up to {limit})."


@mcp.tool()
def lookup_book(title: str) -> Book:
    """Look up a book by its exact title."""
    if title not in CATALOG:
        raise ToolError(f"No book titled {title!r} in the catalog.")
    return Book(title=title, author=CATALOG[title], year=1965)


@mcp.tool()
async def count_books(genre: str, ctx: Context[AppContext]) -> str:
    """Count the books in a genre (uses the lifespan database)."""
    await ctx.report_progress(1, total=1, message="counting")
    db = ctx.request_context.lifespan_context.db
    return f"[request {ctx.request_id}] {db.count_books(genre)} books in {genre!r}."


@mcp.resource("config://app", mime_type="text/plain")
def get_config() -> str:
    """The active shop configuration."""
    return "theme=dark\nlanguage=en"


@mcp.resource("books://{title}")
def book_entry(title: str) -> str:
    """The catalog entry for one book."""
    if title not in CATALOG:
        raise ResourceNotFoundError(f"No book titled {title!r} in the catalog.")
    return f"{title} by {CATALOG[title]}"


@mcp.prompt(title="Recommend a book")
def recommend(
    genre: Annotated[str, Field(description="The genre to recommend in.")],
) -> str:
    """Ask for a recommendation in a genre."""
    return f"Recommend one {genre} book from the catalog and say why."


if __name__ == "__main__":
    mcp.run()   # 默认 stdio；HTTP: mcp.run(transport="streamable-http", port=3001)
```

要点：`run()` 放在 `if __name__ == "__main__":` 内（所有加载方式都会 import 这个文件）。

---

## 5. 客户端完整示例

### 5.1 内存 `Client(mcp)`（测试/嵌入）

```python
import anyio
from mcp import Client
from server import mcp

async def main() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool("search_books", {"query": "dune", "limit": 5})
        print(result.content)
        print(result.structured_content)

anyio.run(main)
```

### 5.2 stdio 子进程

```python
from mcp import Client, StdioServerParameters

server = StdioServerParameters(
    command="uv",
    args=["run", "server.py"],
    env={"BOOKSHOP_API_KEY": "secret"},
)

async def main() -> None:
    async with Client(server) as client:
        result = await client.list_tools()
        print([tool.name for tool in result.tools])
```

- 进入 `async with` 才 spawn；离开时收尾（关 stdin→等待→必要 kill）。
- 子进程**不继承**你的环境（POSIX 白名单：`HOME`、`LOGNAME`、`PATH`、`SHELL`、`TERM`、`USER`）；`env=` 的值叠加在白名单上。
- 想重定向子进程 stderr：`from mcp import stdio_client`，然后 `Client(stdio_client(server, errlog=log_file))`。

### 5.3 Streamable HTTP

```python
import anyio
from mcp import Client

async def main() -> None:
    async with Client("http://localhost:8000/mcp") as client:
        print(client.server_info)
        print(client.server_capabilities)
        print(client.protocol_version)
        print(client.instructions)

anyio.run(main)
```

自带 `httpx2.AsyncClient`（自定义 header / 超时 / mTLS）：

```python
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

async def main() -> None:
    async with httpx2.AsyncClient(
        headers={"Authorization": "Bearer ..."},
        timeout=httpx2.Timeout(30.0, read=300.0),
    ) as http_client:
        transport = streamable_http_client("http://localhost:8000/mcp", http_client=http_client)
        async with Client(transport) as client:
            result = await client.list_tools()
            print([tool.name for tool in result.tools])
```

- `streamable_http_client` 的参数**只有** `url`、`http_client`、`terminate_on_close`。传入 `headers=` 会 `TypeError`。
- 旧名 `streamablehttp_client` 已删除；`get_session_id` 回调已删除（现在只 yield 两个流）。
- 重定向策略：同 scheme/host/port 的 307/308 及同 host `http→https` 会被跟随；其他一律失败 `MCPError: Redirect to ... not followed; use that URL as the endpoint if it is the intended server`。
- SSE（被取代）：`from mcp.client.sse import sse_client` → `Client(sse_client("http://localhost:8000/sse"))`。

### 5.4 `Client` 构造参数（API reference 目录逐字）

字段：`server`、`raise_exceptions`、`read_timeout_seconds`、`sampling_callback`、`sampling_capabilities`、`list_roots_callback`、`logging_callback`、`log_level`、`message_handler`、`client_info`、`mode`、`prior_discover`、`elicitation_callback`、`input_required_max_rounds`、`extensions`、`cache`。

```python
ConnectMode = Literal['legacy', 'auto'] | str
```

- `Client(...)` 是 `@dataclass`；**构造不等于连接**，未进入 `async with` 就使用会报 `RuntimeError: Client must be used within an async context manager`。
- `mode` 默认 `"auto"`：先探 `server/discover`，失败回退 `initialize` 握手；`mode="legacy"` 强制握手（可用 server→client 推送：sampling / push elicitation / `message_handler`）；`mode="2026-07-28"` 直接采用（零协商，但 `server_info` 为 `None`）；配合 `prior_discover=client.session.discover_result` 可零往返拿回身份。
- `raise_exceptions=True` 只对**进程内**连接有效（把 server 端被消毒的 `"Internal server error"` 换成真实异常）。不影响 tool 内异常（那永远是 `is_error=True` 结果）。
- 连接后只读属性：`client.server_info`（可能是 `None`）、`client.server_capabilities`、`client.protocol_version`、`client.instructions`；低层逃生口 `client.session`。

### 5.5 方法名与返回对象

```python
result = await client.list_tools()          # ListToolsResult → result.tools[i].name/.title/.description/.input_schema
result = await client.call_tool("add", {"a": 1, "b": 2})
result.content                              # list[ContentBlock]：TextContent / ImageContent / AudioContent / ResourceLink / EmbeddedResource
result.structured_content                   # dict | None，符合 output_schema
result.is_error                             # bool（ToolError 或未知工具 → True，调用本身不抛）
result = await client.list_resources()      # .resources[i].uri
result = await client.list_resource_templates()  # .resource_templates[i].uri_template
result = await client.read_resource("catalog://genres/poetry")
result.contents                             # list[TextResourceContents | BlobResourceContents] → .text / .blob
result = await client.list_prompts()        # .prompts[i].name/.title/.arguments
result = await client.get_prompt("recommend", {"genre": "poetry"})
result.messages                             # list[PromptMessage] → .role, .content
result = await client.complete(ref=PromptReference(type="ref/prompt", name="recommend"),
                               argument={"name": "genre", "value": "p"})
result.completion.values
```

- **progress**：`await client.call_tool(name, args, progress_callback=show)`，回调签名 `async (progress: float, total: float | None, message: str | None) -> None`。是**每次调用**的参数，不是 `Client` 的构造参数。
- **分页**：每个 `list_*` 接受 `cursor=`，结果有 `next_cursor`（`None` 即结束）。
- 工具内部 `raise ToolError` → 调用**正常返回** `is_error=True`，消息在 `content` 里（供模型读取）。未知工具同样 `is_error=True` + `Unknown tool: ...`。只有 JSON-RPC error 才让 `Client` 抛 `MCPError`。
- 订阅：`client.subscribe_resource(uri)` / `unsubscribe_resource(uri)` 在 2026-07-28 线上返回 `-32601`；替代是 `async with client.listen(...)`。`client.send_ping()` 已废弃（现代连接服务端答 Method not found）。

---

## 6. 运行 / 开发 / 调试

### `mcp.run()`（同步、阻塞）

```python
if __name__ == "__main__":
    mcp.run()                                        # 默认 stdio
    # mcp.run(transport="streamable-http", port=3001)
    # mcp.run(transport="sse")                       # 已被取代，仅为兼容
```

- `--transport` 取值（`run(transport=...)`）：**`"stdio"`（默认）、`"streamable-http"`、`"sse"`**。
- `streamable-http` 关键参数：`host`（默认 `127.0.0.1`）、`port`（默认 `8000`）、**`streamable_http_path`（默认 `"/mcp"`）**、`json_response=False`、`stateless_http=False`、`max_request_body_size`（默认 4 MiB，超出 HTTP 413）、`session_idle_timeout`（默认 1800 秒）、`max_sessions`（默认 10 000）、`event_store`、`retry_interval`、`transport_security`。
- `sse` 关键参数：`host`、`port`、`sse_path`（默认 `/sse`）、`message_path`（默认 `/messages/`）、`max_request_body_size`、`transport_security`。
- 客户端连 `http://127.0.0.1:3001/mcp`（path = `streamable_http_path`）。

### CLI 子命令

```
uv run mcp dev server.py
uv run mcp dev server.py --with pandas --with numpy
uv run mcp dev server.py --with-editable .
uv run mcp run server.py
uv run mcp run server.py:bookshop                # 对象名不是 mcp/server/app 时
uv run mcp run server.py --transport streamable-http
uv run mcp install server.py --name "Bookshop"
uv run mcp install server.py -v API_KEY=abc123 -f .env
uv run mcp version
```

- `mcp dev` = 在 **MCP Inspector** 下运行（需要 `PATH` 上有 `npx`，Inspector 是 Node 应用）。`--with` 往环境里加包，`--with-editable` 安装你自己的包。
- `mcp run` 会 import 文件、找到模块级服务器对象（`mcp`、`server` 或 `app`）并调用其 `run()`；文件里的 `if __name__ == "__main__":` **不会执行**；唯一转发给 `run()` 的选项是 `--transport`。
- `mcp install` 只认 **Claude Desktop**（`-v KEY=VALUE`、`-f .env` 写入 env）。
- `mcp dev` / `mcp run` **只识别 `MCPServer`**；低层 `Server` 需自行运行。
- v2 中 `mcp dev` / `mcp install` 会把生成的 `uv run --with mcp==<你的版本>` 固定到已安装版本。

### MCP Inspector

`uv run mcp dev server.py` → 打开它打印的 URL；Tabs：Tools / Resources / Resource Templates / Prompts。它通过 **stdio** 启动你的 server（与真实宿主完全一致）。

---

## 7. pytest 测试模式（文档逐字）

```python
import pytest
from inline_snapshot import snapshot
from mcp import Client
from mcp.types import CallToolResult, TextContent

from server import mcp


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with Client(mcp, raise_exceptions=True) as c:
        yield c


@pytest.mark.anyio
async def test_call_add_tool(client: Client):
    result = await client.call_tool("add", {"a": 1, "b": 2})
    # Drop the server identity stamp in `_meta`; it is not what this test is about.
    result.meta = None
    assert result == snapshot(
        CallToolResult(
            content=[TextContent(type="text", text="3")],
            structured_content={"result": 3},
        )
    )
```

- 开发依赖：`uv add --dev pytest inline-snapshot` / `pip install pytest inline-snapshot`。
- `anyio_backend` 返回 `"asyncio"`（或 `"trio"`）。`pytest.mark.anyio` 由 anyio 的 pytest 插件提供。
- `Client(mcp)` 是 **era-neutral**：默认协商 2026-07-28。若测试的是 legacy 语义（sampling / push elicitation / `message_handler`），用 `mode="legacy"`，并**去掉** `raise_exceptions=True`（legacy 连接本来不消毒；该 flag 会把失败抛到 server task 里而不是测试里）。
- 替代 v1 的 `create_connected_server_and_client_session()`（**已删除**）。
- 想复盘工具异常：在结果上断言；traceback 在 server 日志里，pytest 的 `caplog` 能拿到。

---

## 8. 授权（OAuth）与 ASGI 挂载

### 服务器 = OAuth 2.1 resource server（只验证、不签发）

```python
from pydantic import AnyHttpUrl
from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings

RESOURCE = "http://127.0.0.1:8000/mcp"
KNOWN_TOKENS = {
    "alice-token": AccessToken(token="alice-token", client_id="alice", scopes=["notes:read"], resource=RESOURCE),
}

class StaticTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        return KNOWN_TOKENS.get(token)

mcp = MCPServer(
    "Notes",
    token_verifier=StaticTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("https://auth.example.com"),
        resource_server_url=AnyHttpUrl(RESOURCE),
        required_scopes=["notes:read"],
        validate_token_resource=True,
    ),
)
```

- `TokenVerifier` 只有一个 async 方法：`verify_token(token: str) -> AccessToken | None`。`AccessToken` 有 `token`、`client_id`、`scopes`、`resource`（还有 `subject`、`expires_at`、`claims`）。
- `AuthSettings`：`issuer_url`、`resource_server_url`、`required_scopes`、`validate_token_resource`（不设时发 `MCPDeprecationWarning` 且行为等同 `False`；3.0 起在有 `resource_server_url` 时默认 `True`）。
- 应用路由：`/mcp` 与 `/.well-known/oauth-protected-resource/mcp`（RFC 9728）。未认证请求得到 401 + `WWW-Authenticate: Bearer ... resource_metadata="..."`。
- 处理器内取身份：`from mcp.server.auth.middleware.auth_context import get_access_token` → 返回 `AccessToken | None`（stdio / 内存连接永远是 `None`）。
- **stdio 与内存 `Client(mcp)` 不过鉴权层。**
- 另有过时参数 `auth_server_provider=`（内嵌完整 AS），新服务器不建议用。
- 客户端侧：`OAuthClientProvider` / `ClientCredentialsOAuthProvider` / `PrivateKeyJWTOAuthProvider` / `IdentityAssertionOAuthProvider` 现在都继承 `httpx2.Auth`，用 `httpx2.AsyncClient(auth=provider)`；`RFC7523OAuthClientProvider` 与 `JWTParameters` 已删除；`scopes=` 改名 `scope=`；`callback_handler` 现在返回 `AuthorizationCodeResult`；`OAuthClientProvider` 的 `timeout` 参数被移除。

### ASGI 挂载（**精确属性名**）

- **没有 `mcp.http_app()`**。正确名字是 **`MCPServer.streamable_http_app()`**（SSE 版是 `mcp.sse_app()`）。

```python
from mcp.server import MCPServer

mcp = MCPServer("Notes")

@mcp.tool()
def add_note(text: str) -> str:
    """Save a note."""
    return f"Saved: {text}"

app = mcp.streamable_http_app()   # Starlette 应用，路由 /mcp
```

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.server import MCPServer

mcp = MCPServer("Notes")

@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    async with mcp.session_manager.run():
        yield

app = Starlette(
    routes=[Mount("/", app=mcp.streamable_http_app())],
    lifespan=lifespan,
)
```

- **挂载会让子应用的 lifespan 失效**：宿主 app 必须自己 `async with mcp.session_manager.run()`，否则首个请求报 `RuntimeError: Task group is not initialized. Make sure to use run().`
- `mcp.session_manager` **只在调用过 `streamable_http_app()` 之后**才存在。
- `streamable_http_app()` 参数与 `run("streamable-http", ...)` 相同（去掉 `port`）：`streamable_http_path="/mcp"`、`json_response`、`stateless_http`、`event_store`、`retry_interval`、`max_request_body_size`、`session_idle_timeout`、`max_sessions`、`transport_security`、`host`。
- 默认只接受 localhost（DNS-rebinding 防护）；部署到真实域名必须传 `transport_security=TransportSecuritySettings(allowed_hosts=[...], allowed_origins=[...])`，否则全部 `421 Misdirected Request`。
- CORS：`allow_headers` 需含 `Authorization`、`Content-Type`、`Last-Event-ID`、`Mcp-Method`、`Mcp-Name`、`Mcp-Protocol-Version`、`Mcp-Session-Id`；`expose_headers=["Mcp-Session-Id"]`。
- 自定义路由：`@mcp.custom_route("/health", methods=["GET"])`（**永不鉴权**）。

---

## 9. v1 → v2 破坏性变更（Top 15+）

1. **`FastMCP` → `MCPServer`**，模块 `mcp.server.fastmcp.*` → `mcp.server.mcpserver.*`；旧路径**删除**（早期症状 `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`）。
2. **字段 camelCase → snake_case**：`isError`→`is_error`、`inputSchema`→`input_schema`、`outputSchema`→`output_schema`、`nextCursor`→`next_cursor`、`mimeType`→`mime_type`、`structuredContent`→`structured_content`、`serverInfo`→`server_info`、`protocolVersion`→`protocol_version`、`uriTemplate`→`uri_template`、`listChanged`→`list_changed`、`progressToken`→`progress_token`。线缆 JSON 仍是 camelCase；自己 `model_dump()` 要加 `by_alias=True`。
3. **`McpError` → `MCPError`**，构造器直接 `(code, message, data)`；`from mcp import MCPError`。`MCPError` 在 tool 里被抛出会变成 **JSON-RPC error**（模型看不到），`ToolError` 才是 `is_error=True` 结果。
4. **`mcp.types` 迁到独立包 `mcp-types`**；`mcp.types` 是永久别名（同一对象）。`mcp.shared.version` 删除 → 用 `mcp.types.version`。
5. **协议版本常量语义变更**：`LATEST_PROTOCOL_VERSION` 从 `"2025-11-25"` 变为 **`"2026-07-28"`**（initialize 握手无法协商它）；`SUPPORTED_PROTOCOL_VERSIONS` 废弃；新增 `HANDSHAKE_PROTOCOL_VERSIONS`、`MODERN_PROTOCOL_VERSIONS`、`KNOWN_PROTOCOL_VERSIONS`、`LATEST_HANDSHAKE_VERSION`、`LATEST_MODERN_VERSION`、`OLDEST_SUPPORTED_VERSION`、`is_version_at_least()`。
6. **transport 参数搬离构造器**：`host`/`port`/`stateless_http`/`json_response`/路径/`transport_security` 都到 `run()` 与 `*_app()`；`mount_path=` 删除；`MCPServer("x", port=9000)` 抛 `TypeError`。
7. **低层 `Server` 重建**：装饰器 `@server.list_tools()` 等 → 构造参数 `on_list_tools=`、`on_call_tool=` …；handler 形状统一为 `async (ctx: ServerRequestContext, params) -> Result`；`server.request_context` 与 `request_ctx` ContextVar 删除；`request_handlers`/`notification_handlers` 字典删除（改用 `add_request_handler` / `get_request_handler(method)`）；`_handle_*` 删除（改用 `middleware`）。
8. **低层自动包装移除**：不再自动包 list/dict/`Iterable[ReadResourceContents]`；参数 schema **不再校验**；tool handler 的普通异常不再变成 `CallToolResult(is_error=True)`，而是 JSON-RPC error。
9. **`mcp.types` 移除的别名**：`Content`→`ContentBlock`、`ResourceReference`→`ResourceTemplateReference`、`Cursor`→`str`、`ClientRequestType`→`ClientRequest` 等；`TaskExecutionMode`/`TASK_*` 删除。
10. **`RootModel` 联合类型改为普通 union + `TypeAdapter`**：`ClientRequest`/`ServerRequest`/`ClientNotification`/`ServerNotification`/`ClientResult`/`ServerResult`/`JSONRPCMessage` 不再有 `.root`。
11. **resource URI 由 `AnyUrl` 变 `str`**（`Resource.uri`、`ReadResourceRequestParams.uri`、`ResourceContents.uri` 等），`read_resource()` 只收 `str`；不再规范化 URI。
12. **额外字段不再保留**（`extra="allow"` → 忽略）；自定义数据请放 `_meta`。
13. **`create_connected_server_and_client_session` 删除** → 用 `Client(mcp)`。
14. **同步 handler 在线程池执行**（`def` 工具不再阻塞事件循环，但也不在事件循环线程上）；`Context` 泛型参数从 3 个减到 2 个（`Context[LifespanContextT, RequestT]`）；`RequestContext` 拆成 `ClientRequestContext` / `ServerRequestContext`；`ctx.fastmcp` → `ctx.mcp_server`；`get_context()` 删除；`ProgressContext`/`progress()` 上下文管理器删除；`Context.client_id` 删除。
15. **roots / sampling / 协议级 logging 被 2026-07-28（SEP-2577）废弃**；`ping` 被**移除**；客户端→服务器 progress 废弃；`subscriptions/listen` 取代独立 GET 流与 `resources/subscribe`。`MCPDeprecationWarning`（`UserWarning` 子类，默认可见）。
16. **`httpx` + `httpx-sse` → `httpx2`**（TLS 走系统信任库 `truststore`；logger 名变 `httpx2` / `httpcore2.*`；异常类型变 `httpx2.ConnectError` 等）。
17. **WebSocket transport 与 `mcp[ws]` 删除**；实验性 Tasks API（`mcp.*.experimental`）删除；`streamablehttp_client` 删除；`get_session_id` 回调删除。
18. **客户端默认 `mode='auto'`**（会先发 `server/discover`）；客户端会按协商版本校验入站报文（不合规服务器会抛 `pydantic.ValidationError`）；`cursor` 从 `ClientSession` 列表方法移除；超时改为 float 秒；超时错误码 `-32001`（`REQUEST_TIMEOUT`）取代 `408`。

---

## 10. 协议版本常量（API reference 逐字）

`mcp_types.version`（`mcp.types.version` 是镜像，同一对象）：

```python
KNOWN_PROTOCOL_VERSIONS: Final[tuple[str, ...]] = (
    "2024-11-05",
    "2025-03-26",
    "2025-06-18",
    "2025-11-25",
    "2026-07-28",
)

HANDSHAKE_PROTOCOL_VERSIONS: Final[tuple[str, ...]] = (
    "2024-11-05",
    "2025-03-26",
    "2025-06-18",
    "2025-11-25",
)

MODERN_PROTOCOL_VERSIONS: Final[tuple[str, ...]] = (
    "2026-07-28",
)

SUPPORTED_PROTOCOL_VERSIONS: tuple[str, ...] = (
    *HANDSHAKE_PROTOCOL_VERSIONS,
    *MODERN_PROTOCOL_VERSIONS,
)

LATEST_PROTOCOL_VERSION: Final[str] = KNOWN_PROTOCOL_VERSIONS[-1]              # "2026-07-28"
LATEST_HANDSHAKE_VERSION: Final[str] = HANDSHAKE_PROTOCOL_VERSIONS[-1]        # "2025-11-25"
LATEST_MODERN_VERSION: Final[str] = MODERN_PROTOCOL_VERSIONS[-1]              # "2026-07-28"
OLDEST_SUPPORTED_VERSION: Final[str] = HANDSHAKE_PROTOCOL_VERSIONS[0]         # "2024-11-05"
```

```python
def is_version_at_least(version: str, minimum: str) -> bool:
    """Return True if `version` is a known revision at least as new as `minimum`."""
```

- 导入：`from mcp.types.version import HANDSHAKE_PROTOCOL_VERSIONS`（v1 是 `from mcp.shared.version import LATEST_PROTOCOL_VERSION`，该模块已删除）。
- 这些 tuple 真的是 tuple（v1 的 `SUPPORTED_PROTOCOL_VERSIONS` 是 list），与 list 拼接会 `TypeError`。
- 其他 meta key 常量（`mcp_types` 顶层）：`PROTOCOL_VERSION_META_KEY`、`CLIENT_INFO_META_KEY`、`CLIENT_CAPABILITIES_META_KEY`、`SERVER_INFO_META_KEY`、`LOG_LEVEL_META_KEY`、`CORE_RESULT_TYPES`、`DEFAULT_NEGOTIATED_VERSION`。
- 其他 JSON-RPC 错误码常量：`INVALID_REQUEST`、`INVALID_PARAMS`（-32602）、`INTERNAL_ERROR`（-32603）、`METHOD_NOT_FOUND`（-32601）、`MISSING_REQUIRED_CLIENT_CAPABILITY`（-32021）。

---

## 11. UNVERIFIED / 文档冲突清单

1. `@mcp.completion()` 的完整签名未在 API 页面展开（只列出 `def completion(self):`）。示例签名见第 3 节，标为 **UNVERIFIED**。
2. `ctx.info()` / `ctx.debug()` / `ctx.warning()` / `ctx.error()` / `ctx.log()`：`handlers/logging` 与 `deprecated` 页面说该能力被 2026-07-28 废弃并给出 `MCPDeprecationWarning`；但 mcpserver `Context` API 页面 docstring 仍把它们当推荐用法展示。**文档内部冲突**，按废弃处理。
3. `Context.read_resource` 的确切返回类型注解未在 API 快照中逐字抓到；文档文本说返回 `ReadResourceContents` 的可迭代（`.content` / `.mime_type`）。类型别名逐字 **UNVERIFIED**。
4. `mcp.server.mcpserver.resources` 中 `FileResource.encoding`、各 Resource 构造签名未逐字核实。
5. 未在文档中找到 `mcp.http_app()`：判定**该属性不存在**，正确 API 是 `streamable_http_app()` / `sse_app()`。
6. `mcp dev` / `mcp run` / `mcp install` 的完整 `--help` 参数列表未抓取（只有 docs 中示例出现的选项）。
7. `mcp.types` 顶层是否 re-export `LATEST_PROTOCOL_VERSION`：迁移指南只示范 `from mcp.types.version import LATEST_PROTOCOL_VERSION`，故按子模块导入为准。
