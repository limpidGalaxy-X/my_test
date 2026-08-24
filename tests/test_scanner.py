"""AC-D 系列：目录扫描与统计。"""
from vault_analyzer.scanner import (
    analyze_file,
    count_characters,
    count_words,
    find_markdown_files,
    scan_vault,
)


def write(tmp_path, name, content):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def test_find_markdown_files_recursive_skips_hidden(tmp_path):
    write(tmp_path, "a.md", "")
    write(tmp_path, "sub/b.md", "")
    write(tmp_path, "sub/c.txt", "")
    write(tmp_path, ".hidden/d.md", "")
    names = [p.name for p in find_markdown_files(tmp_path)]
    assert names == ["a.md", "b.md"]


def test_count_words_mixed():
    assert count_words("Hello world 123 你好世界") == 7  # 3 词 + 4 汉字


def test_count_characters_excludes_whitespace():
    assert count_characters("a b\nc") == 3


def test_title_from_frontmatter(tmp_path):
    p = write(tmp_path, "note.md", "---\ntitle: FM Title\n---\nbody")
    assert analyze_file(p).title == "FM Title"


def test_title_from_heading(tmp_path):
    p = write(tmp_path, "note.md", "# 标题一\n\nbody")
    assert analyze_file(p).title == "标题一"


def test_title_from_stem(tmp_path):
    p = write(tmp_path, "my-note.md", "no heading here\n")
    assert analyze_file(p).title == "my-note"


def test_analyze_file_tags_and_counts(tmp_path):
    p = write(tmp_path, "n.md", "---\ntags: [a, b]\n---\n你好 world\n")
    note = analyze_file(p)
    assert note.tags == ["a", "b"]
    assert note.word_count == 3  # 你、好（2 汉字）+ world（1 词）
    assert note.out_links == []


def test_analyze_file_out_links_in_body(tmp_path):
    p = write(tmp_path, "n.md", "---\ntags: x\n---\nSee [[Target]]\n")
    note = analyze_file(p)
    assert note.out_links == ["Target"]


def test_scan_vault_sorted(tmp_path):
    write(tmp_path, "b.md", "# B")
    write(tmp_path, "a.md", "# A")
    assert [n.title for n in scan_vault(tmp_path)] == ["A", "B"]


def test_empty_dir_no_exception(tmp_path):
    assert scan_vault(tmp_path) == []
    assert find_markdown_files(tmp_path) == []


def test_analyze_plain_file(tmp_path):
    p = write(tmp_path, "plain.md", "just text\n")
    note = analyze_file(p)
    assert note.title == "plain"
    assert note.tags == []
    assert note.out_links == []
