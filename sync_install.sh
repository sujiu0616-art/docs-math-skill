#!/usr/bin/env bash
# 把本仓库（math-doc skill 的唯一真相源）同步到各 agent 的 skills 目录。
#
# 要点：
#   * SRC 是**本仓库自身**（脚本所在目录），不是某个安装副本 —— 之前的方向是把
#     某个安装目录当源头，导致仓库里的通用化修复永远同步不进来。
#   * 目标覆盖本机实际存在的安装位置。旧版只写 .claude / .codex，漏掉了 .agents，
#     而 .agents 正是唯一产生过功能分叉的副本 —— 遗漏目标 = 修复滞留。
#   * 同步前清理缓存与构建产物，避免 __pycache__ / .pytest_cache 被复制过去。
#   * --dry-run 只打印将要执行的动作，便于先确认再动手。
#
# 用法：
#   bash sync_install.sh              # 同步到所有已存在的目标
#   bash sync_install.sh --dry-run    # 只看会做什么
#   INSTALL_TARGETS="$HOME/.zcode/skills/math-doc" bash sync_install.sh   # 只同步指定目标

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

# 目标：默认覆盖常见 agent 的 skills 目录；环境变量 INSTALL_TARGETS 可覆盖（空格分隔）。
DEFAULT_TARGETS=(
  "$HOME/.zcode/skills/math-doc"
  "$HOME/.agents/skills/math-doc"
  "$HOME/.codex/skills/math-doc"
  "$HOME/.claude/skills/math-doc"
)
if [[ -n "${INSTALL_TARGETS:-}" ]]; then
  read -r -a TARGETS <<< "$INSTALL_TARGETS"
else
  TARGETS=("${DEFAULT_TARGETS[@]}")
fi

# 不同步的内容：缓存、构建产物、版本控制、脚本自身。
EXCLUDES=(
  --exclude=__pycache__
  --exclude=.pytest_cache
  --exclude=.git
  --exclude='*.pyc'
  --exclude=sync_install.sh
)

echo "SRC: $SRC"
[[ $DRY_RUN -eq 1 ]] && echo "模式: dry-run（不会改动任何文件）"
echo

for DST in "${TARGETS[@]}"; do
  if [[ ! -d "$DST" ]]; then
    echo "跳过（目标不存在）: $DST"
    continue
  fi
  echo "同步 -> $DST"
  if [[ $DRY_RUN -eq 1 ]]; then
    # 列出将被覆盖的文件数，便于确认范围
    count=$(find "$SRC" -mindepth 1 \
      -path '*/__pycache__' -prune -o \
      -path '*/.pytest_cache' -prune -o \
      -path '*/.git' -prune -o \
      -name '*.pyc' -prune -o \
      -name 'sync_install.sh' -prune -o \
      -type f -print | wc -l)
    echo "   将复制 $count 个文件（保留目标中未被同步的其它文件）"
    continue
  fi
  # 用 rsync 时保留目标中的额外文件（不 rm -rf 整个目录，避免误删用户手动放的东西）；
  # 缓存与构建产物不复制，并在目标侧清掉历史遗留。
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete-excluded "${EXCLUDES[@]}" "$SRC/" "$DST/"
  else
    # 无 rsync（多为 Git Bash）时的回退：先清缓存，再按条目复制。
    find "$DST" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
    find "$DST" -name '.pytest_cache' -type d -prune -exec rm -rf {} + 2>/dev/null || true
    for entry in "$SRC"/*; do
      name="$(basename "$entry")"
      [[ "$name" == "sync_install.sh" ]] && continue
      cp -r "$entry" "$DST/"
    done
    cp -f "$SRC/.gitignore" "$DST/.gitignore" 2>/dev/null || true
  fi
  # 兜底：目标侧不留缓存
  find "$DST" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
  find "$DST" -name '.pytest_cache' -type d -prune -exec rm -rf {} + 2>/dev/null || true
  echo "   完成"
done

echo
echo "同步结束。校验一致性可逐文件比对哈希。"
