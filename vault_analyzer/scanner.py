"""目录扫描与 Note 构建。"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import frontmatter, links


@dataclass(frozen=True)
class Note:
    path: Path
    title: str
    tags: list[str]
    word_count: int
    char_count: int
    out_links: list[str]


# 英文 / 数字连续序列
_WORD_RE = re.compile(r"[A-Za-z0-9]+")
# 单个汉字（CJK 统一表意文字）
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
# 一级标题 ``# 标题``
_HEADING_RE = re.compile(r"^\s*#\s+(.+?)\s*$")


def find_markdown_files(root: Path) -> list[Path]:
    """递归返回 ``root`` 下所有 ``.md`` 文件，跳过以 ``.`` 开头的隐藏目录。"""
    root = Path(root)
    if not root.is_dir():
        return []
    files: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        files.append(path)
    return files


def count_words(text: str) -> int:
    """统计字数：中文逐字计 1，英文 / 数字连续序列计 1。"""
    if not text:
        return 0
    return len(_WORD_RE.findall(text)) + len(_CJK_RE.findall(text))


def count_characters(text: str) -> int:
    """统计去空白后的字符数。"""
    return sum(1 for ch in text if not ch.isspace())


def analyze_file(path: Path) -> Note:
    """读取一个 ``.md`` 文件，构建 ``Note``。"""
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    metadata, body = frontmatter.extract_frontmatter(text)
    return Note(
        path=path,
        title=_resolve_title(path, metadata, body),
        tags=frontmatter.get_tags(metadata),
        word_count=count_words(body),
        char_count=count_characters(body),
        out_links=links.extract_wikilinks(body),
    )


def scan_vault(root: Path) -> list[Note]:
    """扫描整个仓库，返回 Note 列表（按文件路径排序）。"""
    return [analyze_file(path) for path in find_markdown_files(root)]


def _resolve_title(path: Path, metadata: dict, body: str) -> str:
    # 优先级：frontmatter title > 首个一级标题 > 文件名 stem
    title = metadata.get("title")
    if isinstance(title, str) and title.strip() != "":
        return title.strip()
    for line in body.split("\n"):
        match = _HEADING_RE.match(line)
        if match:
            return match.group(1).strip()
    return path.stem
