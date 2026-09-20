---
name: math-doc
description: Generate mathematical Word documents for any scenario — notes, exercise sets, summaries, reports, proofs, papers — in .docx, LaTeX, or Markdown. Covers OMML rendering via python-docx, Chinese typography and font rules, Markdown-to-docx conversion, formula formatting, equation numbering, and cross-references. Use when the user asks to produce or format any mathematical document or formula-heavy output.
version: 2.8.0
author: user
last_update: 2026-09-20
status: production
---

# math-doc Skill

## Purpose

Generate professional mathematical documents for any scenario — lecture notes, exercise sets, summaries, proofs, reports, papers, or anything formula-heavy. Output can be .docx, LaTeX, or Markdown.

## Trigger

Use this skill when:

- user requests any mathematical document (notes, exercises, summaries, proofs, reports)
- user requests a formula-heavy Word document
- user requests formula formatting or OMML conversion
- user requests Markdown/LaTeX to .docx generation
- user requests checking the format of a generated math document

## Decision Priority

1. User explicit requirement
2. Existing project/file/template constraints
3. Domain skill rules
4. General best practice

## Working Mode

Classify the request:

- A. Creation: full pipeline, build from scratch.
- B. Modification: inspect structure first, then modify.
- C. Analysis: explain document structure or formula, do not regenerate.
- D. Debugging: inspect generated file, find root cause, then fix.
- E. Research: gather references or conventions before output.

Ask only when missing information affects the result. Otherwise use reasonable defaults.

## Task Router

- `帮我写证明`、`写讲义`、`整理笔记`、`出习题集` -> math-doc -> ask `需要Word吗？`; if yes, use docx pipeline.
- `帮我改公式` -> Formula mode: return LaTeX/Markdown unless user asks for .docx.
- `检查论文格式` -> Validator mode: run `scripts/validator.py` with an appropriate level.
- 其他任何数学文档请求 -> 同一流水线，按 Working Mode 分类处理。
- Existing document with a template or baseline -> template/baseline wins.

## Pipeline

```text
Markdown -> Parser -> LaTeX extraction -> MathML -> OMML -> DOCX
```

For .docx output, always prefer `latex2mathml -> MML2OMML.XSL -> OMML` over manual OMML construction. Manual OMML is only for edge cases documented in `references/omml.md`.

## Mandatory Rules

### Formula

- Use `latex2mathml -> OMML` for all math.
- **单一入口 `latex_to_omml(latex, alttext=None, fix_limits=True)`**：默认已完成 aligned 改写、n-ary 限位与 naryPr 归一化。不要绕过它直接调 `latex2mathml.converter.convert`，也不要手写 limLoc 修补。
- Never use Unicode composed subscripts/superscripts, plain text formulas, upright variables, or `|x|` as plain text for absolute value.
- LaTeX 绝对值/范数必须写 `\left|...\right|`；独立公式里的裸 `|X|^2` 会被 latex2mathml 解析成空 `m:e`。手动构造 OMML 时用 `mabs` 分隔符结构。
- 大算符限位：`∫` 用 `limLoc="subSup"`，`∑`/`∏` 用 `limLoc="undOvr"`（规则表在 `specs.NARY_LIM_LOC`，validator 用同一份断言）；`lim` 用 `m:limLow`，不用 `m:sSub`。
- 限位的已知边界与结构级改法、`\underbrace` 与 `mstyle` 的处理，见 `references/omml.md`。

### Styles

以下字体/排版规则均为**用户未要求时的默认值**：用户明确指定格式（字体、字号、颜色、间距、对齐等）时，以用户要求为准，默认规则不得覆盖用户格式。

- 字体名以 `scripts/specs.py` 的 `FONT_*` 为单一真相源：正文宋体、标题黑体（Heading 2 必须加粗）、大标题方正小标宋简体、拉丁 Times New Roman。样式级必须显式设 `eastAsia`，只设 run 字体不足以通过 validator。
- 通过 `doc.styles` 设置一次，不逐 run 写字体。
- 表格标题（表N xxx）：表格**下方**居中、常规字体不加粗、不用黑体，space_before 4 / space_after 6。
- 字号、页边距、表格几何、列宽算法、对齐规则见 `references/docx-style.md`。
- No decorative literal spaces. Strip text segments, no spaces around `=`/`+`/`-`; minus sign U+2212.

### Validation

- BEFORE generation: batch-verify all formulas new to this document with `scripts/formula_check.py` (0 failures before writing the generator).
- After generation, run `scripts/validator.py` on the saved `.docx`.
- Level 1: basic open/equation/markdown residue checks（含代码块豁免：Consolas 段落里的 `**`/`$` 不判残留）。
- Level 2: academic font/table checks. Level 3: publication checks plus page size.
- **level 2 的字体断言以 `specs.py` 默认值为准**。若项目以既有 docx 作样式基线且基线另有约定，以基线为准，此时该断言不适用 —— 详见 `references/validator.md`。
- LibreOffice/Poppler unavailable: explicitly state `渲染未验证`。

### Rendering

外部工具按「环境变量 → PATH → 常见安装路径」定位（实现在 `specs.find_soffice` / `specs.find_pdftoppm`），不要写死本机路径：

- LibreOffice：`MATHDOC_SOFFICE` 覆盖，否则查 `soffice` / 常见安装目录。
- poppler：`PDFTOPPM` 覆盖，否则查 PATH。Windows 上**必须指向原生 `pdftoppm.exe`**，不要用 `.cmd` 包装器（本环境会报 `The system cannot find the path specified`）。

```bash
soffice --headless --convert-to pdf --outdir out input.docx           # 渲染 PDF
python scripts/render_check.py out/input.docx 关键词1 关键词2           # 文本冒烟
python scripts/render_diff.py before.pdf after.pdf --out out/           # 像素 diff（--out 落盘差异图）
```

`render_check` 的 probe 必须与文档措辞**逐字节一致**（含空格）；中间 PDF 默认写临时目录，需要保留时加 `--keep-pdf`。

## Auto-Learning（动态 skill）

Skill 不是静态的：每次任务自动读经验、自动沉淀新经验，用户无需手动追加。

- **任务开始前（自动读取）**：读取 `~/.config/math-doc/user-lessons.md`（路径可用 `python scripts/mathdoc_learn.py --path` 确认）。该文件存个人经验库（用户格式要求、踩坑、验证过的新语法），生成时必须遵循其中的条目，优先级：用户明确要求 > user-lessons 条目 > 内置默认规则。
- **任务完成后（自动追加）**：若本次任务产生了新经验——踩坑（含根因/修复）、用户明确给出的格式要求、新验证通过的 LaTeX 语法——用 `mathdoc_learn.py --add` 自动追加，无需用户手动操作：

  ```bash
  python scripts/mathdoc_learn.py --add "教训一句话" --root-cause "根因" --fix "修复" --verify "验证" --task "项目名"
  ```

- 追加前用 `--list` 检查去重；经验文件在 skill 目录之外，`sync_install.sh` 不会覆盖；`references/lessons.md` 保持只读（内置通用经验），个人经验一律进 user-lessons.md。

## Failure Handling

- `latex2mathml` or `MML2OMML.XSL` unavailable: report environment missing; do not silently switch to Unicode or manual OMML.
- Font missing: detect first, fallback second, note fallback in delivery.
- Template exists: template wins.
- Formula conversion fails: preserve the source formula and report the error instead of dropping it.
- Validator reports `empty m:e`:优先检查含裸 `|...|` 的公式，改为 `\left|...\right|` 后重新生成。

## References

Load the relevant reference before generating:

- `references/docx-style.md`: fonts, headings, spacing, page, tables, baseline extraction.
- `references/omml.md`: latex2mathml -> XSLT -> OMML, lim/underbrace handling, manual OMML edge cases, accessibility.
- `references/markdown-parser.md`: Markdown placeholder parsing, bold across `$...$`, literal `$`, spacing, mixed paragraphs.
- `references/validator.md`: validation levels, table grid checks, PDF rendering.
- `references/performance.md`: formula cache, XSLT single-pass, global styles, deferred attach, batch validation.
- `references/lessons.md`: 批量章节文档生成实战（公式预验证、渲染冒烟 probes、GBK 假警报、模板继承、逐章流水线）。
- `~/.config/math-doc/user-lessons.md`: 个人经验库，任务开始前自动读取、完成后自动追加（见 Auto-Learning）。
- `CHANGELOG.md`: version history and past failures.

## Scripts

- `scripts/specs.py`: 共享常量与外部工具定位（`NARY_LIM_LOC`、`FONT_*`、`find_soffice`、`find_pdftoppm`）。零依赖叶子模块，生成侧与校验侧共用。
- `scripts/latex_to_omml.py`: LaTeX -> OMML 管线。入口 `latex_to_omml`，旧名 `latex_to_omml_alt/_fixed/_fixed_alt` 保留为等价别名。
- `scripts/omml_helpers.py`: 手工 OMML builder（`mpara_mix`、`mnary`、`mlim`、`mabs` 等），供 latex2mathml 表达不了的边缘公式。
- `scripts/mathdoc_cli.py`: `--template proof|notes|derivation` skeleton generator.
- `scripts/validator.py`: post-generation .docx validator with `--level 1|2|3`.
- `scripts/render_diff.py`: pixel diff between rendered PDFs（`--out` 写差异图）。
- `scripts/formula_check.py`: batch-verify LaTeX formulas against latex_to_omml before generating.
- `scripts/render_check.py`: lightweight render smoke test (LibreOffice -> PDF -> text probes).
- `scripts/publish_report.py`: delivery report — validate a docx and write `validation-report.md` (equation count, checks, OMML engine), producing the source/result/report triplet.
- `scripts/mathdoc_learn.py`: 动态 skill 经验管理 — `--add` 自动追加教训到个人经验库（自动带日期与问题/根因/修复/验证格式）、`--list` 查看、`--path` 定位。

```bash
python scripts/mathdoc_cli.py --template proof --title 证明 --output proof.docx
python scripts/validator.py proof.docx --level 2
python scripts/formula_check.py --file new_formulas.txt
python scripts/render_check.py doc.docx 定理 定义 性质
python scripts/mathdoc_learn.py --add "本次教训" --root-cause "根因" --fix "修复" --verify "验证"
python -m pytest tests/ -v
```

## Equation Numbering

Default: plain visible text `(1)`, `(2)`, `(3)` with a right tab stop. Use SEQ fields only when the document needs cross-references, and warn that Word requires Ctrl+A F9 to refresh.
