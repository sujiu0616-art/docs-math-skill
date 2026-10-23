# Project Scope: 默认值 / Baseline / 本机环境

> 本文件回答：哪些规则可直接复用，哪些只是 baseline 约定，哪些只是本机工具路径。
> 格式优先级见 `SKILL.md`；默认值语义见 `references/docx-style.md`，具体数值只在 `scripts/specs.py`。

## 1. 可迁移默认值（所有新文档、用户未要求时）

从零新建、没有 baseline 时使用 `scripts/specs.py` 中的常量；本文不重复数值：

| 类别 | 权威常量 |
|---|---|
| 正文 | `FONT_BODY_CN` / `FONT_LATIN` / `BODY_SIZE_PT` / `BODY_LINE_SPACING` |
| 章节标题 | `FONT_HEADING_CN` / `HEADING_SIZES_PT` / `HEADING_LINE_SPACING` / `COLOR_TITLE_BLUE` / `COLOR_DARK_BLUE` |
| 大标题 | `FONT_TITLE_CN` / `TITLE_SIZE_PT` |
| 元信息 | `META_SIZE_PT` / `COLOR_GRAY` |
| 页面 | `PAGE_WIDTH_IN` / `PAGE_HEIGHT_IN` / `MARGIN_*` |
| 表格 | `TABLE_HEADER_FILL`（其余表格规则见 docx-style） |
| 公式/编号 | 见 `omml.md` / `docx-style.md` |

这些值只在**没有 baseline、用户也没有格式要求**时使用。不要把它们当“全局唯一标准”。

## 2. Baseline 示例（只在对应文档/模板中成立）

以下是真实项目中出现过的约定示例，**不是 skill 默认值**：

- 正文用**仿宋/仿宋_GB2312**（公文类排版常见）；
- 正文或标题用**方正小标宋简体**，而不是默认宋体/黑体组合；
- A4 页面 + 2.1cm 或 2.54cm 页边距；
- 特定表头底纹色、列宽、编号格式（如“第 1 章”）。

处理规则：

- 有 baseline 时以 baseline 为准（见 `references/docx-style.md` 的 Baseline Extraction）；
- 只有用户明确要求时，才把上述约定用到新文档；
- 不要把仿宋、小标宋等 baseline 字体写成与“宋体”并列的第二套默认标准。

## 3. 本机环境示例（只用于工具定位，不是格式）

以下路径/命令只是工具发现示例，**不要写进生成文档或格式规则**：

- Windows 字体检测：`%LOCALAPPDATA%\Microsoft\Windows\Fonts`、HKCU 字体注册项、WPF `SystemFontFamilies`、`PrivateFontCollection`；需枚举实际字族，不能只依赖 `InstalledFontCollection`；
- Office OMML 引擎 `MML2OMML.XSL`：常见 Office 安装目录下的 `root/OfficeXX/MML2OMML.XSL`，可用 `MATHDOC_MML2OMML` 覆盖；
- LibreOffice / Poppler：`specs.find_soffice()` / `find_pdftoppm()`，支持 `MATHDOC_SOFFICE` / `PDFTOPPM` 覆盖；
- 个人经验库：`~/.config/math-doc/user-lessons.md`（`mathdoc_learn.py --path`）。

## 4. 判断顺序

1. 用户明确格式要求？→ 用户要求；
2. 有已有文档/模板/baseline？→ baseline；
3. 从零新建且用户没要求？→ 第 1 节的默认常量；
4. 只是运行环境路径？→ 仅用于工具定位，不参与格式。
