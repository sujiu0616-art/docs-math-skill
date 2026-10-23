
#!/usr/bin/env python3
"""Manage the math-doc personal lesson store (safe, user-confirmed).

Design goals (2026-10-23 review):
- 默认只生成候选条目并打印，不写文件；写入/删除必须由用户在交互式终端确认。
- 非 TTY 环境（模型/脚本/管道）一律拒绝写入 --yes 也不能绕过。
- 每条带 ID、日期、来源，便于回滚；--remove <ID> 删除一条。
- 文件在 skill 目录之外（~/.config/math-doc/user-lessons.md），sync_install.sh 不覆盖。

Usage:
    python scripts/mathdoc_learn.py --add "教训" --root-cause "根因" --fix "修复" --verify "验证" --task "任务"
        → 只预览，不写入；用户确认后加 --yes
    python scripts/mathdoc_learn.py --add "..." --yes   # 需要交互式终端，用户输入 y
    python scripts/mathdoc_learn.py --list
    python scripts/mathdoc_learn.py --remove L-20261023-01
    python scripts/mathdoc_learn.py --path
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

DEFAULT_PATH = Path.home() / '.config' / 'math-doc' / 'user-lessons.md'
USER_LESSONS = Path(os.environ.get('MATHDOC_USER_LESSONS') or DEFAULT_PATH)

HEADER = (
    '# user-lessons.md — 个人经验库（math-doc）\n'
    '\n'
    '由 scripts/mathdoc_learn.py 管理；默认只预览，写入/删除需交互式终端确认。\n'
    '每条带 ID（L-YYYYMMDD-NN）、日期、来源，可用 --remove <ID> 回滚。\n'
    '此文件位于 skill 目录之外，sync_install.sh 同步安装不会覆盖。\n'
)


def _load() -> str:
    if not USER_LESSONS.exists():
        return ''
    return USER_LESSONS.read_text(encoding='utf-8')


def _next_id(text: str, today: str) -> str:
    compact = today.replace('-', '')
    pattern = re.compile(r'\[L-' + re.escape(compact) + r'-(\d+)\]')
    nums = [int(m.group(1)) for m in pattern.finditer(text)]
    return f'L-{compact}-{(max(nums) + 1) if nums else 1:02d}'


def _entry(lesson: str, root_cause: str | None, fix: str | None,
           verify: str | None, task: str | None, source: str,
           entry_id: str, today: str) -> str:
    lines = [
        f'### [{entry_id}] {lesson}',
        f'- 日期：{today}',
        f'- 来源：{source}',
    ]
    if task:
        lines.append(f'- 任务：{task}')
    if root_cause:
        lines.append(f'- 根因：{root_cause}')
    if fix:
        lines.append(f'- 修复：{fix}')
    if verify:
        lines.append(f'- 验证：{verify}')
    return '\n'.join(lines) + '\n'


def _insert(text: str, today: str, entry: str) -> str:
    if not text.strip():
        text = HEADER
    heading = f'## {today}'
    if heading in text:
        start = text.index(heading)
        nxt = text.find('\n## ', start + 1)
        if nxt == -1:
            return text.rstrip('\n') + '\n\n' + entry
        prefix = text[:nxt].rstrip('\n')
        suffix = text[nxt:].lstrip('\n')
        return prefix + '\n\n' + entry + '\n' + suffix
    return text.rstrip('\n') + '\n\n' + heading + '\n\n' + entry


def _remove(text: str, entry_id: str) -> tuple[str, bool]:
    pattern = re.compile(r'^### \[' + re.escape(entry_id) + r'\].*$', re.MULTILINE)
    m = pattern.search(text)
    if not m:
        return text, False
    start = m.start()
    next_sub = text.find('\n### [', m.end())
    next_sec = text.find('\n## ', m.end())
    candidates = [i for i in (next_sub, next_sec) if i != -1]
    end = min(candidates) if candidates else len(text)
    text = text[:start] + text[end:]
    text = re.sub(r'\n{3,}', '\n\n', text)
    date_heading = re.search(r'^## \d{4}-\d{2}-\d{2}\s*$', text, re.MULTILINE)
    if date_heading:
        start_d = date_heading.start()
        nxt = text.find('\n## ', start_d + 1)
        section = text[start_d:(nxt if nxt != -1 else len(text))]
        if len(section.strip().splitlines()) == 1:
            text = text[:start_d] + (text[nxt + 1:] if nxt != -1 else '')
    return text, True


def main() -> int:
    parser = argparse.ArgumentParser(description='math-doc personal lessons: preview / confirm / rollback.')
    parser.add_argument('--add', help='教训内容（默认只预览；加 --yes 才写入）')
    parser.add_argument('--root-cause', help='根因')
    parser.add_argument('--fix', help='修复')
    parser.add_argument('--verify', help='验证')
    parser.add_argument('--task', help='任务名（可选）')
    parser.add_argument('--source', default='用户确认', help='来源（默认：用户确认）')
    parser.add_argument('--yes', action='store_true', help='写入意图（仍需交互式 TTY 确认；非 TTY 拒绝）')
    parser.add_argument('--remove', metavar='ID', help='删除指定 ID 的条目')
    parser.add_argument('--list', action='store_true', help='打印全部经验')
    parser.add_argument('--path', action='store_true', help='打印经验文件路径')
    args = parser.parse_args()

    if args.path:
        print(USER_LESSONS)
        return 0
    if args.list:
        text = _load()
        print(text if text else '(empty)')
        return 0
    if args.remove:
        text = _load()
        if not text:
            print('error: user-lessons 不存在', file=sys.stderr)
            return 1
        if not sys.stdin.isatty():
            print('拒绝删除：非交互环境。请用户在自己的终端运行并确认。', file=sys.stderr)
            return 3
        try:
            answer = input(f'确认删除 {args.remove}？[y/N] ')
        except EOFError:
            print('cancelled', file=sys.stderr)
            return 1
        if answer.strip().lower() not in ('y', 'yes'):
            print('cancelled')
            return 1
        new_text, ok = _remove(text, args.remove)
        if not ok:
            print(f'error: 找不到条目 {args.remove}', file=sys.stderr)
            return 1
        USER_LESSONS.write_text(new_text, encoding='utf-8')
        print(f'removed {args.remove}')
        return 0
    if args.add:
        if not args.add.strip():
            print('error: --add 需要教训内容', file=sys.stderr)
            return 1
        text = _load()
        if f'- 教训：{args.add}' in text or f'] {args.add}' in text:
            print(f'skip: 该教训已存在: {args.add[:60]}')
            return 0
        today = date.today().isoformat()
        entry_id = _next_id(text, today)
        entry = _entry(args.add, args.root_cause, args.fix, args.verify,
                       args.task, args.source, entry_id, today)
        if not args.yes:
            print('候选条目（尚未写入）：')
            print(entry)
            print('确认后请在交互式终端加 --yes 再执行；回滚用 --remove ' + entry_id)
            return 2
        if not sys.stdin.isatty():
            print('拒绝写入：检测到非交互环境（stdin 不是 TTY）。', file=sys.stderr)
            print('请用户在自己的终端运行同一命令并输入 y 确认，模型/脚本不能代写。', file=sys.stderr)
            return 3
        try:
            answer = input('确认写入上述条目？[y/N] ')
        except EOFError:
            print('cancelled', file=sys.stderr)
            return 1
        if answer.strip().lower() not in ('y', 'yes'):
            print('cancelled')
            return 1
        USER_LESSONS.parent.mkdir(parents=True, exist_ok=True)
        USER_LESSONS.write_text(_insert(text, today, entry), encoding='utf-8')
        print(f'added {entry_id} to {USER_LESSONS}')
        return 0
    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
