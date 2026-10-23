---
name: math-doc
description: Generate and validate mathematical Word (.docx) documents — notes, exercise sets, summaries, reports, proofs, papers — with native editable OMML equations, Chinese typography defaults, formula pre-checks, a three-level validator and render QA. Use when the user asks to produce or format a formula-heavy .docx, or needs Markdown/LaTeX converted into a Word deliverable. Standalone LaTeX/Markdown output formatting is out of scope.
version: 2.9.1
author: user
last_update: 2026-10-23
status: production
---

# math-doc Skill

## Output Contract

- **主交付**：`.docx`，公式必须是 Word 原生 OMML（双击可编辑）。
- **LaTeX / Markdown**：源格式输入或中间产物。用户明确要纯 LaTeX/Markdown 时，只输出源文件，并说明这是源格式、不套用 Word 版式规则。
- 本 skill **不定义** LaTeX/Markdown/HTML 的成品排版规范。
- 用户要求 / 项目 baseline 的格式优先级高于 skill 默认值；默认值只用于从零新建且用户未提格式要求的文档（细则见 `references/docx-style.md`、`references/project-scope.md`）。

## Trigger

Use this skill when:

- user requests a mathematical Word document (notes, exercises, summaries, proofs, reports, papers)
- user requests formula formatting or native OMML conversion
- user requests Markdown/LaTeX → .docx generation
- user requests checking the format of a generated math document

## Decision Priority

1. 用户明确要求
2. 项目/模板/baseline 约束
3. 本 skill 默认规则
4. 通用最佳实践

## Working Mode

- **A. Creation**：从零新建，走完整 pipeline。
- **B. Modification**：先读结构/样式，再改；不重建整篇文档。
- **C. Analysis**：解释结构或公式，不重生成。
- **D. Debugging**：先定位根因（XML/渲染），再修。
- **E. Research**：先查规范/资料，再动笔。

Ask only when missing information changes the result.

## Task Router

- 写证明/讲义/笔记/习题集 → 问是否要 Word；要则走 docx pipeline。
- 改公式 → 只改公式文本时返回 LaTeX/Markdown；要成品或改已有 docx 则走 docx pipeline。
- 检查论文格式 → Validator 模式：`scripts/validator.py` 选合适 level。
- 其他数学文档请求 → 同一 pipeline，按 Working Mode 分类。
- 已有模板/baseline → template/baseline wins。

## Pipeline

```text
Markdown / LaTeX source
  -> parser (references/markdown-parser.md)
  -> LaTeX formulas
  -> latex_to_omml (single entry; references/omml.md)
  -> OMML
  -> .docx (python-docx)
```

公式转换细节（aligned、n-ary、绝对值、主题字体、`stack_limits`、括号配对）全部在 `references/omml.md`；本文件只保留决策规则与索引。

## Format Priority（铁律）

按序判定，命中即止，**禁止串用**：

1. **用户明确要求**：字体、字号、颜色、间距、对齐、页边距、表格/编号样式等任一项被指定，就以用户要求为唯一约束；默认值与文档原有格式都不得覆盖。
2. **从零新建且用户未提格式要求**：按本 skill 默认格式（`scripts/specs.py` / `references/docx-style.md`）。
3. **基于已有文档/模板修改或续写且用户未提要求**：以该文档**原有格式**为基准；默认值只补原文缺失或未定义的属性，不批量覆盖。

禁止：把默认格式套到已有文档；用原文档格式覆盖用户要求；用户只要求局部时扩大到全文；同一文档混搭多套格式。

## Defaults（索引，不是规则全文）

- 字体/字号/行距/颜色/页边距/表格/标题与公式对齐：`references/docx-style.md`；常量集中在 `scripts/specs.py`。
- 可迁移默认值 vs 某个 baseline 的约定 vs 本机环境路径：`references/project-scope.md`。
- 新建默认摘要：正文宋体 11pt；标题黑体 16/13/12pt；大标题方正小标宋简体 22pt；Latin Times New Roman。具体取值以 `specs.py` 为准。
- 禁止：Unicode/纯文本公式、用空格凑格式、把默认格式套到已有文档。

## Validation

- **生成前**：`scripts/formula_check.py` 预检全部新公式（0 失败再写生成器）。
- **生成后**：`scripts/validator.py --level 1|2|3`；level 2 默认按 skill 默认格式断言字体/主题/标题/表头。若文档来自 baseline/用户格式，必须显式传 `--style-source baseline|user`，validator 会跳过默认样式断言、保留公式与表格网格校验（不要用“手动不跑 level 2”来绕过）。
- **渲染冒烟（可选）**：LibreOffice + `render_check.py` / `render_diff.py`；无渲染工具时在交付里明确写“渲染未验证”。
- 交付前自查：公式为原生 OMML 可编辑、无空 `m:e`、编号对齐、无 markdown 残留。

## Learning（安全流程）

- **开始时**：读取 `~/.config/math-doc/user-lessons.md`（`mathdoc_learn.py --path` 确认位置）；只应用与当前任务直接相关的条目。
- **优先级**：当前用户要求 > 项目 baseline/模板 > 内置规则 > user-lessons（历史经验只作提示，不得覆盖前三层）。
- **结束时**：若发现可复用经验，先生成候选条目（含来源/日期/任务），**展示给用户确认，不得静默写入**：
  - 预览（不写文件，模型/非交互环境只能做到这一步）：`python scripts/mathdoc_learn.py --add "教训" --root-cause "根因" --fix "修复" --verify "验证" --task "任务"`
  - 写入必须由用户在自己的交互式终端运行同一命令并加 `--yes`，再输入 `y` 确认；脚本检测到非 TTY 会拒绝（模型不能代写）。
  - 条目自动带 ID/日期/来源；回滚 `--remove <ID>`（同样需要用户终端确认）。
- `references/lessons.md` 保持只读（内置通用经验）；个人经验只进 user-lessons.md。

## Failure Handling

- 缺 `latex2mathml` / `MML2OMML.XSL`：报告环境缺失，不改用 Unicode/手写 OMML。
- 字体缺失：先检测，再回退，并在交付中注明回退字体。
- 存在模板：模板优先。
- 公式转换失败：保留源公式并报告错误，不静默丢弃。
- validator 报 `empty m:e` 等：按 `references/validator.md` 修复后重跑。

## References

- `references/project-scope.md`: 可迁移默认值 / baseline 示例 / 本机环境，避免把单项目约定当默认值。
- `references/docx-style.md`: 字体、标题、间距、页面、表格、baseline 提取、标题与公式对齐（含编号独立公式完整示例）。
- `references/omml.md`: latex2mathml → XSLT → OMML、limits、aligned、绝对值、主题字体、括号/撇号、空 m:e。
- `references/markdown-parser.md`: Markdown 占位解析、跨行加粗、字面 `$`、混排段落。
- `references/validator.md`: 校验层级、表格网格、PDF/字体验证。
- `references/performance.md`: 公式缓存、XSLT 单次编译、全局样式、批量校验。
- `references/lessons.md`: 内置实战经验（只读）。
- `~/.config/math-doc/user-lessons.md`: 个人经验库（读取 + 经用户确认后追加）。
- `CHANGELOG.md`: 版本历史与已修缺陷。

## Scripts

- `scripts/specs.py`: 共享常量与外部工具定位（`NARY_LIM_LOC`、`FONT_*`、`find_soffice`、`find_pdftoppm`）。
- `scripts/latex_to_omml.py`: LaTeX → OMML 单一入口（全名/旧别名兼容）。
- `scripts/omml_helpers.py`: 手工 OMML builder（边缘公式）。
- `scripts/mathdoc_cli.py`: `--template proof|notes|derivation` 骨架生成器。
- `scripts/validator.py`: `--level 1|2|3` 校验。
- `scripts/formula_check.py`: 生成前批量公式预检。
- `scripts/render_check.py`: 文本冒烟；`scripts/render_diff.py`: 像素 diff。
- `scripts/publish_report.py`: 交付报告（公式数/校验项/引擎来源）。
- `scripts/mathdoc_learn.py`: 经验候选预览（默认不写）、仅交互式终端可 `--yes` 写入、`--list`、`--remove <ID>`（TTY）、`--path`。

```bash
python scripts/mathdoc_cli.py --template proof --title 证明 --output proof.docx
python scripts/validator.py proof.docx --level 2
python scripts/formula_check.py --file new_formulas.txt
python scripts/render_check.py doc.docx 定理 定义 性质
```

## Equation Numbering

默认使用正文可见编号 `(1)`、`(2)`，配 center tab + right tab；不要默认用 SEQ 域，只有需要交叉引用时才用，并提示 Word 需 Ctrl+A F9 刷新。完整实现见 `references/docx-style.md` 的“编号独立公式完整示例”。
