"""LaTeX → MathML → OMML pipeline using Microsoft's MML2OMML.XSL.

Prerequisites:
    pip install latex2mathml

Usage:
    from latex_to_omml import latex_to_omml
    omml = latex_to_omml(r'\\sum_{n=0}^{\\infty} n\\alpha^n = \\frac{\\alpha}{(1-\\alpha)^2}')
    p._element.append(omml)

``latex_to_omml`` 是唯一入口，默认已完成两件预处理：aligned 环境改写、
n-ary 上下限与 naryPr 归一化。文档里"必须走入口、不要绕过"指的就是它——
不要直接调 ``latex2mathml.converter.convert``，也不要绕过 XSLT 自己拼 OMML。
"""
from __future__ import annotations

import copy
import os

import latex2mathml.converter
from lxml import etree

from omml_helpers import mlim
from specs import expected_lim_loc

# Locate MML2OMML.XSL: env var MATHDOC_MML2OMML overrides, else common Office paths.
MML2OMML_CANDIDATES = [
    r'C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL',
    r'C:\Program Files (x86)\Microsoft Office\root\Office16\MML2OMML.XSL',
]
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

_xslt = None


def _xml_parser():
    """不解析外部实体、不联网的 XML 解析器。

    MathML 文本由 latex2mathml 生成，XSL 来自本机 Office 安装；两者都不该被
    当成可信 XML 直接解析 —— 关掉实体解析与网络访问，避免 XXE（读本地文件 /
    发起请求）这类由输入内容触发的副作用。
    """
    return etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)


def _find_xsl():
    env = os.environ.get('MATHDOC_MML2OMML')
    if env:
        return env
    for cand in MML2OMML_CANDIDATES:
        if os.path.exists(cand):
            return cand
    return MML2OMML_CANDIDATES[0]


def _get_xslt():
    """编译并缓存 XSLT。XSL 缺失时在这里抛异常 —— 这是"引擎可用性"的真实探测点。"""
    global _xslt
    if _xslt is None:
        path = _find_xsl()
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"MML2OMML.XSL not found; set MATHDOC_MML2OMML to its path"
            )
        _xslt = etree.XSLT(etree.parse(path, parser=_xml_parser()))
    return _xslt


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
    """归一化大算符的上下限：∑/∏ 叠排、∫ 走侧边角标，并把 lim 从 sSub 改成 limLow。

    限位规则取自 ``specs.NARY_LIM_LOC``（校验侧用同一份表断言）。``lim_{...}``
    在 latex2mathml 里会产出 ``m:sSub``，这里整体改写成 ``m:limLow``——复用
    ``omml_helpers.mlim``，两处不会各写一份结构而漂移。
    """
    for naryPr in omml_el.findall(f'.//{{{M_NS}}}naryPr'):
        chr_el = naryPr.find(f'{{{M_NS}}}chr')
        if chr_el is None:
            continue
        value = expected_lim_loc(chr_el.get(f'{{{M_NS}}}val'))
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
        ssub.getparent().replace(ssub, mlim(list(base), list(sub)))
    return omml_el


def _m_tag(tag):
    return f'{{{M_NS}}}{tag}'


def _w_tag(tag):
    return f'{{{W_NS}}}{tag}'


def _make_operator_run(char, size_pt=None):
    """构造数学算子 run（∑/∏）；size_pt 指定时写入 w:rPr 字号。"""
    run = etree.Element(_m_tag('r'))
    mrpr = etree.SubElement(run, _m_tag('rPr'))
    sty = etree.SubElement(mrpr, _m_tag('sty'))
    sty.set(_m_tag('val'), 'p')
    if size_pt is not None:
        wrpr = etree.SubElement(run, _w_tag('rPr'))
        rfonts = etree.SubElement(wrpr, _w_tag('rFonts'))
        rfonts.set(_w_tag('ascii'), 'Cambria Math')
        rfonts.set(_w_tag('hAnsi'), 'Cambria Math')
        sz = etree.SubElement(wrpr, _w_tag('sz'))
        sz.set(_w_tag('val'), str(int(round(size_pt * 2))))
        szcs = etree.SubElement(wrpr, _w_tag('szCs'))
        szcs.set(_w_tag('val'), str(int(round(size_pt * 2))))
    t = etree.SubElement(run, _m_tag('t'))
    t.text = char
    return run


def _limit_children(nary, tag):
    el = nary.find(_m_tag(tag))
    return list(el) if el is not None else []


def _stacked_nary(nary, operator_size_pt=None):
    """nary -> limUpp(limLow(算子, 下限), 上限) + 操作数；无上下限时返回 None。"""
    nary_pr = nary.find(_m_tag('naryPr'))
    char = '∑'
    if nary_pr is not None:
        chr_el = nary_pr.find(_m_tag('chr'))
        if chr_el is not None and chr_el.get(_m_tag('val')):
            char = chr_el.get(_m_tag('val'))
    lower = _limit_children(nary, 'sub')
    upper = _limit_children(nary, 'sup')
    if not lower and not upper:
        return None
    op_run = _make_operator_run(char, operator_size_pt)
    lim_low = etree.Element(_m_tag('limLow'))
    base = etree.SubElement(lim_low, _m_tag('e'))
    base.append(op_run)
    if lower:
        lim = etree.SubElement(lim_low, _m_tag('lim'))
        for child in lower:
            lim.append(copy.deepcopy(child))
    if upper:
        lim_upp = etree.Element(_m_tag('limUpp'))
        e = etree.SubElement(lim_upp, _m_tag('e'))
        if lower:
            e.append(lim_low)
        else:
            e.append(op_run)
        sup = etree.SubElement(lim_upp, _m_tag('sup'))
        for child in upper:
            sup.append(copy.deepcopy(child))
        result = [lim_upp]
    else:
        result = [lim_low]
    operand = nary.find(_m_tag('e'))
    if operand is not None:
        for child in list(operand):
            result.append(copy.deepcopy(child))
    return result


def stack_nary_limits(omml_el, operator_size_pt=None):
    """把 ∑/∏ 的上下限从 nary 改成 limUpp/limLow 结构。

    背景：用「行内 oMath + 右制表位编号」做编号公式时，Word 把整条公式当
    inline math 渲染，naryPr 的 limLoc 不生效，∑/∏ 上下限会被压到右侧当角标。
    limUpp(limLow(算子, 下限), 上限) 没有 inline/display 之分，Word 与
    LibreOffice 都只能把上下限叠在算子正上/正下，因此编号公式应走这条路。
    """
    for nary in reversed(list(omml_el.iter(_m_tag('nary')))):
        if nary.getparent() is None:
            continue
        nary_pr = nary.find(_m_tag('naryPr'))
        char = None
        if nary_pr is not None:
            chr_el = nary_pr.find(_m_tag('chr'))
            if chr_el is not None:
                char = chr_el.get(_m_tag('val'))
        # 只处理 ∑/∏（limLoc=undOvr）；∫ 仍走侧边角标
        if char is None or expected_lim_loc(char) != 'undOvr':
            continue
        replacement = _stacked_nary(nary, operator_size_pt)
        if replacement is None:
            continue
        parent = nary.getparent()
        index = parent.index(nary)
        parent.remove(nary)
        for offset, element in enumerate(replacement):
            parent.insert(index + offset, element)
    return omml_el


def latex_to_omml(latex_str, alttext=None, fix_limits=True, stack_limits=False, operator_size_pt=None):
    """把 LaTeX 转成 OMML 元素。**这是唯一需要记住的入口。**

    ``fix_limits=True``（默认）时归一化 n-ary 的上下限排布与 naryPr 结构，
    即文档要求的"走入口"。只有调试转换器本身时才传 ``False``，拿未归一化的
    原始 XSLT 结果。

    ``stack_limits=True`` 时把 ∑/∏ 结构化为 ``m:limUpp(m:limLow(...))``，
    用于「行内 oMath + 制表位编号」的编号公式：Word 把这类公式当 inline math，
    ``limLoc`` 不生效，只有结构化才能保证上下限叠排。``operator_size_pt``
    可同时指定算子字号（编号公式默认用 ``specs.DISPLAY_OPERATOR_SIZE_PT``）。
    """
    latex_str = _rewrite_aligned(latex_str)
    mathml = latex2mathml.converter.convert(latex_str)
    tree = etree.fromstring(mathml.encode(), parser=_xml_parser())
    omml = _get_xslt()(tree).getroot()
    if alttext:
        omml.set('alttext', alttext)
    if fix_limits:
        omml = fix_sum_limits(omml)
    if stack_limits:
        omml = stack_nary_limits(omml, operator_size_pt=operator_size_pt)
    return omml


# ---- 兼容别名 ---------------------------------------------------------------
# 下面三个名字是历史入口，行为已与 latex_to_omml 一致（都做完整归一化）。
# 新代码用 latex_to_omml 即可；保留别名是为了不破坏既有生成脚本的 import。

def latex_to_omml_alt(latex_str, alttext=None):
    """兼容别名：等同 ``latex_to_omml(latex_str, alttext)``。"""
    return latex_to_omml(latex_str, alttext)


def latex_to_omml_fixed(latex_str):
    """兼容别名：等同 ``latex_to_omml(latex_str)``。"""
    return latex_to_omml(latex_str)


def latex_to_omml_fixed_alt(latex_str, alttext=None):
    """兼容别名：等同 ``latex_to_omml(latex_str, alttext)``。"""
    return latex_to_omml(latex_str, alttext)
