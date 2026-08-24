"""极简 YAML frontmatter 解析器。

只支持本项目需要的子集（见《02-技术方案》4.1）：
- ``key: value``
- 列表项（``- item``）
- 内联列表 ``[a, b]``

不依赖第三方 YAML 库。
"""
from __future__ import annotations


def extract_frontmatter(text: str) -> tuple[dict, str]:
    """解析笔记开头的 YAML frontmatter。

    返回 ``(metadata, body)``：
    - 无 frontmatter 时返回 ``({}, 原文)``；
    - 有 frontmatter 时，body 为结束 ``---`` 之后的剩余文本（换行已归一化为 ``\\n``）。

    metadata 的值为 ``str`` 或 ``list[str]``。
    """
    if not text:
        return {}, ""

    # 归一化 CRLF，便于逐行处理
    lines = [line.rstrip("\r") for line in text.split("\n")]

    # 允许 frontmatter 前有前导空行：找到第一个非空行
    first_content = None
    for idx, line in enumerate(lines):
        if line.strip() != "":
            first_content = idx
            break
    if first_content is None:
        return {}, text

    if lines[first_content].strip() != "---":
        return {}, text

    # 找结束的 ``---``
    end = None
    for i in range(first_content + 1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text

    metadata = _parse_block(lines[first_content + 1 : end])
    body = "\n".join(lines[end + 1 :])
    return metadata, body


def get_tags(metadata: dict) -> list[str]:
    """从 metadata 中归一化标签：列表直接取；字符串按逗号拆分；去重保持顺序。"""
    raw = None
    for key in ("tags", "tag"):
        if key in metadata:
            raw = metadata[key]
            break
    if raw is None:
        return []

    if isinstance(raw, list):
        items = [str(x).strip() for x in raw]
    else:
        items = [part.strip() for part in str(raw).split(",")]

    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item == "":
            continue
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _parse_block(lines: list[str]) -> dict:
    metadata: dict = {}
    current_key: str | None = None

    for line in lines:
        stripped = line.strip()
        if stripped == "":
            continue

        # 列表项
        if stripped.startswith("- "):
            item = stripped[2:].strip()
            if current_key is not None and item != "":
                existing = metadata.get(current_key)
                if isinstance(existing, list):
                    existing.append(item)
                else:
                    metadata[current_key] = [item]
            continue

        # key: value
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if key == "":
                continue

            if value == "":
                # 可能是列表的开头（下一行是 ``- item``）；先占位为列表
                current_key = key
                metadata.setdefault(key, [])
            elif value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                items = [x.strip() for x in inner.split(",") if x.strip() != ""]
                metadata[key] = items
                current_key = None
            else:
                metadata[key] = value
                current_key = None

    return metadata
