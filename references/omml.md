# OMML and Formula Conversion

## Canonical Pipeline

```text
LaTeX -> latex2mathml -> MathML -> MML2OMML.XSL -> OMML -> docx
```

必须优先走 latex2mathml → XSLT，不手工构造 OMML；只有 latex2mathml 无法表达、或 XSLT 不可用的边缘公式才用本文件末尾的手工 OMML 结构。映射由 `MML2OMML.XSL` 完成，项目侧只做归一化（`latex_to_omml.py`）。

## Dependencies

- `pip install latex2mathml`
- Microsoft `MML2OMML.XSL`（可用 `MATHDOC_MML2OMML` 覆盖路径）
- 首次调用验证 `etree.XSLT(etree.parse(xsl_path))` 能编译成功
- 环境缺失时报告，不静默切换为 Unicode 文本或手工 OMML

## Integral, Summation, and Limit Placement

| 符号 | 限制位置 | OMML 值 |
|---|---|---|
| 积分 `∫` | 侧边角标 | `limLoc="subSup"` |
| 求和 `∑`、连乘 `∏` | 正上下方 | `limLoc="undOvr"` |
| `lim` | 下方 | `m:limLow`，不用 `m:sSub` |

naryPr 归一化（移除 `subHide/supHide`、补 `ctrlPr(Cambria Math)`）由 `latex_to_omml()` 入口内的 `fix_sum_limits()` 完成；不要另写第二条“补 limLoc”链。`lim_{...}` 的 `m:sSub` 也由入口改写为 `m:limLow`。

## Inline-Numbered Equations and n-ary Limits

编号公式常用「行内 `m:oMath` + 右制表位 `(n)`」实现（`mathdoc_cli.add_numbered_equation`）。Word 会把整条公式当 **inline math**：`naryPr/limLoc` 不生效，∑/∏ 上下限被压到右侧；XML 断言不报错也可能渲染错误。

修复：编号公式里的 ∑/∏ 用结构

```text
m:limUpp( m:limLow(算子, 下限), 上限 )
```

不要用 `m:nary`。该结构没有 inline/display 之分，Word/LO 都只能叠排。生成侧入口 `latex_to_omml(..., stack_limits=True, operator_size_pt=specs.DISPLAY_OPERATOR_SIZE_PT)` 已封装；∫ 保持侧边角标，不结构化。

## Inline Math Must Be OMML

正文行内数学和展示公式使用同一套 OMML 规则。禁止 Unicode 凑角标、正体变量、ASCII `|` 代替绝对值。

## aligned Environment Safety Rule

禁止把 `\begin{aligned}...\end{aligned}` 直接喂给 latex2mathml：它不识别 aligned，会把 `&` 当普通字符输出成非法 XML，整条转换链崩溃。

`latex_to_omml.py` 的 `_rewrite_aligned()` 已在入口做预处理：aligned → `array{rl}`（& 前右对齐、后左对齐，语义等价），latex2mathml 会转成 OMML `m:m`。`[t]/[b]/[c]` 垂直位置参数不支持，安全剥离；嵌套 aligned 递归处理。任何公式都必须走 `latex_to_omml` 入口，不要直接调 `latex2mathml.converter.convert`。

## Parentheses and Primes

普通括号后接撇号（如 `(\ln x)'`）是 MML2OMML.XSL 的已知脆弱点：XSLT 会把 `)` 和 `′` 一起当成上标，生成 `m:d` 时开括号被放大、闭括号留在内容里，Word 里表现为「括号一大一小」。

生成侧入口会先把**数量配对**的普通 `(` `)` 改写成 `\left(...\right)`：XSLT 生成两侧同缩放的 `m:d`，撇号落在 `m:d` 外层的上标上。已有 `\left(`/`\right)` 或含 `\text{` 的公式不重复包装；括号不配对时保持原样。`[...]` 不自动包装（可能是 `\sqrt[3]{}` 的可选参数），需要时手写 `\left[...\right]`。

## Delimiter-leading Sign

`\left(-x\right)`、`\left(-j\omega\right)` 这类“定界符内以正负号开头”的公式，latex2mathml 会把开头的 `+`/`-` 解析成独立运算符节点，其 `m:e` 落在定界符对象外成为空元素。

生成侧用花括号把符号包成序数原子：`\left({-}x\right)`。这是空 `m:e` 的第二个已知来源（第一个是裸 `|...|`）。

## Display Math Alignment

- 仅含公式的段落会被 Word 当 display math；水平位置由 `m:oMathParaPr/m:jc` 控制（默认 `centerGroup`、`center`、`left`、`right`）。
- 单行独立公式默认居中；不要用空格凑居中。
- 多行对齐用 `aligned`（改写为 `array{rl}` → `m:m`）作为单个公式块，不拆多段。
- 编号属于段落文本（右侧制表位），不要写进 `m:oMath`。
- 场景规则见 `references/docx-style.md` 的 Equation Alignment；用户/模板要求优先。

## Absolute Value Safety Rule

禁止生成裸 `|x|`，也不要用 `\|x\|` 绕过。绝对值/范数统一写：

```text
\left|x\right|
\left|X(j\omega)\right|^2
\frac{1}{\left|a\right|}
```

手工构造 OMML 时用 `mabs([...])`。原因：ASCII `|` 可能产生空 `m:e`，validator 只能事后报错；生成侧必须先防住。其他手写 OMML 边缘公式的元素表：

| 类型 | 示例 | 风格 | OMML |
|---|---|---|---|
| 变量 | x, t, C | italic | `mr("x", italic=True)` |
| 函数名 | e, sin, Re | upright | `mrn("e")` |
| 运算符/数字 | =, +, −, 0 | upright | `mrn("=")` |
| 希腊变量 | ω, θ, φ | italic | `mr("ω", italic=True)` |
| 绝对值 | `\left|C\right|` | delimiter | `mabs([C_])` |
| 上下标 | ω₀, e^{rt} | script | `msub(...)` / `msup(...)` |

## Performance Notes

- **XSLT 只编译一次**：`latex_to_omml.py` 的 `_get_xslt()` 首次编译并缓存 MML2OMML.XSL，后续公式复用同一对象；不要每次转换重新 parse/编译。
- **公式去重缓存**：文档中唯一公式只转换一次，首次构建的子树无 parent 可安全缓存；一旦 append 进段落，复用必须 `deepcopy`。缓存只保留在生成器进程内，不写入 docx。

## Accessibility

`latex_to_omml_alt(latex, alttext)` / `latex_to_omml_fixed_alt` 会把 alttext 写到 `m:oMath` 根节点；Word 不一定原生读取，正文仍应保留可读的线性数学文本。
