"""命令行入口。"""
from __future__ import annotations

import argparse
from pathlib import Path

from . import report, scanner


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="vault-analyzer",
        description="扫描 Obsidian 仓库并输出分析报告",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="要扫描的仓库根目录（默认当前目录）",
    )
    args = parser.parse_args(argv)

    notes = scanner.scan_vault(Path(args.root))
    stats = report.build_stats(notes)
    print(report.generate_report(stats), end="")
    return 0
