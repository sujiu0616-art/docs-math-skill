# math-doc Skill

[![CI](https://github.com/sujiu0616-art/docs-math-skill/actions/workflows/test.yml/badge.svg)](https://github.com/sujiu0616-art/docs-math-skill/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

不是又一个 Markdown → DOCX 转换器，而是一条 **公式预检 → 原生 OMML → 中文排版 → 三级校验 → 渲染对比** 的数学文档质量流水线。

## 它能生成什么

讲义、证明、习题集、论文——任何公式密集的 Word 文档。公式是 **Word 原生 OMML**：双击可编辑，不是 Unicode 近似，不是截图。

[examples/](examples/README.md) 里已提交 4 份真实产物（讲义、证明、习题集、论文），打开即用。

## 特性

- **强制原生 OMML**：公式是 Word 可双击编辑的原生方程，不是 Unicode 近似或截图；裸 `\|x\|` 等危险语法直接报错，不会静默产出坏公式
- **生成前公式预检**：`formula_check.py` 批量验证全部 LaTeX 公式可转 OMML，0 失败再动笔
- **生成后独立校验**：`validator.py --level 1/2/3` 对公式、字体、表格、分页做可执行断言
- **渲染验证**：像素 diff（`render_diff.py`）或轻量文本冒烟（`render_check.py`）
- **回归测试**：22 个生产公式、91 个用例，CI 自动跑
- **交付报告**：`publish_report.py` 输出公式数、校验项、引擎来源，可证明公式是原生 OMML

## 怎么验证（每条命令都能跑）

```bash
python scripts/formula_check.py --file new_formulas.txt     # 生成前：公式全部可转 OMML
python scripts/validator.py result.docx --level 2           # 生成后：公式/字体/表格/分页断言
python scripts/render_check.py result.docx 关键词1 关键词2   # 渲染冒烟（LibreOffice → PDF → 文本 probe）
python scripts/publish_report.py result.docx --level 2 \
    --report validation-report.md                           # 交付报告：公式数 + 校验项 + 引擎来源
```

`publish_report.py` 产出「source / result / report」三件套，收件人可以凭报告核实公式是原生 OMML。示例报告：[examples/reports/validation-report.md](examples/reports/validation-report.md)。

## 安装

复制 `math-doc` 文件夹到你的 agent 的 skills 目录，并安装依赖：

```bash
pip install -r math-doc/requirements.txt
```

常见 skills 目录（按你的 agent 而定）：

| 目录 | 通常对应 |
|---|---|
| `~/.claude/skills/` | Claude Code |
| `~/.codex/skills/` | Codex |
| `~/.zcode/skills/` | ZCode |
| `~/.cursor/skills/` 等 | 支持 skills 目录的其他 agent |

## 依赖

- Python：`latex2mathml`、`python-docx`、`lxml`、`pypdf`、`Pillow`（见 `requirements.txt`）
- Microsoft Word 及 `MML2OMML.XSL`（Office 16）——或设 `MATHDOC_MML2OMML` 指向 XSL 文件
- LibreOffice 用于 PDF 渲染（`MATHDOC_SOFFICE` 可覆盖路径）
- Poppler `pdftoppm` 用于像素 diff（`PDFTOPPM` 可指向原生 exe）

无 Office/LibreOffice 时：`validator.py` 的 XML 断言照常工作，渲染步骤显式声明「渲染未验证」即可。

## 布局

```
SKILL.md            skill 入口：用途、管线、强制规则、失败处理
references/         样式规范、OMML 细节、markdown 解析、验证、性能、实战经验
scripts/            latex_to_omml / omml_helpers / mathdoc_cli / validator /
                    formula_check / render_check / render_diff / publish_report
tests/              回归测试：22 个生产公式 × 91 用例 + 无 Office 可跑的 MathML 测试
examples/           4 份样例文档 + 复现脚本 + 交付报告示例
```

## 许可

MIT License，见 [LICENSE](LICENSE)。
