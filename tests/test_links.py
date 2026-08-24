"""AC-B / AC-C 系列：双链解析与孤儿 / 断链判定。"""
from pathlib import Path

from vault_analyzer.links import (
    extract_wikilinks,
    find_broken_links,
    find_orphans,
    normalize_target,
)
from vault_analyzer.scanner import Note


def make_note(title, out_links=(), stem=None):
    stem = stem if stem is not None else title
    return Note(
        path=Path(f"/vault/{stem}.md"),
        title=title,
        tags=[],
        word_count=0,
        char_count=0,
        out_links=list(out_links),
    )


# ---- AC-B：extract_wikilinks ----
def test_simple_link():
    assert extract_wikilinks("[[A]]") == ["A"]


def test_alias():
    assert extract_wikilinks("[[A|别名]]") == ["A"]


def test_heading():
    assert extract_wikilinks("[[A#标题]]") == ["A"]


def test_alias_and_heading():
    assert extract_wikilinks("[[A|别名#标题]]") == ["A"]


def test_embed():
    assert extract_wikilinks("![[img.png]]") == ["img.png"]


def test_empty_targets_dropped():
    assert extract_wikilinks("[[]] and [[#x]]") == []


def test_dedup_keeps_order():
    assert extract_wikilinks("[[B]] [[A]] [[B]]") == ["B", "A"]


def test_strips_whitespace():
    assert extract_wikilinks("[[  A  ]]") == ["A"]


def test_normalize_target():
    assert normalize_target("A|别名#标题") == "A"


# ---- AC-C：find_orphans ----
def test_orphan_when_no_incoming_links():
    a = make_note("A", out_links=["B"])
    b = make_note("B")
    assert find_orphans([a, b]) == ["A"]


def test_mutual_links_not_orphan():
    a = make_note("A", out_links=["B"])
    b = make_note("B", out_links=["A"])
    assert find_orphans([a, b]) == []


def test_orphan_case_insensitive():
    a = make_note("A", out_links=["b"])
    b = make_note("B")
    assert find_orphans([a, b]) == ["A"]


def test_self_link_does_not_count():
    a = make_note("A", out_links=["A"])
    assert find_orphans([a]) == ["A"]


# ---- AC-C：find_broken_links ----
def test_broken_link():
    a = make_note("A", out_links=["Missing"])
    b = make_note("B")
    assert find_broken_links([a, b]) == [("A", "Missing")]


def test_no_broken_when_target_exists():
    a = make_note("A", out_links=["B"])
    b = make_note("B")
    assert find_broken_links([a, b]) == []


def test_broken_case_insensitive():
    a = make_note("A", out_links=["b"])
    b = make_note("B")
    assert find_broken_links([a, b]) == []


def test_broken_matches_title_or_stem():
    a = make_note("A", out_links=["My Title"])
    b = make_note("My Title", stem="note-b")
    assert find_broken_links([a, b]) == []
