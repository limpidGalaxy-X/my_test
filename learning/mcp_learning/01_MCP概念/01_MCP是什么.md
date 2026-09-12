# 01 · MCP 是什么

## 1. 官方定义

> Model Context Protocol (MCP) 是一个开放协议，用于让 LLM 应用（LLM applications）与外部数据源、工具之间实现无缝集成。它标准化了「把上下文提供给模型」这件事。
> —— [MCP 规范 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18)

拆开看三个关键词：

| 关键词 | 含义 |
| --- | --- |
| **开放协议** | 不是某个厂商的 SDK，是一份规范（specification）+ 多个语言的官方 SDK |
| **LLM 应用 ↔ 外部世界** | 连接的两端是「AI 应用」和「数据/工具」，不是「人 ↔ 机器」 |
| **标准化上下文** | 把"模型需要看到的资料"和"模型可以调用的动作"用统一格式描述出来 |

---

## 2. 它到底解决什么问题

### 问题一：集成组合爆炸（M × N）

假设你有 5 个 AI 应用（IDE 插件、聊天机器人、Agent 框架……）和 20 个数据源（GitHub、Postgres、本地文件、Slack……）。
没有标准时，每条连线都要单独写适配代码：`5 × 20 = 100` 份集成。

有了 MCP：每个数据源写一个 Server，每个应用实现一个 Client，`5 + 20 = 25` 份工作，

### 问题二：模型不知道你的私有上下文

模型训练数据里没有：你的代码库、你公司的数据库、你本机的文件、你昨天的会议记录。
MCP 提供了一套**结构化**的方式把这些喂给模型，而不是把一堆字符串硬塞进 prompt。

### 问题三：工具调用的描述不统一

各家模型的 function calling 格式不同（字段名、schema 方言）。
MCP 定义了统一的 `inputSchema`（JSON Schema）+ 描述 + 注解，写一次，所有 MCP Host 都能用。

---

## 3. 和「函数调用（Function Calling）」的区别

这是最容易混淆的一对概念。

| 维度 | Function Calling | MCP |
| --- | --- | --- |
| 是什么 | **模型厂商的 API 能力**：让模型输出「我要调用哪个函数、参数是什么」 | **应用之间的通信协议**：让 AI 应用发现并调用外部能力 |
| 谁定义 | OpenAI / Anthropic / Google 各自的 API 规范 | 开放规范，厂商中立 |
| 解决 | 模型 → 宿主程序的**意图表达** | 宿主程序 → 外部能力的**连接与发现** |
| 范围 | 一次模型输出里的一个字段 | 连接生命周期、能力协商、传输、认证、资源、提示词、日志、进度 |
| 关系 | —— | **MCP 工具最终会转换成模型的 function calling 描述**。两者是上下游，不是竞争关系 |

一句话：

```
用户提问 → Host 通过 MCP 拿到「工具清单」→ 转成模型的 function calling 格式
        → 模型说"调用 add(1,2)" → Host 通过 MCP 把调用发给 Server → 结果回填给模型
                       ↑ MCP 管这段                    ↑ MCP 管这段
```

### 代码上的对应关系

```python
# 你在 MCP Server 里写：                          # Host 内部转换成模型看得懂的东西：
@mcp.tool()                                       {
def add(a: int, b: int) -> int:                     "name": "add",
    """Add two numbers."""                          "description": "Add two numbers.",
    return a + b                                    "input_schema": {
                                                        "type": "object",
                                                        "properties": {"a": {"type":"integer"},
                                                                       "b": {"type":"integer"}},
                                                        "required": ["a", "b"]}}
                                                  }
```

---

## 4. 和 LSP（Language Server Protocol）的关系

MCP 规范自己承认借鉴了 LSP：

| | LSP | MCP |
| --- | --- | --- |
| 解决的问题 | 编辑器 ↔ 语言工具（M 个编辑器 × N 种语言） | AI 应用 ↔ 数据/工具（M 个应用 × N 个能力） |
| 协议基础 | JSON-RPC 2.0 | JSON-RPC 2.0 |
| 角色 | Client（编辑器）/ Server（语言服务） | Host + Client / Server |
| 能力协商 | `initialize` 交换 capabilities | `initialize` 交换 capabilities |

> 记住这个类比，MCP 的很多设计（initialize 握手、capabilities、notifications）你会立刻觉得眼熟。

---

## 5. MCP 的组成部分（一张全景图）

```
┌────────────────────────────── Host（LLM 应用）──────────────────────────────┐
│                                                                             │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                    │
│   │  Client #1   │   │  Client #2   │   │  Client #3   │   ← 每个 Server 一条│
│   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘                    │
└──────────┼──────────────────┼──────────────────┼────────────────────────────┘
           │                  │                  │
     stdio │          HTTP    │          stdio   │        ← 传输层（Transport）
           │                  │                  │
   ┌───────┴──────┐   ┌───────┴──────┐   ┌───────┴──────┐
   │  Server: 文件 │   │ Server: 数据库│   │ Server: 搜索  │
   │              │   │              │   │              │
   │ Tools  ──────┤   │ Tools        │   │ Tools        │   ← 服务端三大原语
   │ Resources ───┤   │ Resources    │   │ Resources    │
   │ Prompts  ────┤   │ Prompts      │   │ Prompts      │
   └──────────────┘   └──────────────┘   └──────────────┘
```

服务端能提供 3 种原语（Tools / Resources / Prompts），
客户端也能反向提供 3 种（Sampling / Roots / Elicitation），详见 `03_三大原语与传输.md`。

---

## 6. 现实中的 MCP 生态

| 角色 | 现实例子 |
| --- | --- |
| Host | Claude Desktop、Claude Code、VS Code + Copilot、Cursor、Zed、各类 Agent 框架 |
| Server（官方/社区） | 文件系统、Git/GitHub、Postgres/SQLite、Slack、Sentry、Puppeteer、各类云服务 |
| SDK | Python、TypeScript、Java、Kotlin、C#、Go、Ruby、Rust、Swift… |
| 调试工具 | MCP Inspector（`mcp dev` 会调用它） |

**你现在的位置**：准备用 Python SDK 写一个自己的 Server。

---

## 7. 自测

1. 用一句话说明 MCP 和 function calling 的关系。
2. Host 和 Client 有什么区别？一个 Host 能有几个 Client？
3. 为什么说 MCP 让集成从 M × N 变成 M + N？
4. MCP 基于哪种 RPC 协议？这和 LSP 有什么共同点？

答案都在上面的表格里。答不出来就回去再看一遍，否则后面写代码会「照着抄但不懂」。

---

下一篇：`02_架构与协议基础.md`
