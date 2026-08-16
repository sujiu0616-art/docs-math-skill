#!/usr/bin/env python3
"""Delivery report for a generated math-doc: validate and write validation-report.md.

Produces the "source / result / report" deliverable triplet so the recipient can
prove the equations are native OMML (editable in Word), not Unicode or images.

Usage:
    python scripts/publish_report.py result.docx \
        --source source.md --level 2 --report validation-report.md

Exit code 0 = document passed the requested validation level.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validator import validate_docx  # noqa: E402
from latex_to_omml import _find_xsl  # noqa: E402
from docx import Document  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402


def collect_stats(docx_path: Path) -> dict:
    doc = Document(str(docx_path))
    body = doc.element.body
    omath = sum(1 for _ in body.iter(qn('m:oMath')))
    tables = len(doc.tables)
    chars = sum(len(t.text or '') for t in body.iter(qn('w:t')))
    return {'equations': omath, 'tables': tables, 'chars': chars}


def write_report(report_path: Path, docx_path: Path, source_path: Path | None,
                 level: int, checks: list[str], stats: dict, xsl_source: str) -> None:
    lines = [
        '# Validation Report',
        '',
        f'- **Document**: `{docx_path.name}`',
        f'- **Source**: `{source_path.name}`' if source_path else f'- **Source**: not provided',
        f'- **Validation level**: {level} (1 basic / 2 academic / 3 publication)',
        f'- **Date**: {date.today().isoformat()}',
        f'- **OMML engine**: Microsoft MML2OMML.XSL（{xsl_source}）',
        '',
        '## Artifacts',
        '',
        '- `source.md` — the Markdown/LaTeX source of the document',
        f'- `{docx_path.name}` — the generated Word document (equations are native OMML, double-click editable in Word)',
        '- `validation-report.md` — this report',
        '',
        '## Contents',
        '',
        f'- Equations (OMML): **{stats["equations"]}**',
        f'- Tables: **{stats["tables"]}**',
        f'- Characters: **{stats["chars"]}**',
        '',
        '## Validation checks',
        '',
    ]
    for c in checks:
        lines.append(f'- [x] {c}')
    lines.append('')
    lines.append('**Result: PASS** — the document passed every check at this level;'
                 ' equations are native OMML, not Unicode text or images.')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text('\n'.join(lines), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Validate a math-doc and write a delivery report.')
    parser.add_argument('docx', type=Path, help='generated .docx file')
    parser.add_argument('--source', type=Path, help='source markdown/laTeX file, if kept')
    parser.add_argument('--level', type=int, choices=(1, 2, 3), default=2)
    parser.add_argument('--report', type=Path, default=Path('validation-report.md'),
                        help='output validation report path')
    args = parser.parse_args()

    try:
        checks = validate_docx(args.docx, level=args.level)
    except (AssertionError, FileNotFoundError) as exc:
        print(f'FAIL: {exc}')
        raise SystemExit(1)

    stats = collect_stats(args.docx)
    _find_xsl()  # raise early if the engine is missing
    xsl_src = ('MATHDOC_MML2OMML environment variable'
               if 'MATHDOC_MML2OMML' in os.environ
               else 'local Office installation')
    write_report(args.report, args.docx, args.source, args.level, checks, stats, xsl_src)
    print(f'OK: {len(checks)} checks passed, report written to {args.report}')


if __name__ == '__main__':
    main()
