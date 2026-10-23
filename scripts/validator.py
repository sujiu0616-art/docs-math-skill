#!/usr/bin/env python3
"""Validate a generated math-doc .docx file.

Usage:
    python validator.py path.docx --level 2
    python validator.py path.docx --level 2 --style-source baseline
    python validator.py --list-checks

Exit code 0 means the document passed the requested checks.

--style-source default(default) 表示按本 skill 默认格式断言字体/主题/标题对齐；
baseline/user 表示文档有项目模板或用户格式要求，跳过默认格式断言（仍校验公式与表格网格）。

字体与结构规则取自 ``specs.py``（生成侧用同一份常量），改一处不会两侧漂移。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from specs import (  # noqa: E402
    FONT_BODY_CN,
    FONT_HEADING_CN,
    FONT_LATIN,
    FONT_TITLE_CN,
    TABLE_HEADER_FILL,
    THEME_FONT_ATTRS,
    expected_lim_loc,
)

#: 校验项编号 -> 含义。validator.md 的检查项表必须与本表一致；
#: 输出/失败信息统一带编号，文档与脚本对不上时可直接按编号发现。
CHECK_SPECS = {
    'B1': '存在 OMML 公式',
    'B2': '无空 m:e',
    'B3': 'lim 使用 m:limLow',
    'B4': '无 Markdown 残留',
    'B5': '无首尾空格',
    'M1': 'n-ary limLoc 正确',
    'M2': '编号公式 n-ary 已结构化（stack_limits）',
    'S1': 'Normal 字体符合默认（default 专属）',
    'S2': 'Heading 字体符合默认（default 专属）',
    'S3': 'Title 字体符合默认（default 专属）',
    'S4': '无主题字体属性（default 专属）',
    'S5': '大标题居中（default 专属）',
    'T1': '表格网格有效',
    'T2': '表头样式符合默认（default 专属）',
    'P1': '页面尺寸有效',
}


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
        raise AssertionError('[B1] no OMML equations found')
    checks.append(f"[B1] equations={stats['equations']}")

    empty_e = [e for e in body.iter(qn('m:e')) if not e.getchildren()]
    if empty_e:
        raise AssertionError(
            f'[B2] {len(empty_e)} empty m:e elements; '
            'check bare |...| absolute values and use \\left|...\\right|'
        )
    checks.append('[B2] no empty m:e')

    for ssub in body.iter(qn('m:sSub')):
        if ''.join(ssub.itertext()).startswith('lim'):
            raise AssertionError('[B3] lim must use m:limLow, not m:sSub')
    checks.append('[B3] lim m:limLow ok')

    for t_el in body.iter(qn('w:t')):
        t = t_el.text or ''
        if _in_code_block(t_el):
            continue
        if '**' in t:
            raise AssertionError(f"[B4] stray ** in text: {t[:60]}")
        if '$' in t:
            has_cjk = any('\u4e00' <= c <= '\u9fff' for c in t)
            if has_cjk and '...' not in t:
                raise AssertionError(f"[B4] suspicious $ in CJK context: {t[:60]}")
        if t != t.strip():
            raise AssertionError(f"[B5] leading/trailing space in text: {t[:60]}")

    checks.append('[B4] no markdown residue')
    checks.append('[B5] no leading/trailing spaces')
    return checks


def check_math_layout(doc: Document) -> list[str]:
    body = doc.element.body
    for nary_pr in body.iter(qn('m:naryPr')):
        chr_el = nary_pr.find(qn('m:chr'))
        lim_el = nary_pr.find(qn('m:limLoc'))
        op = chr_el.get(qn('m:val')) if chr_el is not None else None
        expected = expected_lim_loc(op)
        if expected and (lim_el is None or lim_el.get(qn('m:val')) != expected):
            raise AssertionError(f'[M1] {op} must use limLoc={expected}')
    return ['[M1] nary limits ok']


def _style_east_asia(doc: Document, style_name: str):
    """取样式级的 eastAsia 字体名；样式缺失时返回 None。"""
    if style_name not in doc.styles:
        return None
    rpr = doc.styles[style_name].element.find(qn('w:rPr'))
    rfonts = rpr.find(qn('w:rFonts')) if rpr is not None else None
    return rfonts.get(qn('w:eastAsia')) if rfonts is not None else None


def _theme_font_attrs(rfonts) -> list[str]:
    """返回 `w:rFonts` 上存在的主题字体属性（带值），用于报错。"""
    found = []
    for attr in THEME_FONT_ATTRS:
        value = rfonts.get(qn('w:' + attr))
        if value is not None:
            found.append(f'w:{attr}={value}')
    return found


def _effective_alignment(paragraph) -> WD_ALIGN_PARAGRAPH:
    """段落有效对齐：段落显式值 > 样式值 > 默认左对齐。"""
    if paragraph.alignment is not None:
        return paragraph.alignment
    style = paragraph.style
    if style is not None and style.paragraph_format.alignment is not None:
        return style.paragraph_format.alignment
    return WD_ALIGN_PARAGRAPH.LEFT


def check_title_alignment(doc: Document) -> None:
    """大标题默认居中：Title 样式段落，或带“方正小标宋简体”字体 run 的段落。

    生成器的骨架标题是 run 级大标题（不走 Title 样式），因此按字体识别；
    用户/模板明确要求左对齐标题时，level 2 不适用（见 references/validator.md）。
    """
    checked = 0
    for index, paragraph in enumerate(doc.paragraphs, start=1):
        is_title_style = paragraph.style is not None and paragraph.style.name == 'Title'
        has_title_font = any(
            rf.get(qn('w:eastAsia')) == FONT_TITLE_CN
            for rf in paragraph._p.iter(qn('w:rFonts'))
        )
        if not (is_title_style or has_title_font):
            continue
        checked += 1
        effective = _effective_alignment(paragraph)
        if effective != WD_ALIGN_PARAGRAPH.CENTER:
            raise AssertionError(
                '[S5] document title must be centered '
                f'(paragraph {index}, got alignment={effective})'
            )


def check_theme_fonts(doc: Document) -> None:
    """主题字体优先于显式字体：使用中的样式与正文 run 的 `w:rFonts` 不得带 *Theme。

    这是 XML 断言的盲区修复：以前只读 w:eastAsia 值，有 Theme 属性时 Word 实际用主题字体，
    validator 仍会通过；现在直接报 FAIL，并提示用 PDF 内嵌字体名复核。
    """
    used = ['Normal']
    used += [name for name in ('Heading 1', 'Heading 2', 'Heading 3') if name in doc.styles]
    if any(p.style.name == 'Title' for p in doc.paragraphs):
        used.append('Title')
    for name in used:
        if name not in doc.styles:
            continue
        style = doc.styles[name]
        rpr = style.element.find(qn('w:rPr'))
        rfonts = rpr.find(qn('w:rFonts')) if rpr is not None else None
        if rfonts is None:
            continue
        present = _theme_font_attrs(rfonts)
        if present:
            raise AssertionError(
                f'[S4] style {name} has theme font attributes ({", ".join(present)}); '
                'Word uses theme fonts over explicit w:rFonts — remove *Theme attrs before setting explicit fonts'
            )
    for rfonts in doc.element.body.iter(qn('w:rFonts')):
        present = _theme_font_attrs(rfonts)
        if present:
            raise AssertionError(
                f'[S4] run-level w:rFonts has theme font attributes ({", ".join(present)}); '
                'explicit fonts will be ignored — remove *Theme attrs'
            )


def check_numbered_equation_nary(doc: Document) -> None:
    """编号公式（行内 oMath + 制表位编号）里的 ∑/∏ 必须结构化为 limUpp/limLow。

    行内 oMath 段落中 Word 按 inline math 排 n-ary，limLoc 不生效，上下限会被压成侧标。
    XML 层面只能靠“段落里是否还有 nary”来拦（属性存在 ≠ 渲染生效）。
    """
    for index, paragraph in enumerate(doc.paragraphs, start=1):
        p = paragraph._p
        if p.find(qn('m:oMathPara')) is not None:
            continue
        omaths = p.findall(qn('m:oMath'))
        if not omaths:
            continue
        has_number_tab = any(run.text and run.text.startswith('\t') for run in paragraph.runs)
        if not has_number_tab:
            continue
        for omath in omaths:
            for nary in omath.iter(qn('m:nary')):
                pr = nary.find(qn('m:naryPr'))
                chr_el = pr.find(qn('m:chr')) if pr is not None else None
                char = chr_el.get(qn('m:val')) if chr_el is not None else None
                if char is None or expected_lim_loc(char) != 'undOvr':
                    continue
                if nary.find(qn('m:sub')) is None or nary.find(qn('m:sup')) is None:
                    continue
                raise AssertionError(
                    f'[M2] numbered equation (paragraph {index}) still uses m:nary for {char}; '
                    'Word renders inline n-ary limits as side scripts — '
                    'build it with latex_to_omml(..., stack_limits=True) (m:limUpp/m:limLow)'
                )


def check_academic(doc: Document, style_source: str = 'default') -> list[str]:
    checks = check_math_layout(doc)
    strict_style = style_source == 'default'

    if strict_style:
        # 正文中文字体须与 specs 的默认约定一致。
        east = _style_east_asia(doc, 'Normal')
        if east != FONT_BODY_CN:
            raise AssertionError(f'[S1] Normal eastAsia must be {FONT_BODY_CN} (got {east!r})')

        normal = doc.styles['Normal']
        rpr = normal.element.find(qn('w:rPr'))
        rfonts = rpr.find(qn('w:rFonts')) if rpr is not None else None
        if rfonts is not None and (
            rfonts.get(qn('w:ascii')) != FONT_LATIN or rfonts.get(qn('w:hAnsi')) != FONT_LATIN
        ):
            raise AssertionError(f'[S1] Normal Latin/digits must be {FONT_LATIN}')
        checks.append('[S1] Normal font ok')

        for name in ('Heading 1', 'Heading 2', 'Heading 3'):
            if name not in doc.styles:
                continue
            if _style_east_asia(doc, name) != FONT_HEADING_CN:
                raise AssertionError(f'[S2] {name} eastAsia must be {FONT_HEADING_CN}')
            style = doc.styles[name]
            rpr = style.element.find(qn('w:rPr'))
            rfonts = rpr.find(qn('w:rFonts')) if rpr is not None else None
            if rfonts.get(qn('w:ascii')) != FONT_LATIN or rfonts.get(qn('w:hAnsi')) != FONT_LATIN:
                raise AssertionError(f'[S2] {name} Latin/digits must be {FONT_LATIN}')
            if name == 'Heading 2' and style.font.bold is not True:
                raise AssertionError('[S2] Heading 2 must be bold')
        checks.append('[S2] Heading fonts ok')

        # 大标题检查：仅当文档实际使用了 Title 样式段落时生效。
        if any(p.style.name == 'Title' for p in doc.paragraphs):
            if _style_east_asia(doc, 'Title') != FONT_TITLE_CN:
                raise AssertionError(f'[S3] Title eastAsia must be {FONT_TITLE_CN}')
        checks.append('[S3] Title font ok')

        check_theme_fonts(doc)
        checks.append('[S4] no theme font attrs')

        check_title_alignment(doc)
        checks.append('[S5] title alignment ok')
    else:
        checks.append(f'[note] style-source={style_source}: skipped S1-S5/T2 default style assertions')

    check_numbered_equation_nary(doc)
    checks.append('[M2] numbered nary stacked ok')

    for table in doc.tables:
        grid = table._tbl.tblGrid
        cols = grid.findall(qn('w:gridCol')) if grid is not None else []
        actual = [int(c.get(qn('w:w'), 0)) for c in cols]
        if len(actual) != len(table.columns):
            raise AssertionError('[T1] tblGrid column count mismatch')
        if not all(w > 0 for w in actual):
            raise AssertionError('[T1] tblGrid contains zero-width columns')

        if not strict_style:
            continue
        rows = table._tbl.findall(qn('w:tr'))
        if not rows:
            continue
        first_tr_pr = rows[0].find(qn('w:trPr'))
        if first_tr_pr is None or first_tr_pr.find(qn('w:tblHeader')) is None:
            raise AssertionError('[T2] first table row must repeat as header')
        if first_tr_pr.find(qn('w:cantSplit')) is None:
            raise AssertionError('[T2] header row must be cantSplit')

        for tc in rows[0].findall(qn('w:tc')):
            tc_pr = tc.find(qn('w:tcPr'))
            if tc_pr is None:
                continue
            shd = tc_pr.find(qn('w:shd'))
            if shd is None or shd.get(qn('w:fill')) != TABLE_HEADER_FILL:
                raise AssertionError(f'[T2] header cells must use fill {TABLE_HEADER_FILL}')
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
                    raise AssertionError('[T2] cells must use vAlign=center')

    checks.append(f'[T1] tables={len(doc.tables)} grid ok'
                  + ('' if strict_style else f' (T2 header style checks skipped, source={style_source})'))
    return checks


def validate_docx(path: str | Path, level: int = 1, style_source: str = 'default') -> list[str]:
    doc_path = Path(path)
    if not doc_path.exists():
        raise FileNotFoundError(doc_path)

    doc = Document(str(doc_path))
    checks = check_basic(doc)
    if level >= 2:
        checks.extend(check_academic(doc, style_source=style_source))
    if level >= 3:
        for section in doc.sections:
            if section.page_width.cm < 10 or section.page_height.cm < 10:
                raise AssertionError('[P1] page size looks invalid')
        checks.append('[P1] page size ok')
    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description='Validate math-doc .docx output.')
    parser.add_argument('docx', type=Path, nargs='?', help='generated .docx file')
    parser.add_argument('--level', type=int, choices=(1, 2, 3), default=1)
    parser.add_argument(
        '--style-source', choices=('default', 'baseline', 'user'), default='default',
        help='文档格式来源：default=按本 skill 默认断言；baseline/user=跳过默认字体/主题/标题/表头样式断言',
    )
    parser.add_argument('--list-checks', action='store_true', help='打印检查项编号与含义后退出')
    args = parser.parse_args()

    if args.list_checks:
        for check_id, desc in CHECK_SPECS.items():
            print(f'{check_id}\t{desc}')
        return
    if args.docx is None:
        parser.error('缺少 docx 路径（除非使用 --list-checks）')

    try:
        checks = validate_docx(args.docx, level=args.level, style_source=args.style_source)
    except (AssertionError, FileNotFoundError) as exc:
        print(f'FAIL: {exc}')
        raise SystemExit(1)
    print('OK: ' + ', '.join(checks))


if __name__ == '__main__':
    main()
