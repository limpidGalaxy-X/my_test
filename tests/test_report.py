"""AC-E 系列：报告生成。"""
from pathlib import Path

from vault_analyzer.report import VaultStats, build_stats, generate_report
from vault_analyzer.scanner import Note


def make_note(title, tags=(), out_links=(), words=0, chars=0, stem=None):
    stem = stem if stem is not None else title
    return Note(
        path=Path(f"/vault/{stem}.md"),
        title=title,
        tags=list(tags),
        word_count=words,
        char_count=chars,
        out_links=list(out_links),
    )


def test_report_has_title_and_overview():
    stats = VaultStats(2, 10, 20, {}, [], [])
    r = generate_report(stats)
    assert "# Obsidian 仓库分析报告" in r
    assert "- 笔记数：2" in r
    assert "- 总字数：10" in r
    assert "- 总字符数：20" in r
    assert "- 标签种类数：0" in r


def test_report_empty_sections_show_none():
    stats = VaultStats(0, 0, 0, {}, [], [])
    r = generate_report(stats)
    assert r.count("（无）") == 3  # 标签频率 / 孤儿笔记 / 断链


def test_tag_frequency_sorted_desc():
    a = make_note("A", tags=["x", "y"])
    b = make_note("B", tags=["y"])
    stats = build_stats([a, b])
    assert list(stats.tag_frequency.items()) == [("y", 2), ("x", 1)]


def test_tag_frequency_tie_alphabetical():
    a = make_note("A", tags=["b"])
    b = make_note("B", tags=["a"])
    stats = build_stats([a, b])
    assert list(stats.tag_frequency.items()) == [("a", 1), ("b", 1)]


def test_build_stats_aggregates():
    a = make_note("A", tags=["t"], out_links=["B", "Missing"], words=3, chars=5)
    b = make_note("B", words=2, chars=4)
    stats = build_stats([a, b])
    assert stats.total_notes == 2
    assert stats.total_words == 5
    assert stats.total_chars == 9
    assert stats.tag_frequency == {"t": 1}
    assert stats.orphans == ["A"]
    assert stats.broken_links == [("A", "Missing")]


def test_report_includes_broken_table():
    stats = VaultStats(2, 0, 0, {}, [], [("A", "Missing")])
    r = generate_report(stats)
    assert "| 来源 | 目标 |" in r
    assert "| A | Missing |" in r
