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
        xsl_path = _find_xsl()
        if not os.path.exists(xsl_path):
            raise FileNotFoundError(
                f"MML2OMML.XSL not found; set MATHDOC_MML2OMML to its location (tried: {xsl_path})"
            )
        _xslt = etree.XSLT(etree.parse(xsl_path))
    return _xslt


def latex_to_omml(latex_str):
    """Convert LaTeX string to OMML oMath element."""
    return latex_to_omml_alt(latex_str)


def latex_to_omml_alt(latex_str, alttext=None):
    """Convert LaTeX to OMML and optionally preserve alttext on the oMath root."""
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


def fix_sum_limits(omml_el):
    """Fix n-ary limits by symbol: sum/product above/below, integral to the side.

    Also replaces `lim_{...}` rendered as m:sSub with m:limLow.
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
