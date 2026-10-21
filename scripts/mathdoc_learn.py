#!/usr/bin/env python3
"""Append lessons to the user experience file — the "dynamic skill" store.

The skill reads this file automatically before each generation task and
appends new lessons automatically after each task (see SKILL.md
"Auto-Learning").  The file lives OUTSIDE the skill directory
(~/.config/math-doc/user-lessons.md) so sync_install.sh never overwrites it.

Usage:
    python scripts/mathdoc_learn.py --add "教训一句话"
    python scripts/mathdoc_learn.py --add "问题" --root-cause "根因" --fix "修复" --verify "验证"
    python scripts/mathdoc_learn.py --add "..." --task "某项目"     # 可选标注任务
    python scripts/mathdoc_learn.py --list
    python scripts/mathdoc_learn.py --path
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

USER_LESSONS = Path.home() / '.config' / 'math-doc' / 'user-lessons.md'

HEADER = (
    '# user-lessons.md — 个人经验库（math-doc 自动追加）\n'
    '\n'
    '由 `scripts/mathdoc_learn.py` 在每次任务完成时自动追加，下次生成前自动读取。\n'
    '此文件位于 skill 目录之外，`sync_install.sh` 同步安装不会覆盖。\n'
    '\n'
)


def _load() -> str:
    if not USER_LESSONS.exists():
        return ''
    return USER_LESSONS.read_text(encoding='utf-8')


def add(lesson: str, root_cause: str | None, fix: str | None,
        verify: str | None, task: str | None) -> None:
    if not lesson:
        raise SystemExit('error: --add 需要教训内容')
    text = _load()
    if f'- 教训：{lesson}' in text:
        print(f'skip: 该教训已存在: {lesson[:40]}')
        return
    if not text:
        text = HEADER
    today = date.today().isoformat()
    lines = []
    if task:
        lines.append(f'- 任务：{task}')
    lines.append(f'- 教训：{lesson}')
    if root_cause:
        lines.append(f'- 根因：{root_cause}')
    if fix:
        lines.append(f'- 修复：{fix}')
    if verify:
        lines.append(f'- 验证：{verify}')
    block = f'\n\n## {today}\n' + '\n'.join(lines) + '\n'
    if f'## {today}' in text:
        # insert into today's section: after its last line
        idx = text.rindex(f'## {today}')
        end = text.find('\n## ', idx + 4)
        end = len(text) if end == -1 else end
        text = text[:end] + '\n'.join(lines) + '\n' + text[end:]
    else:
        text = text.rstrip() + block
    USER_LESSONS.parent.mkdir(parents=True, exist_ok=True)
    USER_LESSONS.write_text(text, encoding='utf-8')
    print(f'appended to {USER_LESSONS}: {lesson[:60]}')


def main() -> None:
    parser = argparse.ArgumentParser(description='math-doc dynamic skill: manage user lessons.')
    parser.add_argument('--add', help='教训内容（自动追加，无需手动编辑文件）')
    parser.add_argument('--root-cause', help='根因')
    parser.add_argument('--fix', help='修复')
    parser.add_argument('--verify', help='验证')
    parser.add_argument('--task', help='任务名（可选）')
    parser.add_argument('--list', action='store_true', help='打印全部经验')
    parser.add_argument('--path', action='store_true', help='打印经验文件路径')
    args = parser.parse_args()

    if args.path:
        print(USER_LESSONS)
        return
    if args.list:
        text = _load()
        print(text if text else '(empty)')
        return
    if args.add:
        add(args.add, args.root_cause, args.fix, args.verify, args.task)
        return
    parser.print_help()


if __name__ == '__main__':
    sys.exit(main())
