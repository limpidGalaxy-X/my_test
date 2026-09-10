r"""
04_实战项目 / client.py —— 一个"像 Agent 一样"的 MCP 客户端

它演示了一个真实 Host 内部会做的事：

    1. 连接服务器，读取 instructions 和工具清单
    2. 让"模型"（这里是写死的规则）决定调用哪个工具
    3. 调用工具 -> 拿到结构化结果
    4. 需要原文时读资源
    5. 需要模板时取 prompt

三种连接方式：
    .\.venv\Scripts\python.exe client.py                 # 内存直连 server.mcp（默认）
    .\.venv\Scripts\python.exe client.py --stdio         # 把 server.py 拉起来当子进程
    .\.venv\Scripts\python.exe client.py --http http://127.0.0.1:8000/mcp
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

HERE = Path(__file__).parent
SERVER_FILE = HERE / "server.py"


# ---------------------------------------------------------------------------
# 一个"玩具大脑"：根据用户问题决定调用哪个工具
# 真实 Host 里这一步是 LLM 的 function calling
# ---------------------------------------------------------------------------
def plan(question: str, tool_names: list[str]) -> tuple[str, dict]:
    q = question.lower()
    if "标签" in question or "tag" in q:
        return "list_tags", {}
    if "全部" in question or "所有笔记" in question or "列出" in question:
        return "list_notes", {}
    if "读" in question and "#" in question:
        note_id = question.split("#", 1)[1].strip().split()[0]
        return "get_note", {"note_id": note_id}
    # 默认：搜索
    keyword = question.replace("搜索", "").replace("找", "").strip() or ""
    return "search_notes", {"keyword": keyword, "limit": 5}


async def run(client: Client) -> None:
    print("=" * 74)
    print(f"已连接：{client.server_info.name}   协议版本：{client.protocol_version}")
    print("=" * 74)
    info = await client.list_tools()
    tools = {t.name: t for t in info.tools}
    print(f"可用工具：{list(tools)}")
    print(f"instructions：{client.instructions}")
    print()

    questions = [
        "搜索 学习",
        "列出所有笔记",
        "有哪些标签",
        "读 #<第一个ID>",
    ]

    # 先放两篇笔记，保证有数据可查
    for title, content, tags in [
        ("MCP 速记", "MCP 用 JSON-RPC 2.0；工具由模型调用，资源由应用读取。", ["mcp"]),
        ("Python 装饰器", "functools.wraps 是必须写的，否则元信息丢失。", ["python"]),
    ]:
        r = await client.call_tool("add_note", {"title": title, "content": content, "tags": tags})
        print(f"  [准备数据] + {r.structured_content['id']} {r.structured_content['title']}")

    listed = (await client.call_tool("list_notes", {})).structured_content["result"]
    if listed:
        questions[3] = f"读 #{listed[0]['id']}"

    for question in questions:
        tool_name, args = plan(question, list(tools))
        print()
        print(f"👤 用户：{question}")
        print(f"🤖 决定调用：{tool_name}({json.dumps(args, ensure_ascii=False)})")

        result = await client.call_tool(tool_name, args)
        if result.is_error:
            print(f"   ⚠️ 调用失败：{result.content[0].text}")
            continue

        if tool_name == "get_note":
            note = result.structured_content
            print(f"   📄 {note['title']}  标签={note['tags']}")
            # 需要"原文"时读资源（而不是工具返回的 JSON）
            read = await client.read_resource(f"notes://note/{note['id']}")
            print("   📎 资源原文：")
            for line in read.contents[0].text.splitlines():
                print(f"      {line}")

            prompt = await client.get_prompt("review_note", {"note_id": note["id"]})
            print(f"   🧩 可用提示词：{prompt.messages[0].content.text.splitlines()[0]}")
        else:
            print(f"   ✅ 结构化结果：{json.dumps(result.structured_content, ensure_ascii=False)[:150]}")

    print()
    print("=" * 74)
    print("清理演示数据")
    print("=" * 74)
    for item in listed:
        if item["title"] in ("MCP 速记", "Python 装饰器"):
            await client.call_tool("delete_note", {"note_id": item["id"], "confirm": True})
            print(f"  已删除 {item['id']} {item['title']}")


async def main() -> None:
    if "--stdio" in sys.argv:
        params = StdioServerParameters(command=sys.executable, args=[str(SERVER_FILE), "--serve"])
        print(f"以 stdio 启动子进程：{params.command} {params.args}")
        async with Client(params) as client:
            await smoke(client)
        return

    if "--http" in sys.argv:
        idx = sys.argv.index("--http")
        url = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "http://127.0.0.1:8000/mcp"
        async with Client(url) as client:
            await smoke(client)
        return

    # 默认：内存直连（把 server.py 当模块导入，直接拿它的 mcp 对象）
    sys.path.insert(0, str(HERE))
    import server  # noqa: E402  （server.py 里的 if __name__ == "__main__" 不会执行）

    async with Client(server.mcp) as client:
        await run(client)


async def smoke(client: Client) -> None:
    """stdio / HTTP 模式下只做只读检查（不写数据，避免污染真实笔记库）。"""
    print("=" * 74)
    print(f"已连接：{client.server_info.name}   协议版本：{client.protocol_version}")
    print("=" * 74)
    for t in (await client.list_tools()).tools:
        print(f"  {t.name:<14}{t.description}")
    print()
    print("资源模板：", [t.uri_template for t in (await client.list_resource_templates()).resource_templates])
    print("提示词：", [p.name for p in (await client.list_prompts()).prompts])


if __name__ == "__main__":
    asyncio.run(main())
