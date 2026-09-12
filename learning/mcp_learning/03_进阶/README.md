# 03 · 进阶

> 基础篇让你"能写出能跑的服务器"，进阶篇让你"能写出不出事的服务器"。

---

## 文件导航

| 文件 | 内容 | 类型 |
| --- | --- | --- |
| `01_结构化输出与pydantic.py` | 返回类型 → `structured_content` / `outputSchema` 的**实测**对照表 | 可运行 |
| `02_lifespan与依赖注入.py` | 数据库连接、HTTP 客户端这类"重资源"怎么跨请求共享 | 可运行 |
| `03_传输与ASGI挂载.py` | stdio / Streamable HTTP / 挂进 Starlette-FastAPI | 可运行 |
| `04_认证与授权.md` | OAuth 2.1 全流程、`TokenVerifier` + `AuthSettings`、7 条安全红线 | 文档 |
| `05_v1到v2迁移对照.md` | `FastMCP` → `MCPServer`，18 条破坏性变更逐条"报错 + 修法" | 文档 |
| `06_调试与排错.md` | 五层定位法、30 行报错速查表、五种调试手段、最小复现模板 | 文档 |
| `参考_MCP_Python_SDK_v2速查表.md` | SDK v2 全量速查（签名、导入路径、版本常量） | 参考 |

---

## 三条主线

### 主线 1：数据怎么进出（01）

```
你的函数返回什么  ──►  structured_content 长什么样  ──►  outputSchema 长什么样
   int                     {"result": 3}                 {"result": "integer"}
   list[X]                 {"result": [...]}             {"result": "array"}
   BaseModel               {"字段": ...}                  模型自己的 schema
   structured_output=False None                          （不生成）
```

**一句话**：不确定用什么返回类型时，就定义一个 pydantic 模型。

### 主线 2：资源怎么活得久（02）

```
模块顶层创建   ❌ import 副作用、没有事件循环、测试难隔离
每次调用创建   ❌ 慢、连接泄漏
lifespan 创建  ✅ 启动一次、所有请求共享、关闭时清理
```

关键 API：`MCPServer(lifespan=...)` + `ctx.request_context.lifespan_context`。

### 主线 3：怎么暴露出去（03）

```
本机 Host ──── stdio ────►  mcp.run()
远程/多人 ──── HTTP ─────►  mcp.run(transport="streamable-http")
已有 Web 应用 ─ ASGI 挂载 ─►  mcp.streamable_http_app() + session_manager
```

---

## 进阶篇里最容易翻车的 5 个点

| 坑 | 症状 | 正解 |
| --- | --- | --- |
| 静态 resource 带 `Context` | 导入期 `ValueError: ... no URI template variables` | 改成模板资源，或做成工具 |
| 传输参数写进构造函数 | `TypeError: unexpected keyword argument 'port'` | 放到 `mcp.run(...)` |
| 用 `mcp.http_app()` | `AttributeError` | 正确名字是 `streamable_http_app()` / `sse_app()` |
| 挂载后第一个请求 500 | `RuntimeError: Task group is not initialized` | 宿主 lifespan 里 `async with mcp.session_manager.run():` |
| 进度回调写成同步函数 | `TypeError: 'NoneType' object can't be awaited` | `async def progress_callback(...)` |

---

## 学完进阶，你应该能回答

1. 为什么工具返回 `int` 时 `structured_content` 是 `{"result": 3}` 而不是 `3`？
2. `lifespan_context` 在没有配置 lifespan 时是什么？为什么不是 `None`？
3. 同一个 `Client` 反复连接服务器，lifespan 会跑几次？
4. 什么情况下必须给 `Client` 传 `mode="legacy"`？
5. 为什么静态资源不允许注入 `Context`？
6. v1 教程里的 `FastMCP` 在 v2 里叫什么？旧路径会报什么错？

答不上来就回去翻对应文件；答案都在里面。
