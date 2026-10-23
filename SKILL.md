---
name: math-doc
description: Generate and validate mathematical Word (.docx) documents — notes, exercise sets, summaries, reports, proofs, papers — with native editable OMML equations, Chinese typography defaults, formula pre-checks, a three-level validator and render QA. Use when the user asks to produce or format a formula-heavy .docx, or needs Markdown/LaTeX converted into a Word deliverable. Standalone LaTeX/Markdown output formatting is out of scope.
version: 2.10.0
author: user
last_update: 2026-10-23
status: production
---

# math-doc Skill

## Output Contract

- **主交付**：`.docx`，公式必须是 Word 原生 OMML（双击可编辑）。
- **LaTeX / Markdown**：源格式输入或中间产物；用户明确要纯 LaTeX/Markdown 时只输出源文件，并说明不套用 Word 版式规则。
- 本 skill 不定义 LaTeX/Markdown/HTML 的成品排版规范。

## Trigger

Use when the user requests a mathematical Word document, formula formatting/OMML conversion, Markdown/LaTeX → .docx generation, or format checking of a generated math document.

## Decision Priority

1. 用户明确要求
2. 项目/模板/baseline 约束
3. 本 skill 默认规则
4. 通用最佳实践

## Working Mode

- **A. Creation**：从零新建，走完整 pipeline。
- **B. Modification**：先读结构/样式，再改；不重建整篇。
- **C. Analysis**：解释结构/公式，不重生成。
- **D. Debugging**：先定位根因（XML/渲染），再修。
- **E. Research**：先查规范/资料，再动笔。

信息不足且会影响结果时才提问。

## Task Router

- 写证明/讲义/笔记/习题集 → 问是否要 Word；要则走 docx pipeline。
- 改公式 → 只改公式文本时返回 LaTeX/Markdown；要成品或改已有 docx 则走 docx pipeline。
- 检查论文格式 → `scripts/validator.py` 选合适 level。
- 已有模板/baseline → template/baseline wins。

## Pipeline

```text
Markdown / LaTeX source -> parser -> LaTeX formulas
  -> latex_to_omml (single entry; references/omml.md) -> OMML -> .docx
```

公式细节只在 `references/omml.md`；本文件只保留决策规则与索引。

## Format Priority（铁律）

按序判定，命中即止，**禁止串用**：

1. **用户明确要求**：任一项格式被指定，就以用户要求为唯一约束。
2. **从零新建且用户未提要求**：按 `scripts/specs.py` / `references/docx-style.md` 默认格式。
3. **已有文档/模板修改或续写且用户未提要求**：以原格式为基准，默认值只补缺失属性。

禁止：默认格式套已有文档；原文档格式覆盖用户要求；局部要求扩大到全文；同一文档混搭多套格式。

## Validation

- 生成前：`scripts/formula_check.py` 预检全部新公式（0 失败再写生成器）。
- 生成后：`scripts/validator.py --level 1|2|3`；检查项编号与意图见 `references/validator.md`。
- 文档来自 baseline/用户格式时，传 `--style-source baseline|user`；不要用“不跑 level 2”绕过。
- 渲染冒烟可选（`render_check.py` / `render_diff.py`）；无工具时交付说明写“渲染未验证”。

## Learning（安全流程）

- 开始时读取 `~/.config/math-doc/user-lessons.md`（`mathdoc_learn.py --path`）；只应用与本任务直接相关的条目。
- 优先级：当前用户要求 > 项目 baseline/模板 > 内置规则 > user-lessons。个人经验只是提示，不得覆盖前三层。
- 结束时如发现可复用经验：先生成候选并展示给用户；写入/删除必须由用户在自己的终端确认（非 TTY 拒绝）。细节见 `mathdoc_learn.py --help`。
- `references/pitfalls.md` 是内置经验（只读）；个人经验只进 user-lessons.md。

## Failure Handling

- 缺 `latex2mathml` / `MML2OMML.XSL`：报告环境缺失，不改用 Unicode/手写 OMML。
- 字体缺失：检测→回退→交付注明。
- 模板存在：模板优先。
- 公式转换失败：保留源公式并报错，不静默丢弃。
- validator 失败：按编号到 `references/validator.md` 定位后重跑。

## References

- `references/project-scope.md`：默认值/baseline/本机环境分层。
- `references/docx-style.md`：字体、间距、页面、表格、标题与公式对齐、baseline 提取。
- `references/omml.md`：公式转换唯一权威（入口、limits、aligned、绝对值、括号、性能注意）。
- `references/markdown-parser.md`：Markdown 占位解析、跨行加粗、字面 `$`、混排段落。
- `references/validator.md`：检查项编号、来源开关、长文档待办、PDF 字体复核。
- `references/pitfalls.md`：现象→规则→依据（只读）。
- `~/.config/math-doc/user-lessons.md`：个人经验（提示级）。
- `CHANGELOG.md`：历史、决策、已修缺陷。

## Scripts

- `specs.py` 常量与外部工具定位；`latex_to_omml.py` 公式入口；`omml_helpers.py` 手工 OMML。
- `mathdoc_cli.py` 骨架生成 + 样式/编号公式/`set_table_widths`。
- `validator.py` 校验（`--level`、`--style-source`、`--list-checks`）；`publish_report.py` 交付报告。
- `formula_check.py` 预检；`render_check.py` / `render_diff.py` 渲染冒烟。
- `mathdoc_learn.py` 经验预览/确认写入/回滚（详见 `--help`）。

## Equation Numbering

默认正文可见编号 `(1)`、`(2)`，配 center tab + right tab；需要交叉引用时才用 SEQ 域，并提示 Word 需 Ctrl+A F9 刷新。实现见 `references/docx-style.md`。
