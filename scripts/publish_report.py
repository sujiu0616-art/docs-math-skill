#!/usr/bin/env python3
"""Delivery report for a generated math-doc: validate and write validation-report.md.

Produces the "source / result / report" deliverable triplet so the recipient can
prove the equations are native OMML (editable in Word), not Unicode or images.

Usage:
    python scripts/publish_report.py result.docx \
        --source source.md --level 2 --report validation-report.md

Exit code 0 = document passed the requested validation level.
失败时同样会写出报告（结论为 FAIL 并附失败原因），便于留痕。
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validator import collect_stats, validate_docx  # noqa: E402
from latex_to_omml import _find_xsl, _get_xslt  # noqa: E402


def probe_engine() -> tuple[bool, str]:
    """真实探测 OMML 引擎：编译一次 XSLT，而不是只看环境变量在不在。

    此前只检查 ``MATHDOC_MML2OMML`` 是否设置，引擎缺失时报告照样写
    "local Office installation"，等于对收件人撒谎。这里以能否编译为准。
    """
    env_set = bool(os.environ.get('MATHDOC_MML2OMML'))
    try:
        _get_xslt()
    except FileNotFoundError:
        return False, f'unavailable — MML2OMML.XSL not found at {_find_xsl()}'
    except Exception as exc:  # noqa: BLE001 - 报告要如实记录任何编译失败
        return False, f'unavailable — XSLT failed to compile ({type(exc).__name__}: {exc})'
    origin = 'MATHDOC_MML2OMML environment variable' if env_set else 'local Office installation'
    return True, f'{origin} ({_find_xsl()})'


def write_report(report_path: Path, docx_path: Path, source_path: Path | None,
                 level: int, checks: list[str], stats: dict | None,
                 engine_ok: bool, engine_desc: str, failure: str | None) -> None:
    source_line = (
        f'- **Source**: `{source_path.name}`' if source_path
        else '- **Source**: not provided'
    )
    lines = [
        '# Validation Report',
        '',
        f'- **Document**: `{docx_path.name}`',
        source_line,
        f'- **Validation level**: {level} (1 basic / 2 academic / 3 publication)',
        f'- **Date**: {date.today().isoformat()}',
        f'- **OMML engine**: Microsoft MML2OMML.XSL — {engine_desc}',
        '',
        '## Artifacts',
        '',
    ]
    if source_path:
        lines.append(f'- `{source_path.name}` — the Markdown/LaTeX source of the document')
    else:
        lines.append('- (source file not kept)')
    lines.append(
        f'- `{docx_path.name}` — the generated Word document '
        '(equations are native OMML, double-click editable in Word)'
    )
    lines.append('- `validation-report.md` — this report')
    lines.append('')

    if stats is not None:
        lines += [
            '## Contents',
            '',
            f'- Equations (OMML): **{stats["equations"]}**',
            f'- Tables: **{stats["tables"]}**',
            f'- Characters: **{stats["chars"]}**',
            '',
        ]

    lines += ['## Validation checks', '']
    if checks:
        for c in checks:
            lines.append(f'- [x] {c}')
    else:
        lines.append('- (no check completed)')
    lines.append('')

    if failure is None:
        lines.append(
            '**Result: PASS** — the document passed every check at this level;'
            ' equations are native OMML, not Unicode text or images.'
        )
    else:
        lines.append(f'**Result: FAIL** — {failure}')

    if not engine_ok:
        lines.append('')
        lines.append(
            '> **注意**：本次未验证公式的 OMML 引擎来源，报告不能作为'
            '"公式是原生 OMML"的证据。'
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text('\n'.join(lines), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Validate a math-doc and write a delivery report.')
    parser.add_argument('docx', type=Path, help='generated .docx file')
    parser.add_argument('--source', type=Path, help='source markdown/LaTeX file, if kept')
    parser.add_argument('--level', type=int, choices=(1, 2, 3), default=2)
    parser.add_argument('--report', type=Path, default=Path('validation-report.md'),
                        help='output validation report path')
    args = parser.parse_args()

    engine_ok, engine_desc = probe_engine()

    try:
        checks = validate_docx(args.docx, level=args.level)
    except (AssertionError, FileNotFoundError) as exc:
        # 校验失败也要留报告：收件人需要知道失败在哪一项，而不是只看到终端一行字。
        write_report(args.report, args.docx, args.source, args.level,
                     [], None, engine_ok, engine_desc, f'{exc}')
        print(f'FAIL: {exc}')
        print(f'report written to {args.report}')
        raise SystemExit(1)

    stats = collect_stats(args.docx)
    write_report(args.report, args.docx, args.source, args.level,
                 checks, stats, engine_ok, engine_desc, None)

    if not engine_ok:
        print(f'WARN: OMML engine {engine_desc}')
    print(f'OK: {len(checks)} checks passed, report written to {args.report}')


if __name__ == '__main__':
    main()
