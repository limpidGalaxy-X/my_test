"""AC-F 系列：命令行入口。"""
from vault_analyzer.cli import main


def test_main_empty_dir(tmp_path, capsys):
    rc = main(["--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "# Obsidian 仓库分析报告" in captured.out
    assert "- 笔记数：0" in captured.out


def test_main_scans_root(tmp_path, capsys):
    (tmp_path / "n.md").write_text("# Hello\n", encoding="utf-8")
    rc = main(["--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "- 笔记数：1" in captured.out


def test_main_default_root_is_cwd(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "x.md").write_text("content", encoding="utf-8")
    rc = main([])
    captured = capsys.readouterr()
    assert rc == 0
    assert "- 笔记数：1" in captured.out
