# Validator

验证与生成分离。生成完 `.docx` 后，对保存的文件做独立校验，不混入生成代码。

## Validation Levels

| Level | 场景 | 检查范围 |
|---|---|---|
| 1 basic | 普通作业/快速输出 | B1-B5 |
| 2 academic | 论文/讲义/报告 | Level 1 + M1/M2 + T1 + S1-S5/T2 |
| 3 publication | 投稿/正式交付 | Level 2 + P1 页面尺寸 + 渲染/PDF 复核 |

## CLI

```bash
python scripts/validator.py path.docx --level 2
python scripts/validator.py path.docx --level 2 --style-source baseline
python scripts/validator.py --list-checks
```

`--style-source` 明确文档格式来源：

- `default`（默认）：执行 S1-S5 字体/主题/标题与 T2 表头样式断言。
- `baseline` / `user`：跳过 S1-S5/T2，仍执行 B1-B5、M1/M2、T1、P1；输出中以 `[note]` 列出被跳过的断言。
- 不要用“不跑 level 2”绕过；检查项编号与含义以 `validator.py` 的 `CHECK_SPECS` 为唯一代码来源。

## Check Items

| 编号 | 含义 | 来源 |
|---|---|---|
| B1 | 存在 OMML 公式 | 所有 |
| B2 | 无空 `m:e` | 所有 |
| B3 | `lim` 使用 `m:limLow`，不是 `m:sSub` | 所有 |
| B4 | 无 Markdown 残留（代码块 Consolas 段落豁免） | 所有 |
| B5 | `w:t` 无首尾空格（代码块豁免） | 所有 |
| M1 | n-ary `limLoc` 与 `specs.NARY_LIM_LOC` 一致 | 所有 |
| M2 | 编号公式的 ∑/∏ 已结构化，无 `m:nary` | 所有 |
| S1 | Normal 中英文字体符合默认 | default |
| S2 | Heading 字体、H2 加粗符合默认 | default |
| S3 | Title 字体符合默认 | default |
| S4 | 使用中的样式与正文 run 无 `*Theme` 属性 | default |
| S5 | 大标题/标题块居中 | default |
| T1 | `tblGrid/gridCol` 数量与宽度有效 | 所有 |
| T2 | 表头 `tblHeader/cantSplit/shd/vAlign` 符合默认 | default |
| P1 | 页面尺寸有效（level 3） | level 3 |

## Long Document（待办，当前未自动化）

以下规则保留，但 `validator.py` 尚未实现，不得在交付说明里声称“已校验”；需要时用渲染/人工或后续脚本检查：

- **L1 页数**：渲染 PDF 后核对页数，排查异常空页/断页；检查分页符、表格宽度、图片尺寸。
- **L2 跨页表头**：长表格 `tblHeader` 跨页重复、表头行 `cantSplit`；渲染检查跨页处是否孤立表头或行内容被截断。
- **L3 标题孤行**：Heading 段落应 `keep_with_next`；渲染检查页尾不能只留标题。
- 建议阈值：超过 30 页或 10 张以上表格时启用；具体阈值可由项目定义。

## Render / PDF

```bash
soffice --headless --convert-to pdf --outdir out input.docx
python scripts/render_check.py out/input.docx 关键词1 关键词2
python scripts/render_diff.py before.pdf after.pdf --out out/
```

工具定位由 `specs.find_soffice()` / `find_pdftoppm()` 处理，可用 `MATHDOC_SOFFICE` / `PDFTOPPM` 覆盖；Windows 上必须指向原生 `pdftoppm.exe`，不要用 `.cmd`。只改公式时优先裁剪公式区域再 diff。

### 字体最终验证（PDF 内嵌字体名）

XML 断言通过 ≠ 渲染字体正确。转 PDF 后读内嵌字体名，例如：

- `FZXBSJW--GB1-0` = 方正小标宋（大标题）
- `SimHei` = 黑体（章节标题）
- `SimSun` = 宋体（中文正文）
- `TimesNewRomanPSMT` = Times New Roman（拉丁/数字）

字体名带 `+` 前缀是 PDF 子集标记，属正常；缺字体会出现替代字体（如 `LiberationSerif`、`NotoSerifSC`）。必要时 300dpi 放大看字形，不能只信 validator 的 OK。

## Empty m:e 排查

B2 报错时先查两类已知来源，规则分别见 `references/omml.md`：

1. 裸 `|...|` 绝对值 → 生成侧写 `\left|...\right|`。
2. `\left(-x\right)` 这类定界符内以正负号开头 → 写 `\left({-}x\right)`。
