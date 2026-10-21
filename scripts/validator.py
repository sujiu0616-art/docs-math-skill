#!/usr/bin/env python3
"""Validate a generated math-doc .docx file.

Usage:
    python validator.py path.docx --level 2

Exit code 0 means the document passed the requested checks.

字体与结构规则取自 ``specs.py``（生成侧用同一份常量），改一处不会两侧漂移。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from specs import (  # noqa: E402
    FONT_BODY_CN,
    FONT_HEADING_CN,
    FONT_LATIN,
    FONT_TITLE_CN,
    TABLE_HEADER_FILL,
    expected_lim_loc,
)


def collect_stats(doc_or_path) -> dict:
    """文档规模统计（公式数、表格数、文本字数）。校验与交付报告共用同一实现。

    接受 ``Document`` 对象或路径 —— 调用方已经打开文档时不必重复打开。
    （``docx.Document`` 是工厂函数而非类，故按路径类型分派，不用 isinstance 判定。）
    """
    if isinstance(doc_or_path, (str, Path)):
        doc = Document(str(doc_or_path))
    else:
        doc = doc_or_path
    body = doc.element.body
    return {
        'equations': sum(1 for _ in body.iter(qn('m:oMath'))),
        'tables': len(doc.tables),
        'chars': sum(len(t.text or '') for t in body.iter(qn('w:t'))),
    }


def _in_code_block(t_el) -> bool:
    """w:t 是否位于代码块段落（该段存在 Consolas 字体 run）内。

    代码块是逐字引用的源程序，里面出现 **、$ 等都是正常内容，
    不能用"markdown 残留"的判据去卡它。
    """
    p = t_el
    while p is not None and p.tag != qn('w:p'):
        p = p.getparent()
    if p is None:
        return False
    for r in p.iter(qn('w:r')):
        rpr = r.find(qn('w:rPr'))
        if rpr is not None:
            rf = rpr.find(qn('w:rFonts'))
            if rf is not None and rf.get(qn('w:ascii')) == 'Consolas':
                return True
    return False


def check_basic(doc: Document) -> list[str]:
    body = doc.element.body
    checks = []

    stats = collect_stats(doc)
    if stats['equations'] == 0:
        raise AssertionError('no OMML equations found')
    checks.append(f"equations={stats['equations']}")

    empty_e = [e for e in body.iter(qn('m:e')) if not e.getchildren()]
    if empty_e:
        raise AssertionError(
            f'{len(empty_e)} empty m:e elements; '
            'check bare |...| absolute values and use \\left|...\\right|'
        )
    checks.append('no empty m:e')

    for ssub in body.iter(qn('m:sSub')):
        if ''.join(ssub.itertext()).startswith('lim'):
            raise AssertionError('lim must use m:limLow, not m:sSub')

    for t_el in body.iter(qn('w:t')):
        t = t_el.text or ''
        if _in_code_block(t_el):
            continue
        if '**' in t:
            raise AssertionError(f"stray ** in text: {t[:60]}")
        if '$' in t:
            has_cjk = any('\u4e00' <= c <= '\u9fff' for c in t)
            if has_cjk and '...' not in t:
                raise AssertionError(f"suspicious $ in CJK context: {t[:60]}")
        if t != t.strip():
            raise AssertionError(f"leading/trailing space in text: {t[:60]}")

    checks.append('no markdown residue')
    checks.append('no leading/trailing spaces')
    return checks


def check_math_layout(doc: Document) -> list[str]:
    body = doc.element.body
    for nary_pr in body.iter(qn('m:naryPr')):
        chr_el = nary_pr.find(qn('m:chr'))
        lim_el = nary_pr.find(qn('m:limLoc'))
        op = chr_el.get(qn('m:val')) if chr_el is not None else None
        expected = expected_lim_loc(op)
        if expected and (lim_el is None or lim_el.get(qn('m:val')) != expected):
            raise AssertionError(f'{op} must use limLoc={expected}')
    return ['nary limits ok']


def _style_east_asia(doc: Document, style_name: str):
    """取样式级的 eastAsia 字体名；样式缺失时返回 None。"""
    if style_name not in doc.styles:
        return None
    rpr = doc.styles[style_name].element.find(qn('w:rPr'))
    rfonts = rpr.find(qn('w:rFonts')) if rpr is not None else None
    return rfonts.get(qn('w:eastAsia')) if rfonts is not None else None


def check_academic(doc: Document) -> list[str]:
    checks = check_math_layout(doc)

    # 正文中文字体须与 specs 的默认约定一致。
    # 若项目以既有 docx 为样式基线且基线另有约定（如方正小标宋简体），以基线为准，
    # 此时本项不适用 —— 详见 references/validator.md。
    east = _style_east_asia(doc, 'Normal')
    if east != FONT_BODY_CN:
        raise AssertionError(f'Normal eastAsia must be {FONT_BODY_CN} (got {east!r})')

    normal = doc.styles['Normal']
    rpr = normal.element.find(qn('w:rPr'))
    rfonts = rpr.find(qn('w:rFonts')) if rpr is not None else None
    if rfonts is not None and (
        rfonts.get(qn('w:ascii')) != FONT_LATIN or rfonts.get(qn('w:hAnsi')) != FONT_LATIN
    ):
        raise AssertionError(f'Normal Latin/digits must be {FONT_LATIN}')
    checks.append('Normal font ok')

    for name in ('Heading 1', 'Heading 2', 'Heading 3'):
        if name not in doc.styles:
            continue
        if _style_east_asia(doc, name) != FONT_HEADING_CN:
            raise AssertionError(f'{name} eastAsia must be {FONT_HEADING_CN}')
        style = doc.styles[name]
        rpr = style.element.find(qn('w:rPr'))
        rfonts = rpr.find(qn('w:rFonts')) if rpr is not None else None
        if rfonts.get(qn('w:ascii')) != FONT_LATIN or rfonts.get(qn('w:hAnsi')) != FONT_LATIN:
            raise AssertionError(f'{name} Latin/digits must be {FONT_LATIN}')
        if name == 'Heading 2' and style.font.bold is not True:
            raise AssertionError('Heading 2 must be bold')
    checks.append('Heading fonts ok')

    # 大标题检查：仅当文档实际使用了 Title 样式段落时生效；
    # run 级大标题（普通段落 + run 字体）由生成脚本负责，不在此检查。
    if any(p.style.name == 'Title' for p in doc.paragraphs):
        if _style_east_asia(doc, 'Title') != FONT_TITLE_CN:
            raise AssertionError(f'Title eastAsia must be {FONT_TITLE_CN}')
    checks.append('Title font ok')

    for table in doc.tables:
        grid = table._tbl.tblGrid
        cols = grid.findall(qn('w:gridCol')) if grid is not None else []
        actual = [int(c.get(qn('w:w'), 0)) for c in cols]
        if len(actual) != len(table.columns):
            raise AssertionError('tblGrid column count mismatch')
        if not all(w > 0 for w in actual):
            raise AssertionError('tblGrid contains zero-width columns')

        rows = table._tbl.findall(qn('w:tr'))
        if not rows:
            continue
        first_tr_pr = rows[0].find(qn('w:trPr'))
        if first_tr_pr is None or first_tr_pr.find(qn('w:tblHeader')) is None:
            raise AssertionError('first table row must repeat as header')
        if first_tr_pr.find(qn('w:cantSplit')) is None:
            raise AssertionError('header row must be cantSplit')

        for tc in rows[0].findall(qn('w:tc')):
            tc_pr = tc.find(qn('w:tcPr'))
            if tc_pr is None:
                continue
            shd = tc_pr.find(qn('w:shd'))
            if shd is None or shd.get(qn('w:fill')) != TABLE_HEADER_FILL:
                raise AssertionError(f'header cells must use fill {TABLE_HEADER_FILL}')
            v_align = tc_pr.find(qn('w:vAlign'))
            if v_align is None or v_align.get(qn('w:val')) != 'center':
                raise AssertionError('cells must use vAlign=center')

        for row in rows[1:]:
            for tc in row.findall(qn('w:tc')):
                tc_pr = tc.find(qn('w:tcPr'))
                if tc_pr is None:
                    continue
                v_align = tc_pr.find(qn('w:vAlign'))
                if v_align is None or v_align.get(qn('w:val')) != 'center':
                    raise AssertionError('cells must use vAlign=center')

    checks.append(f'tables={len(doc.tables)} ok')
    return checks


def validate_docx(path: str | Path, level: int = 1) -> list[str]:
    doc_path = Path(path)
    if not doc_path.exists():
        raise FileNotFoundError(doc_path)

    doc = Document(str(doc_path))
    checks = check_basic(doc)
    if level >= 2:
        checks.extend(check_academic(doc))
    if level >= 3:
        for section in doc.sections:
            if section.page_width.cm < 10 or section.page_height.cm < 10:
                raise AssertionError('page size looks invalid')
        checks.append('page size ok')
    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description='Validate math-doc .docx output.')
    parser.add_argument('docx', type=Path, help='generated .docx file')
    parser.add_argument('--level', type=int, choices=(1, 2, 3), default=1)
    args = parser.parse_args()

    try:
        checks = validate_docx(args.docx, level=args.level)
    except (AssertionError, FileNotFoundError) as exc:
        print(f'FAIL: {exc}')
        raise SystemExit(1)
    print('OK: ' + ', '.join(checks))


if __name__ == '__main__':
    main()
