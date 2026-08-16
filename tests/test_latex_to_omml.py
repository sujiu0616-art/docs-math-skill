# -*- coding: utf-8 -*-
"""Regression tests for the LaTeX -> OMML pipeline.

Formula set is real production data extracted from the batch chapter-generation
project (Oppenheim ch7-ch10): every formula below was rendered and validated in
a published .docx. These tests keep the converter from silently regressing.

Run:  python -m pytest tests/ -v
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from latex_to_omml import _find_xsl, latex_to_omml_fixed  # noqa: E402

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

_XSL = _find_xsl()
pytestmark = pytest.mark.skipif(
    not os.path.exists(_XSL),
    reason="MML2OMML.XSL not found; set MATHDOC_MML2OMML to run these tests",
)

FORMULAS = [
    r"H(s)=\frac{Y(s)}{X(s)}=\frac{\sum_{k=0}^{M}b_{k}s^{k}}{\sum_{k=0}^{N}a_{k}s^{k}}",
    r"H(z)=\frac{Y(z)}{X(z)}=\frac{\sum_{k=0}^{M}b_{k}z^{-k}}{\sum_{k=0}^{N}a_{k}z^{-k}}",
    r"H_{r}(j\omega)=\frac{e^{j\omega T/2}H(j\omega)}{2\sin(\omega T/2)/\omega}",
    r"X(s)=\int_{-\infty}^{+\infty}x(t)e^{-st}\,dt,\qquad s=\sigma+j\omega",
    r"X(z)=\sum_{n=-\infty}^{+\infty}x[n]z^{-n},\qquad z=re^{j\omega}",
    r"X_{b}(e^{j\omega})=X_{p}(e^{j\omega/N})",
    r"X_{d}(e^{j\Omega})=\frac{1}{T}\sum_{k=-\infty}^{+\infty}X_{c}\left(j\frac{\Omega-2\pi k}{T}\right)",
    r"X_{p}(j\omega)=\frac{1}{T}\sum_{k=-\infty}^{+\infty}X\left(j(\omega-k\omega_{s})\right),\qquad \omega_{s}=\frac{2\pi}{T}",
    r"Y(j\omega)=\frac{1}{2}\left[X(j(\omega-\omega_{c}))+X(j(\omega+\omega_{c}))\right]",
    r"Y(j\omega)=\sum_{k}a_{k}X(j(\omega-k\omega_{c}))",
    r"Y(s)=H(s)X(s)",
    r"Y(z)=H(z)X(z)",
    r"\frac{dx(t)}{dt}\leftrightarrow s\tilde{X}(s)-x(0^{-}),\qquad \frac{d^{2}x(t)}{dt^{2}}\leftrightarrow s^{2}\tilde{X}(s)-sx(0^{-})-x'(0^{-})",
    r"\tilde{X}(s)=\int_{0^{-}}^{+\infty}x(t)e^{-st}\,dt",
    r"\tilde{X}(z)=\sum_{n=0}^{+\infty}x[n]z^{-n}",
    r"p(t)=\sum_{n=-\infty}^{+\infty}\delta(t-nT),\qquad x_{p}(t)=x(t)p(t)=\sum_{n=-\infty}^{+\infty}x(nT)\delta(t-nT)",
    r"x(t)=\frac{1}{2\pi j}\int_{\sigma-j\infty}^{\sigma+j\infty}X(s)e^{st}\,ds",
    r"x[n-1]\leftrightarrow z^{-1}\tilde{X}(z)+x[-1],\qquad x[n+1]\leftrightarrow z\tilde{X}(z)-zx[0]",
    r"x[n]=\frac{1}{2\pi j}\oint X(z)z^{n-1}\,dz",
    r"y(t)=x(t)c(t)",
    r"|X(e^{j\omega})|=\frac{\prod\text{零点向量长度}}{\prod\text{极点向量长度}},\qquad \angle X(e^{j\omega})=\sum\text{零点向量角}-\sum\text{极点向量角}",
    r"|X(j\omega)|=\frac{\prod\text{零点向量长度}}{\prod\text{极点向量长度}},\qquad \angle X(j\omega)=\sum\text{零点向量角}-\sum\text{极点向量角}",
]

def _omml(latex):
    return latex_to_omml_fixed(latex)


@pytest.mark.parametrize("latex", FORMULAS)
def test_converts(latex):
    omml = _omml(latex)
    assert omml is not None


@pytest.mark.parametrize("latex", FORMULAS)
def test_root_is_omath(latex):
    assert _omml(latex).tag == f"{{{M_NS}}}oMath"


@pytest.mark.parametrize("latex", FORMULAS)
def test_no_empty_me(latex):
    empties = [e for e in _omml(latex).iter(f"{{{M_NS}}}e") if not e.getchildren()]
    assert not empties, "empty m:e element (bare |x|? use \\left|...\\right|)"


@pytest.mark.parametrize("latex", FORMULAS)
def test_lim_is_not_ssub(latex):
    for ssub in _omml(latex).iter(f"{{{M_NS}}}sSub"):
        assert not "".join(ssub.itertext()).startswith("lim")


def test_sum_limits_above_and_below():
    omml = _omml(r"\sum_{n=-\infty}^{+\infty} x[n] z^{-n}")
    naries = list(omml.iter(f"{{{M_NS}}}naryPr"))
    assert naries, "expected an n-ary operator (sum)"
    lim = naries[0].find(f"{{{M_NS}}}limLoc")
    assert lim is not None and lim.get(f"{{{M_NS}}}val") == "undOvr"


def test_lim_uses_limlow():
    omml = _omml(r"\lim_{z\to\infty} X(z)")
    assert list(omml.iter(f"{{{M_NS}}}limLow")), "lim must use m:limLow"


def test_abs_left_right_ok():
    omml = _omml(r"\left|X(e^{j\omega})\right|")
    assert list(omml.iter(f"{{{M_NS}}}d"))
