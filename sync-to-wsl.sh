#!/usr/bin/env bash
# sync-to-wsl.sh —— 把 Windows 侧的暂存副本，单向推送到 WSL 里的 ~/hello-devops
#
# 用法（在 Windows 的 PowerShell / CMD 里敲）：
#   wsl -d Ubuntu-22.04 -- bash /mnt/e/PyTest/sync-to-wsl.sh --check    # 只看状态，不改任何东西
#   wsl -d Ubuntu-22.04 -- bash /mnt/e/PyTest/sync-to-wsl.sh            # 同步（有未提交改动会中止）
#   wsl -d Ubuntu-22.04 -- bash /mnt/e/PyTest/sync-to-wsl.sh --force    # 忽略未提交改动，强行覆盖
#
# 设计原则（重要）：
#   * 单向：只从 Windows 推到 WSL，绝不反向。
#   * 唯一的"家"是 $DST：你运行的代码、venv、docker build 都在那边。
#   * 安全：目标仓库有未提交改动时默认【中止】，绝不悄悄覆盖你的东西。
#   * 幂等：重复运行结果一样。
set -uo pipefail

SRC="/mnt/e/PyTest/hello-devops"      # 暂存区（在 Windows 侧写字的地方）
DST="$HOME/hello-devops"              # 唯一的家（你运行代码的地方）

FORCE=0
CHECK=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --check) CHECK=1 ;;
  esac
done

echo "=============================================="
echo "  源（暂存）: $SRC"
echo "  目标（家）: $DST"
echo "=============================================="

[ -d "$SRC" ] || { echo "✗ 源目录不存在：$SRC"; exit 1; }
if [ ! -d "$DST" ]; then
  echo "✗ 目标不存在。先手动初始化一次："
  echo "    cp -r $SRC ~/hello-devops"
  exit 1
fi

cd "$DST" || exit 1

# ---------- 状态体检 ----------
if [ -d .git ]; then
  echo ""
  echo "=== git 体检 ==="
  echo "分支            : $(git branch --show-current 2>/dev/null || echo '(尚未产生)')"
  echo "user.name       : [$(git config --global user.name)]"
  echo "user.email      : [$(git config --global user.email)]"
  echo "最近提交        : $(git log --oneline -1 2>/dev/null || echo '（还没有任何提交）')"
  echo ""
  DIRTY=$(git status --porcelain | wc -l)
  echo "未提交改动      : $DIRTY 个"
  if [ "$DIRTY" -gt 0 ]; then
    git status --short | head -40
  fi
else
  echo "提示：目标还不是 git 仓库（建议 cd ~/hello-devops && git init）"
  DIRTY=0
fi

if [ "$CHECK" -eq 1 ]; then
  echo ""
  echo "=== 两边内容差异预览（$SRC → $DST）==="
  echo "    differ  = 内容不同，同步时会被覆盖"
  echo "    Only in $DST = 只在你那边有（同步不会删除它）"
  echo ""
  diff -rq "$SRC" "$DST" 2>/dev/null | grep -v '/\.git' | grep -v '\.venv' | head -50
  echo ""
  echo "（--check 模式：什么都没改）"
  exit 0
fi

# ---------- 安全检查：目标有未提交改动就不覆盖 ----------
if [ "${DIRTY:-0}" -gt 0 ] && [ "$FORCE" -ne 1 ]; then
  echo ""
  echo "✗ 已中止，没有覆盖任何文件。"
  echo "  处理办法（二选一）："
  echo "    1) 先存档： cd ~/hello-devops && git add -A && git commit -m \"wip: 同步前的基线\""
  echo "    2) 确认丢弃： wsl -d Ubuntu-22.04 -- bash /mnt/e/PyTest/sync-to-wsl.sh --force"
  exit 9
fi
[ "${DIRTY:-0}" -gt 0 ] && echo "（--force 已指定：继续覆盖）"

# ---------- 复制 ----------
echo ""
echo "=== 开始复制 ==="
cp -r "$SRC"/. "$DST"/ || { echo "✗ 复制失败"; exit 1; }

echo ""
echo "=== 复制后的目标内容 ==="
ls -la "$DST"
echo ""
echo "--- docs/ ---"
ls -la "$DST/docs" 2>/dev/null

# ---------- 结果汇报 ----------
if [ -d "$DST/.git" ]; then
  echo ""
  echo "=== git status：以上这些就是本次推送的改动 ==="
  echo "    （想看清改了什么： git -C $DST diff）"
  git -C "$DST" status --short
fi

echo ""
echo "✓ 同步完成。"
echo "  唯一生效的代码在：$DST"
echo "  下一步："
echo "    cd ~/hello-devops && code .        # 用 VS Code 的 WSL 门打开"
echo "    git add -A && git commit -m \"docs: 同步工程思维 / venv 手册\""
