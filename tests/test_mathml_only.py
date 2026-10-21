# -*- coding: utf-8 -*-
"""MathML-level tests that do NOT require MML2OMML.XSL.

These run in CI where no Office installation exists. They cover the first half
of the pipeline (LaTeX -> MathML); the OMML half is covered by
test_latex_to_omml.py, which auto-skips without the XSL.
"""
import latex2mathml.converter

FORMULAS = [
    r"\sum_{n=0}^{\infty}\frac{1}{n^{2}}",
    r"\int_{0}^{1}x^{2}\,dx",
    r"\left|a+b\right|\le\left|a\right|+\left|b\right|",
    r"\lim_{x\to 0}\frac{\sin x}{x}",
    r"e^{-j\omega_{0}t}",
    r"\oint_{C}f(z)\,dz",
    r"X(z)=\sum_{n=-\infty}^{+\infty}x[n]z^{-n}",
]


def test_all_formulas_produce_mathml():
    for latex in FORMULAS:
        assert '<math' in latex2mathml.converter.convert(latex)


def test_frac_produces_mathml_fraction():
    assert '<mfrac>' in latex2mathml.converter.convert(r"\frac{1}{2}")


def test_sum_produces_mathml_subsup():
    assert '<msubsup>' in latex2mathml.converter.convert(
        r"\sum_{n=0}^{\infty}n")
