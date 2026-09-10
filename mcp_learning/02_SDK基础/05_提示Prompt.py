r"""
05 - 提示词（Prompt）：用户主动选择的工作流模板

Host 通常把 Prompt 渲染成斜杠命令 / 按钮，例如输入框里打 `/code_review`。
**用户点菜，服务器上菜** —— 这是 Prompt 和 Tool 的本质区别。

返回值两种写法：
  * 返回 str          -> 变成一条 role="user" 的消息
  * 返回 list[Message]-> 多轮对话（UserMessage / AssistantMessage 混排）

注意：Prompt 的参数只是**扁平的命名字符串列表**，没有 JSON Schema 校验。
缺必填参数会让整个请求失败。

运行：
    .\.venv\Scripts\python.exe "05_提示Prompt.py"
    .\.venv\Scripts\python.exe "05_提示Prompt.py" --serve
"""

from __future__ import annotations

import asyncio
import sys

from mcp.server import MCPServer
from mcp.server.mcpserver import AssistantMessage, UserMessage

mcp = MCPServer("PromptShowcase", instructions="演示 MCP 提示词模板的写法。")


# ---------------------------------------------------------------------------
# 1. 最简单：返回 str -> 一条 user 消息
# ---------------------------------------------------------------------------
@mcp.prompt(title="代码评审")
def code_review(code: str, language: str = "python") -> str:
    """Ask the model to review a piece of code."""
    return (
        f"请以资深 {language} 工程师的身份评审下面这段代码。\n"
        f"要求：\n"
        f"1. 指出潜在 bug 和安全问题\n"
        f"2. 给出改进建议，按重要性排序\n"
        f"3. 最后给出改写后的版本\n\n"
        f"```{language}\n{code}\n```"
    )


# ---------------------------------------------------------------------------
# 2. 多轮对话：返回 list[Message]
#    可以预置一个 assistant 回复，做 few-shot 示例
# ---------------------------------------------------------------------------
@mcp.prompt(title="写提交信息", description="按团队规范生成 git commit message")
def commit_message(diff: str) -> list[UserMessage | AssistantMessage]:
    """Generate a git commit message following the team convention."""
    return [
        UserMessage("我们团队的 commit message 规范是这样的，请先记住。"),
        AssistantMessage(
            "好的，请把规范发给我。\n\n（示例）\n"
            "feat(scope): 新增功能\n"
            "fix(scope): 修复缺陷\n"
            "docs(scope): 文档变更\n"
            "refactor(scope): 重构（不改变行为）"
        ),
        UserMessage("明白。现在请根据下面的 diff 生成一条符合规范的 commit message：\n\n" + diff),
    ]


# ---------------------------------------------------------------------------
# 3. 多个可选参数：全部给默认值，这样 Host 上只显示一个输入框
# ---------------------------------------------------------------------------
@mcp.prompt(title="解释代码")
def explain(topic: str, level: str = "beginner", language: str = "中文") -> str:
    """Explain a code concept at a given level."""
    return (
        f"请用{language}向一个 {level} 解释「{topic}」。\n"
        f"要求：先用一个生活类比，再给最小可运行示例，最后列出 3 个常见误区。"
    )


# ---------------------------------------------------------------------------
# 4. 无参数 Prompt：纯粹的固定工作流
# ---------------------------------------------------------------------------
@mcp.prompt(title="每日站会")
def daily_standup() -> str:
    """A fixed three-question standup template."""
    return (
        "请按下面三个问题逐个问我，一次只问一个，等我回答后再问下一个：\n"
        "1. 昨天完成了什么？\n"
        "2. 今天计划做什么？\n"
        "3. 有什么阻塞？"
    )


# ---------------------------------------------------------------------------
# 自测
# ---------------------------------------------------------------------------
async def demo() -> None:
    from mcp import Client

    async with Client(mcp) as client:
        print("=" * 72)
        print("1) prompts/list：Host 会把这些渲染成斜杠命令")
        print("=" * 72)
        listed = await client.list_prompts()
        for p in listed.prompts:
            args = ", ".join(
                f"{a.name}{'' if a.required else '?'}" for a in (p.arguments or [])
            )
            print(f"  /{p.name:<16} title={p.title!r}  参数: ({args})")
            print(f"      description={p.description!r}")

        print()
        print("=" * 72)
        print("2) prompts/get：传入参数，拿到渲染后的消息")
        print("=" * 72)
        result = await client.get_prompt("code_review", {"code": "print('hi')", "language": "python"})
        print(f"  description={result.description!r}")
        for i, msg in enumerate(result.messages, 1):
            text = getattr(msg.content, "text", msg.content)
            print(f"  --- message {i} role={msg.role} ---")
            print("  " + str(text).replace("\n", "\n  "))

        print()
        print("=" * 72)
        print("3) 多轮消息（返回 list[Message]）")
        print("=" * 72)
        result = await client.get_prompt("commit_message", {"diff": "diff --git a/x.py b/x.py\n+print(1)"})
        for i, msg in enumerate(result.messages, 1):
            text = getattr(msg.content, "text", msg.content)
            print(f"  [{i}] {msg.role}: {str(text)[:70].replace(chr(10), ' / ')}...")

        print()
        print("=" * 72)
        print("4) 省略可选参数（用默认值）")
        print("=" * 72)
        result = await client.get_prompt("explain", {"topic": "装饰器"})
        print("  " + str(getattr(result.messages[0].content, "text", "")).replace("\n", "\n  "))

        print()
        print("=" * 72)
        print("5) 无参数 Prompt")
        print("=" * 72)
        result = await client.get_prompt("daily_standup", {})
        print("  " + str(getattr(result.messages[0].content, "text", "")).replace("\n", "\n  "))

        print()
        print("=" * 72)
        print("6) 缺必填参数 / 未知 Prompt")
        print("=" * 72)
        for name, args in [("code_review", {}), ("not_exist", {})]:
            try:
                await client.get_prompt(name, args)
                print(f"  {name}{args} -> 竟然成功了？")
            except Exception as exc:  # noqa: BLE001
                print(f"  {name}{args} -> {type(exc).__name__}: {str(exc)[:90]}")

        print()
        print("  ⚠ 注意：客户端只看到 'Internal server error'，")
        print("     真实原因（ValueError: Missing required arguments: {'code'}）")
        print("     只在**服务器端的日志**里。这就是为什么调试时一定要看 stderr。")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        mcp.run()
    else:
        asyncio.run(demo())
