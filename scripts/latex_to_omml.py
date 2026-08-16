"""
LaTeX → MathML → OMML pipeline using Microsoft's MML2OMML.XSL.

Prerequisites:
    pip install latex2mathml
    
Usage:
    from latex_to_omml import latex_to_omml, fix_sum_limits
    omml = latex_to_omml(r'\\sum_{n=0}^{\\infty} n\\alpha^n = \\frac{\\alpha}{(1-\\alpha)^2}')
    omml = fix_sum_limits(omml)  # Ensure limits are above/below
    p._element.append(omml)
"""

import latex2mathml.converter
from lxml import etree
import os

# Locate MML2OMML.XSL: env var MATHDOC_MML2OMML overrides, else common Office paths.
MML2OMML_CANDIDATES = [
    r'C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL',
    r'C:\Program Files (x86)\Microsoft Office\root\Office16\MML2OMML.XSL',
]
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

_xslt = None

def _find_xsl():
    env = os.environ.get('MATHDOC_MML2OMML')
    if env:
        return env
    for cand in MML2OMML_CANDIDATES:
        if os.path.exists(cand):
            return cand
    return MML2OMML_CANDIDATES[0]

def _get_xslt():
    global _xslt
    if _xslt is None:
        path = _find_xsl()
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"MML2OMML.XSL not found; set MATHDOC_MML2OMML to its path"
            )
        _xslt = etree.XSLT(etree.parse(path))
    return _xslt


def latex_to_omml(latex_str):
    """Convert LaTeX string to OMML oMath element."""
    return latex_to_omml_alt(latex_str)


def _rewrite_aligned(latex):
    """LaTeX 预处理：把 latex2mathml 不认识的 aligned 环境改写为 array 环境。

    latex2mathml 会把 aligned 里的对齐符 & 当普通字符输出成 <mi>&</mi>
    （裸 &，非法 XML），导致 etree 解析崩溃、整条转换链失败。array 环境会被
    正确转成 OMML m:m（多行对齐数组，Word 可编辑）。aligned 的对齐语义为
    「& 前右对齐、后左对齐」，等价 array{rl}；[t]/[b]/[c] 垂直位置参数
    latex2mathml 不支持，安全剥离（仅丢失垂直位置，内容不变）。
    嵌套 aligned 用深度匹配处理。
    """
    parts = []
    pos = 0
    while True:
        start = latex.find(r'\begin{aligned}', pos)
        if start == -1:
            parts.append(latex[pos:])
            return ''.join(parts)
        parts.append(latex[pos:start])
        body_pos = start + len(r'\begin{aligned}')
        if body_pos < len(latex) and latex[body_pos] == '[':
            eb = latex.find(']', body_pos)
            if eb != -1:
                body_pos = eb + 1  # 剥离 [t]/[b]/[c]
        depth = 1
        scan = body_pos
        matched = None
        while scan <= len(latex):
            nb = latex.find(r'\begin{aligned}', scan)
            ne = latex.find(r'\end{aligned}', scan)
            if ne == -1:
                break
            if nb != -1 and nb < ne:
                depth += 1
                scan = nb + len(r'\begin{aligned}')
            else:
                depth -= 1
                if depth == 0:
                    matched = ne
                    break
                scan = ne + len(r'\end{aligned}')
        if matched is None:
            # 无配对的 \end{aligned}：原样保留剩余，避免丢内容
            parts.append(latex[start:])
            return ''.join(parts)
        body = _rewrite_aligned(latex[body_pos:matched])  # 递归处理嵌套 aligned
        parts.append(r'\begin{array}{rl}' + body + r'\end{array}')
        pos = matched + len(r'\end{aligned}')


def latex_to_omml_alt(latex_str, alttext=None):
    """Convert LaTeX to OMML and optionally preserve alttext on the oMath root."""
    latex_str = _rewrite_aligned(latex_str)
    mathml = latex2mathml.converter.convert(latex_str)
    tree = etree.fromstring(mathml.encode())
    xslt = _get_xslt()
    omml = xslt(tree).getroot()
    if alttext:
        omml.set('alttext', alttext)
    return omml


def mathml_to_omml_alt(mathml_elem, alttext=None):
    """Convert a MathML element to OMML, preserving MathML alttext when present."""
    xslt = _get_xslt()
    omml = xslt(mathml_elem).getroot()
    if alttext is None:
        alttext = mathml_elem.get('alttext')
    if alttext:
        omml.set('alttext', alttext)
    return omml


def _narypr_cambria(naryPr):
    """Normalize naryPr to the reference layout (verified above/below in Word/WPS):

    remove subHide/supHide and append ctrlPr with Cambria Math.  MML2OMML.XSL always
    emits subHide/supHide="off"; the reference document structure (which renders
    above/below correctly) has ctrlPr and no subHide/supHide.
    """
    for tag in ('subHide', 'supHide'):
        el = naryPr.find(f'{{{M_NS}}}{tag}')
        if el is not None:
            naryPr.remove(el)
    if naryPr.find(f'{{{M_NS}}}ctrlPr') is None:
        ctrl = etree.SubElement(naryPr, f'{{{M_NS}}}ctrlPr')
        rpr = etree.SubElement(ctrl, f'{{{W_NS}}}rPr')
        rfonts = etree.SubElement(rpr, f'{{{W_NS}}}rFonts')
        rfonts.set(f'{{{W_NS}}}ascii', 'Cambria Math')
        rfonts.set(f'{{{W_NS}}}hAnsi', 'Cambria Math')


def fix_sum_limits(omml_el):
    """Fix n-ary limits by symbol: sum/product above/below, integral to the side.

    Also normalizes naryPr to the reference structure (ctrlPr Cambria Math, no
    subHide/supHide) and replaces `lim_{...}` rendered as m:sSub with m:limLow.
    """
    for naryPr in omml_el.findall(f'.//{{{M_NS}}}naryPr'):
        chr_el = naryPr.find(f'{{{M_NS}}}chr')
        if chr_el is None:
            continue
        op = chr_el.get(f'{{{M_NS}}}val')
        value = 'undOvr' if op in ('∑', '∏') else 'subSup' if op == '∫' else None
        if value is None:
            continue
        lim_loc = naryPr.find(f'{{{M_NS}}}limLoc')
        if lim_loc is not None:
            lim_loc.set(f'{{{M_NS}}}val', value)
        else:
            ll = etree.SubElement(naryPr, f'{{{M_NS}}}limLoc')
            ll.set(f'{{{M_NS}}}val', value)
        _narypr_cambria(naryPr)

    for ssub in list(omml_el.iter(f'{{{M_NS}}}sSub')):
        if not ''.join(ssub.itertext()).startswith('lim'):
            continue
        base = ssub.find(f'{{{M_NS}}}e')
        sub = ssub.find(f'{{{M_NS}}}sub')
        if base is None or sub is None:
            continue
        lim_low = etree.Element(f'{{{M_NS}}}limLow')
        e = etree.SubElement(lim_low, f'{{{M_NS}}}e')
        lim = etree.SubElement(lim_low, f'{{{M_NS}}}lim')
        for child in list(base):
            e.append(child)
        for child in list(sub):
            lim.append(child)
        ssub.getparent().replace(ssub, lim_low)
    return omml_el


def latex_to_omml_fixed(latex_str):
    """Convert LaTeX to OMML with summation limits fixed."""
    return fix_sum_limits(latex_to_omml(latex_str))


def latex_to_omml_fixed_alt(latex_str, alttext=None):
    """Convert LaTeX to OMML with limits fixed and optional alttext preserved."""
    return fix_sum_limits(latex_to_omml_alt(latex_str, alttext))
