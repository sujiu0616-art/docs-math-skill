# OMML and Formula Conversion

## Canonical Pipeline

```text
LaTeX -> latex2mathml -> MathML -> MML2OMML.XSL -> OMML -> docx
```

必须优先走 latex2mathml -> XSLT，不手工构造 OMML；只有 latex2mathml 无法表达、或 XSLT 不可用的边缘公式才用下面的手工 OMML 结构。

## Dependencies

- `pip install latex2mathml`
- Microsoft `MML2OMML.XSL`，通常为 `C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL`
- 首次调用验证 `etree.XSLT(etree.parse(xsl_path))` 能编译成功
- 环境缺失时报告，不静默切换为 Unicode 文本或手工 OMML

## XSLT Template Mapping

```xml
<xsl:template match="m:math">     -> <m:oMath>
<xsl:template match="m:mrow">     -> <xsl:apply-templates/>
<xsl:template match="m:mi|m:mn|m:mo|m:mtext"> -> <m:r><m:t>
<xsl:template match="m:mfrac">    -> <m:f><m:num>/<m:den>
<xsl:template match="m:msup">     -> <m:sSup><m:e>/<m:sup>
<xsl:template match="m:msub">     -> <m:sSub><m:e>/<m:sub>
<xsl:template match="m:msqrt">    -> <m:rad><m:deg/><m:e>
<xsl:template match="m:mstyle">   -> <xsl:apply-templates/>
```

`\underbrace` 检测用 XPath predicate：

```xml
<xsl:template match="m:munder[m:munder/m:mo[text()='⏟']]">
  <!-- build m:limLow + m:groupChr + m:lim -->
</xsl:template>
```

## Integral, Summation, and Limit Placement

| 符号 | 限制位置 | OMML 值 |
|---|---|---|
| 积分 `∫` | 侧边角标 | `limLoc="subSup"` |
| 求和 `∑`、连乘 `∏` | 正上下方 | `limLoc="undOvr"` |
| `lim` | `lim` 下方 | `m:limLow`，不用 `m:sSub` |

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def fix_integral_limits_and_lim(body):
    for naryPr in body.iter(qn('m:naryPr')):
        chr_el = naryPr.find(qn('m:chr'))
        if chr_el is None:
            continue
        op = chr_el.get(qn('m:val'))
        lim = naryPr.find(qn('m:limLoc'))
        if op == '∫':
            if lim is None:
                lim = OxmlElement('m:limLoc')
                naryPr.append(lim)
            lim.set(qn('m:val'), 'subSup')

    for ssub in list(body.iter(qn('m:sSub'))):
        if not ''.join(ssub.itertext()).startswith('lim'):
            continue
        base = ssub.find(qn('m:e'))
        sub = ssub.find(qn('m:sub'))
        if base is None or sub is None:
            continue
        limlow = OxmlElement('m:limLow')
        e = OxmlElement('m:e')
        lim = OxmlElement('m:lim')
        for child in list(base):
            e.append(child)
        for child in list(sub):
            lim.append(child)
        limlow.append(e)
        limlow.append(lim)
        ssub.getparent().replace(ssub, limlow)
```

`fix_sum_limits()` 不能无脑把全部 `nary` 改成 `undOvr`；生成后应定向修正积分和 `lim`。

## Inline Math Must Be OMML

正文行内数学和展示公式使用同一套 OMML 规则。禁止 Unicode 凑角标、正体变量、ASCII `|` 代替绝对值。

## Absolute Value Safety Rule

Never generate `|x|` as plain text, and do not use `\|x\|` as an absolute-value workaround.

This is a generation-side safety rule, not only a validator backstop. The generator must prevent bare `|...|` before it reaches latex2mathml.

Use one of these:

```text
\left|x\right|
\left|X(j\omega)\right|^2
\frac{1}{\left|a\right|}
```

Or use the OMML delimiter structure for manual construction:

```python
mabs([mr("x", italic=True)])
```

Reason: ASCII `|` may produce invalid MathML/OMML. For example, standalone `|X(j\omega)|^2` is converted to an empty `<m:e>`, so the validator reports `empty m:e` only after generation. The generation side must prevent this by always emitting `\left|...\right|` or `mabs`.

| Symbol type | Example | Style | OMML |
|---|---|---|---|
| Variable | x, t, C, a, r | italic | `mr("x", italic=True)` |
| Function name | e, sin, cos, Re, Im | upright | `mrn("e")` |
| Operator | =, +, −, ·, >, < | upright | `mrn("=")` |
| Number | 0, 1, 2π | upright | `mrn("0")` |
| Greek variable | ω, θ, φ, α | italic | `mr("ω", italic=True)` |
| Absolute value | `\left|C\right|` | delimiter | `mabs([C_])` |
| Subscript | ω₀ | script | `msub([om_], [mrn("0")])` |
| Superscript | e^{rt} | script | `msup([mrn("e")], [rt_])` |

## Manual OMML Element Reference

| Element | Purpose |
|---|---|
| `m:oMath` | Math block container |
| `m:r` / `m:t` | Math run and text |
| `m:f` / `m:num` / `m:den` | Fraction |
| `m:sSup` / `m:sSub` / `m:e` / `m:sup` / `m:sub` | Scripts |
| `m:d` / `m:begChr` / `m:endChr` | Delimiters and absolute value |
| `m:rad` / `m:deg` / `m:e` | Radical |
| `m:nary` + `limLoc="undOvr"` | Summation/product with under/over limits |
| `m:nary` + `limLoc="subSup"` | Integral with side limits |
| `m:groupChr` | Underbrace/overbrace |
| `m:limLow` / `m:lim` | Lower limit |

## Accessibility

`latex_to_omml_alt(latex, alttext)` 和 `latex_to_omml_fixed_alt(latex, alttext)` 会把 alttext 写到 `m:oMath` 根节点的 `alttext` 属性。Word 不一定原生读取该属性；正文仍应保留可读的线性数学文本。

## Scripts

- `scripts/latex_to_omml.py`: LaTeX -> OMML 管线。
- `scripts/omml_helpers.py`: `mpara_mix`、`mnary`、`mlim`、`mabs` 等 OMML builder。
