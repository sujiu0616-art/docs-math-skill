# math-doc Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

把公式密集的 Markdown / LaTeX 生成 **Word 原生 OMML** 文档：公式双击可编辑，中文排版、三级校验、渲染冒烟，整条流水线可执行、可验证。

只交付 Word/.docx；LaTeX/Markdown 作为输入源或中间产物，不套用 Word 版式规则。

## 特性

- **原生 OMML**：`latex2mathml → MML2OMML.XSL → OMML`，单入口 `latex_to_omml`；裸 `|x|` 等危险写法直接报错。
- **生成前预检**：`formula_check.py` 批量验证全部 LaTeX 公式可转 OMML。
- **生成后校验**：`validator.py --level 1|2|3` 对公式、字体、表格、分页做可执行断言。
- **渲染验证**：`render_check.py` 文本冒烟，`render_diff.py` 像素 diff。
- **交付报告**：`publish_report.py` 输出公式数、校验结论与 OMML 引擎来源。
- **经验沉淀（安全）**：`mathdoc_learn.py` 默认只生成候选条目，用户确认后才写入 `~/.config/math-doc/user-lessons.md`，可用 ID 回滚。

## 安装

把本目录放进 agent 的 skills 目录（如 `~/.claude/skills/`、`~/.codex/skills/`、`~/.agents/skills/`），然后安装依赖：

```bash
pip install -r requirements.txt
```

依赖：Python（`latex2mathml`、`python-docx`、`lxml`、`pypdf`、`Pillow`）；Microsoft Word + `MML2OMML.XSL`（或设 `MATHDOC_MML2OMML`）；可选 LibreOffice / Poppler 用于渲染验证。

## 用法

```bash
python scripts/mathdoc_cli.py --template proof --title 证明 --output proof.docx
python scripts/formula_check.py --file new_formulas.txt
python scripts/validator.py proof.docx --level 2
python scripts/render_check.py proof.docx 关键词1 关键词2
python scripts/publish_report.py proof.docx --level 2 --report validation-report.md
```

多 agent 安装可先 `bash sync_install.sh --dry-run` 预览，再去掉 `--dry-run` 同步。

## 目录

```text
SKILL.md      skill 入口：用途、管线、强制规则、失败处理
references/   样式规范、OMML 细节、markdown 解析、验证、性能、实战经验
scripts/      生成 / 校验 / 渲染 / 报告 / 经验管理
```

## 许可

MIT License，见 [LICENSE](LICENSE)。
