# 04 · 实战项目：个人笔记库

> 把前面所有知识串成一个**能用的** MCP 服务器。
> 三个文件，一共不到 700 行，但覆盖了 MCP 服务器该有的全部要素。

---

## 文件

| 文件 | 作用 |
| --- | --- |
| `server.py` | 服务器本体：lifespan + 6 个工具 + 2 个资源模板 + 2 个提示词 + 演示 |
| `client.py` | 一个"像 Agent 一样"的客户端：读工具清单 → 决定调用 → 读资源 → 取提示词 |
| `test_server.py` | 11 个单元测试（内存 Client 直连，不污染真实数据） |
| `notes.json` | 运行时自动生成的数据文件（可删） |

---

## 本项目演示了什么

| 知识点 | 在代码里的位置 |
| --- | --- |
| `MCPServer` 构造与 `instructions` | `mcp = MCPServer("笔记库", instructions=...)` |
| lifespan 加载/落盘 | `app_lifespan` + `NoteStore.load/save` |
| 跨请求共享资源 | `ctx.request_context.lifespan_context` |
| `Context[AppContext]` 类型化注入 | `search_notes(ctx: Context[AppContext], ...)` |
| 工具参数校验与 JSON Schema | `SearchResult` / `Annotated` / `Field(ge=..., le=...)` |
| 结构化输出 | 返回 `Note` / `SearchResult` / `list[NoteSummary]` |
| `ToolError`（给模型看） | `add_note` 空标题、`delete_note` 未确认 |
| `ResourceNotFoundError` | `NoteStore.get` |
| 工具注解 | `readOnlyHint` / `destructiveHint` / `idempotentHint` |
| 静态资源的限制 | 见下方"踩坑记录" |
| 资源模板 + Context | `notes://note/{note_id}`、`notes://tag/{tag}` |
| 提示词（单条 / 多轮） | `review_note` / `summarize_topic`（返回 `list[UserMessage]`） |
| 日志走 stderr | `logging`，绝不会 `print` 到 stdout |
| 测试隔离 | 测试里用 `MCP_NOTES_FILE` 指向临时文件 |

---

## 运行

```powershell
cd E:\PyTest\learning\mcp_learning\04_实战项目

# 1) 自测：看完整流程（会临时写入再清理笔记）
..\.venv\Scripts\python.exe server.py

# 2) 客户端演示（内存直连）
..\.venv\Scripts\python.exe client.py

# 3) 单元测试
..\.venv\Scripts\python.exe test_server.py

# 4) 作为真正的服务器跑起来
..\.venv\Scripts\python.exe server.py --serve                 # stdio
..\.venv\Scripts\python.exe server.py --http                  # http://127.0.0.1:8000/mcp
..\.venv\Scripts\python.exe client.py --http http://127.0.0.1:8000/mcp
..\.venv\Scripts\python.exe -m mcp dev server.py               # MCP Inspector（需要 Node.js）
```

接进 Claude Desktop：

```json
{
  "mcpServers": {
    "notes": {
      "command": "E:\\PyTest\\learning\\mcp_learning\\.venv\\Scripts\\python.exe",
      "args": ["E:\\PyTest\\learning\\mcp_learning\\04_实战项目\\server.py", "--serve"]
    }
  }
}
```

---

## 踩坑记录（都是实测踩出来的）

### 1. 静态资源不能用 `Context`

```python
@mcp.resource("notes://index")
def notes_index(ctx: Context) -> list[dict]:   # ❌ 导入期直接报错
    ...
```

```
ValueError: Resource 'notes://index' has no URI template variables, but the handler
declares a Context parameter. Context injection for static resources is not supported.
```

**解决**：需要 lifespan 数据的资源，要么写成**模板**（URI 里带 `{param}`），要么做成 **tool**。
本项目两个都用了：索引做成 `list_notes()` 工具，按标签查询做成 `notes://tag/{tag}` 模板。

### 2. 裸列表返回会被包一层 `result`

```python
def list_tags(...) -> list[TagCount]: ...
# structured_content == {"result": [{"tag": ..., "count": ...}, ...]}
```

而返回 pydantic 模型时**不会**包：

```python
def get_note(...) -> Note: ...
# structured_content == {"id": ..., "title": ...}
```

写客户端断言时务必注意。

### 3. `Context` 只在被注册的函数上自动注入

`_ctx_app(ctx)` 这种 helper 必须**手动把 ctx 传进去**，它自己拿不到。

---

## 可以继续做的练习

1. 把 `NoteStore` 换成 SQLite（提示：连接放进 lifespan）
2. 加一个 `summarize_note` 工具，用 `ctx.elicit` 让用户选摘要长度
   （注意：需要 stdio/HTTP + `mode="legacy"`）
3. 加一个 `notes://search/{keyword}` 资源模板
4. 给 `add_note` 加 `annotations=ToolAnnotations(idempotentHint=False)`
5. 用 `ctx.report_progress` 给"重建索引"这类长任务加进度上报
6. 把服务器挂进一个 FastAPI 应用（见 `../03_进阶/03_传输与ASGI挂载.py`）
7. 加 `auth=AuthSettings(...)` + `token_verifier=` 做 OAuth 保护
   （见 `../03_进阶/04_认证与授权.md`）
