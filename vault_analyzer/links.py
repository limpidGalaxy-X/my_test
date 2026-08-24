"""双链（wikilink）解析与孤儿 / 断链判定。"""
from __future__ import annotations

import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # 仅用于类型标注，避免循环导入
    from .scanner import Note

_WIKILINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")


def extract_wikilinks(text: str) -> list[str]:
    """提取正文中的双链目标（去别名、去锚点、去空白、去重并保持首现顺序）。"""
    results: list[str] = []
    seen: set[str] = set()
    for raw in _WIKILINK_RE.findall(text or ""):
        target = normalize_target(raw)
        if target == "":
            continue
        if target not in seen:
            seen.add(target)
            results.append(target)
    return results


def normalize_target(raw: str) -> str:
    """把 ``[[A|别名#标题]]`` 归一化为 ``A``：取 ``|`` 前、再去掉 ``#`` 后。"""
    raw = raw.split("|", 1)[0]
    raw = raw.split("#", 1)[0]
    return raw.strip()


def find_orphans(notes: Iterable["Note"]) -> list[str]:
    """返回孤儿笔记的 title 列表（没有任何*其他*笔记链接到它，大小写不敏感）。"""
    notes = list(notes)
    orphans: list[str] = []
    for note in notes:
        names = _known_names(note)
        is_orphan = True
        for other in notes:
            if other is note:
                continue
            if any(target.lower() in names for target in other.out_links):
                is_orphan = False
                break
        if is_orphan:
            orphans.append(note.title)
    return orphans


def find_broken_links(notes: Iterable["Note"]) -> list[tuple[str, str]]:
    """返回断链列表 ``(来源笔记 title, 断链目标)``。

    断链 = 出链目标不在「所有笔记的文件名 stem ∪ title」集合中（大小写不敏感）。
    """
    notes = list(notes)
    all_names: set[str] = set()
    for note in notes:
        all_names |= _known_names(note)

    broken: list[tuple[str, str]] = []
    for note in notes:
        for target in note.out_links:
            if target.lower() not in all_names:
                broken.append((note.title, target))
    return broken


def _known_names(note: "Note") -> set[str]:
    """某笔记的「已知名」集合（小写）：文件名 stem 与 title。"""
    names = {note.title.lower()}
    if note.path is not None:
        names.add(note.path.stem.lower())
    names.discard("")
    return names
