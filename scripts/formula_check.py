# -*- coding: utf-8 -*-
r"""Batch-verify LaTeX formulas against latex_to_omml BEFORE generating a document.

Catches latex2mathml/XSLT incompatibilities up front instead of mid-generation:
    * 新章节/新文档涉及未用过的公式时，先跑本脚本
    * 0 failures 再写生成脚本；有 FAIL 则换等价写法（如 \left|...\right|）

Usage:
    python scripts/formula_check.py "<latex>..." ["<latex>..."]
    python scripts/formula_check.py --file formulas.txt   # 每行一个公式
    python scripts/formula_check.py < formulas.txt        # stdin

Exit code: 0 = all OK, 1 = at least one failure.
"""
import argparse
import sys
from pathlib import Path

from latex_to_omml import latex_to_omml

HERE = Path(__file__).resolve().parent


def check(expr: str):
    try:
        latex_to_omml(expr)
        return True, ""
    except Exception as e:  # noqa: BLE001 - report any converter failure
        return False, f"{type(e).__name__}: {e}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", help="每行一个 LaTeX 公式的文本文件（UTF-8）")
    ap.add_argument("formulas", nargs="*", help="待验证的 LaTeX 公式")
    args = ap.parse_args()

    if args.file:
        formulas = [
            ln.rstrip("\n")
            for ln in open(args.file, encoding="utf-8")
            if ln.strip()
        ]
    elif args.formulas:
        formulas = args.formulas
    else:
        formulas = [ln.rstrip("\n") for ln in sys.stdin if ln.strip()]

    if not formulas:
        print("no formulas to check", file=sys.stderr)
        return 1

    fails = 0
    for f in formulas:
        ok, err = check(f)
        print(("OK  " if ok else "FAIL") + " " + f + ("" if ok else " -> " + err))
        if not ok:
            fails += 1
    print(f"\n{fails} failures / {len(formulas)} formulas")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
