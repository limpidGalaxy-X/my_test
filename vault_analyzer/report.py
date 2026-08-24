"""汇总统计与 Markdown 报告生成。"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from . import links
from .scanner import Note


@dataclass
class VaultStats:
    total_notes: int
    total_words: int
    total_chars: int
    tag_frequency: dict[str, int]
    orphans: list[str]
    broken_links: list[tuple[str, str]]


def build_stats(notes: Iterable[Note]) -> VaultStats:
    """把 Note 列表汇总为 ``VaultStats``。"""
    notes = list(notes)
    total_notes = len(notes)
    total_words = sum(note.word_count for note in notes)
    total_chars = sum(note.char_count for note in notes)

    freq: dict[str, int] = {}
    for note in notes:
        for tag in note.tags:
            freq[tag] = freq.get(tag, 0) + 1
    tag_frequency = dict(sorted(freq.items(), key=lambda kv: (-kv[1], kv[0])))

    return VaultStats(
        total_notes=total_notes,
        total_words=total_words,
        total_chars=total_chars,
        tag_frequency=tag_frequency,
        orphans=links.find_orphans(notes),
        broken_links=links.find_broken_links(notes),
    )


def generate_report(stats: VaultStats) -> str:
    """生成 Markdown 报告文本（固定结构，便于断言）。"""
    lines: list[str] = []
    lines.append("# Obsidian 仓库分析报告")
    lines.append("")
    lines.append("## 概览")
    lines.append("")
    lines.append(f"- 笔记数：{stats.total_notes}")
    lines.append(f"- 总字数：{stats.total_words}")
    lines.append(f"- 总字符数：{stats.total_chars}")
    lines.append(f"- 标签种类数：{len(stats.tag_frequency)}")
    lines.append("")

    lines.append("## 标签频率")
    lines.append("")
    if stats.tag_frequency:
        lines.append("| 标签 | 次数 |")
        lines.append("| ---- | ---- |")
        for tag, count in stats.tag_frequency.items():
            lines.append(f"| {tag} | {count} |")
    else:
        lines.append("（无）")
    lines.append("")

    lines.append("## 孤儿笔记")
    lines.append("")
    if stats.orphans:
        for orphan in stats.orphans:
            lines.append(f"- {orphan}")
    else:
        lines.append("（无）")
    lines.append("")

    lines.append("## 断链")
    lines.append("")
    if stats.broken_links:
        lines.append("| 来源 | 目标 |")
        lines.append("| ---- | ---- |")
        for src, tgt in stats.broken_links:
            lines.append(f"| {src} | {tgt} |")
    else:
        lines.append("（无）")

    return "\n".join(lines) + "\n"
