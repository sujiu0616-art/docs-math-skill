# Project Scope: 默认值 / Baseline / 本机环境

> 本文件回答一个问题：哪些规则可以直接复用，哪些只是一个项目（baseline）的约定，哪些只是本机工具路径。
> 格式优先级见 `SKILL.md` 的 Format Priority；默认值细节见 `references/docx-style.md`。

## 1. 可迁移默认值（所有新文档、用户未要求时）

这些是从零新建文档时的回退值，全部定义在 `scripts/specs.py`：

| 类别 | 默认值 |
|---|---|
| 正文 | 宋体 + Times New Roman，11pt，行距 1.35 |
| 章节标题 | 黑体，H1 16pt / H2 13pt（加粗）/ H3 12pt，行距 1.15 |
| 大标题 | 22pt 加粗，中文方正小标宋简体，拉丁 Times New Roman |
| 颜色 | H1/H2 标题蓝 `#2E74B5`，H3 深蓝 `#1F4D78`，模板元信息灰 `#595959` |
| 页面 | 8.5 × 11 in，左右 1 in、上下 0.8 in |
| 表格 | 表头底纹 `E8EEF5`、跨页重复、垂直居中；表题在表格下方居中、不加粗 |
| 公式 | 独立公式居中、编号右对齐；行内公式随文不居中；∑/∏ 上下限结构叠排 |
| 校验 | level 1/2/3 见 `references/validator.md` |

这些值只在**没有 baseline、用户也没有格式要求**时使用。不要把它们当作“全局唯一标准”。

## 2. Baseline 示例（只在对应文档/模板中成立）

以下是真实项目中出现过的约定示例，**不是 skill 默认值**：

- 正文用**仿宋/仿宋_GB2312**（公文类排版常见）；
- 正文或标题用**方正小标宋简体**，而不是默认的宋体/黑体组合；
- A4 页面 + 2.1cm 或 2.54cm 页边距；
- 特定的表头底纹色、列宽、编号格式（如“第 1 章”）。

处理规则：

- 有 baseline 时以 baseline 为准（`references/docx-style.md` 的 Baseline Extraction）；
- 只有用户明确要求时，才把上述约定用到新文档；
- **不要把仿宋、小标宋等 baseline 字体写成与“宋体”并列的第二套默认标准**。

## 3. 本机环境示例（只用于工具定位，不是格式）

以下路径/命令只是工具发现示例，**不要写进生成文档或格式规则**：

- Windows 字体目录：`%LOCALAPPDATA%\Microsoft\Windows\Fonts`、HKCU 字体注册项；字体检测需枚举实际字族；
- Office OMML 引擎 `MML2OMML.XSL`：常见 `C:\Program Files\Microsoft Office\root\Office16\...`，可用 `MATHDOC_MML2OMML` 覆盖；
- LibreOffice / Poppler：`specs.find_soffice()` / `find_pdftoppm()`，支持 `MATHDOC_SOFFICE` / `PDFTOPPM` 覆盖；
- 个人经验库：`~/.config/math-doc/user-lessons.md`（`mathdoc_learn.py --path`）。

## 4. 判断顺序

1. 用户明确格式要求？→ 用户要求；
2. 有已有文档/模板/baseline？→ baseline；
3. 从零新建且用户没要求？→ 本文件第 1 节的默认值；
4. 只是运行环境路径？→ 仅用于工具定位，不参与格式。
