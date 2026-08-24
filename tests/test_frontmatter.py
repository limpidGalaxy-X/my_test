"""AC-A 系列：frontmatter 解析。"""
from vault_analyzer.frontmatter import extract_frontmatter, get_tags


def test_no_frontmatter_returns_original():
    text = "# Hello\n\nbody\n"
    meta, body = extract_frontmatter(text)
    assert meta == {}
    assert body == text


def test_empty_text():
    assert extract_frontmatter("") == ({}, "")


def test_leading_blank_lines_before_frontmatter():
    text = "\n\n---\ntitle: X\n---\nbody\n"
    meta, body = extract_frontmatter(text)
    assert meta == {"title": "X"}
    assert body == "body\n"


def test_missing_closing_dash_means_no_frontmatter():
    text = "---\ntitle: X\n"
    meta, body = extract_frontmatter(text)
    assert meta == {}
    assert body == text


def test_key_value_stripped():
    meta, _ = extract_frontmatter("---\ntitle:  My Note  \n---\nbody")
    assert meta == {"title": "My Note"}


def test_list_items():
    meta, _ = extract_frontmatter("---\ntags:\n  - a\n  - b\n---\nbody")
    assert meta == {"tags": ["a", "b"]}


def test_inline_list():
    meta, _ = extract_frontmatter("---\ntags: [a, b]\n---\nbody")
    assert meta == {"tags": ["a", "b"]}


def test_body_is_text_after_closing():
    text = "---\ntitle: X\n---\n# 标题\n\n正文\n"
    meta, body = extract_frontmatter(text)
    assert meta == {"title": "X"}
    assert body == "# 标题\n\n正文\n"


def test_get_tags_from_list_dedupes():
    assert get_tags({"tags": ["a", "b", "a"]}) == ["a", "b"]


def test_get_tags_from_comma_string():
    assert get_tags({"tags": "a, b, a"}) == ["a", "b"]


def test_get_tags_single_string():
    assert get_tags({"tags": "a"}) == ["a"]


def test_get_tags_missing():
    assert get_tags({}) == []
