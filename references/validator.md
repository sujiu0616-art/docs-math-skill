# Validator

验证与生成分离。生成完 `.docx` 后，对保存的文件做独立校验，不混入生成代码。

## Validation Levels

| Level | 场景 | 检查 |
|---|---|---|
| 1 basic | 普通作业/快速输出 | 文档能打开、存在公式、无空 `m:e`、无 Markdown 残留、无首尾空格、表格结构有效 |
| 2 academic | 论文/讲义/报告 | Level 1 + 字体、表格网格、表头、垂直居中、引用字段存在 |
| 3 publication | 投稿/正式交付 | Level 2 + 渲染 PDF 视觉检查、页边距、公式编号、跨页表头、渲染 diff |

## Long Document Validation

长文档在 Level 2 基础上追加以下检查：

- 页数检查：渲染 PDF 后核对页数，确认没有异常空页或断页；页数异常时检查分页符、表格宽度和图片尺寸。
- 表格跨页：长表格必须保留 `tblHeader` 跨页重复表头，表头行 `cantSplit`，并渲染检查跨页处是否出现孤立表头或行内容被切断。
- 标题孤行：Heading 段落必须 `keep_with_next`；渲染检查页尾不能只留下标题，正文应随标题进入下一页。

长文档阈值可按项目定义，建议文档超过 30 页、或包含 10 张以上表格时启用。

```python
from docx import Document

doc = Document("long.docx")
for p in doc.paragraphs:
    if p.style.name.startswith("Heading") and not p.paragraph_format.keep_with_next:
        print("heading may orphan:", p.text[:40])
```

## CLI

```bash
python scripts/validator.py path.docx --level 2
python scripts/render_diff.py before.pdf after.pdf --dpi 150 --threshold 0.02
```

## Core Checks

- `body.xpath('.//m:e[not(node())]')` 必须为空。
- 积分 `limLoc=subSup`；求和/连乘 `limLoc=undOvr`；`lim` 必须是 `m:limLow`。
- 文本 run 中不能有 `**`；CJK 上下文中出现可疑 `$` 要报错。
- `w:t` 不能有首尾空格。
- Normal eastAsia 必须是 `宋体`；Heading eastAsia 是 `黑体`；Latin/digits 是 Times New Roman。
- `w:tblGrid/gridCol` 数量和宽度必须匹配；只设 `cell.width` 不够。
- 表头行有 `tblHeader`、`cantSplit`；表头单元格有 `shd E8EEF5`；所有单元格 `vAlign=center`。
- LibreOffice 可用时转 PDF 检查；没有渲染工具时明确说明“渲染未验证”。

`empty m:e` 最常见来源是裸 `|...|` 绝对值公式，例如 `|X(jω)|²`。先查这类公式并改成 `\left|...\right|`，再重新生成和校验。

Heading 样式必须显式存在 `w:rPr/w:rFonts` 且 `eastAsia=黑体`；只给标题 run 设黑体但样式本身缺失时仍会失败。

## Table Grid Check

Word 的有效列布局来自 `w:tblGrid/w:gridCol`。LibreOffice 转换可能仍看起来正常，但隐藏 mismatch；validator 必须检查保存后的 docx，而不是只检查内存中的 cell width。

```python
from docx.oxml.ns import qn

def check_table_grid(doc, expected_per_table):
    for table, expected in zip(doc.tables, expected_per_table):
        grid = table._tbl.tblGrid
        cols = grid.findall(qn("w:gridCol")) if grid is not None else []
        actual = [int(c.get(qn("w:w"), 0)) for c in cols]
        assert len(actual) == len(table.columns), "tblGrid column count mismatch"
        assert all(w > 0 for w in actual), "tblGrid contains zero-width columns"
        expected = [int(cm * 567) for cm in expected]
        assert actual == expected, f"tblGrid mismatch: {actual} != {expected}"
```

## PDF Rendering

```bash
soffice --headless --convert-to pdf --outdir out input.docx
```

Windows 下不要默认使用 `pdftoppm`，因为它可能解析到 `.cmd` 包装器并报“找不到路径”。优先直接调用原生 exe：

```powershell
# 优先解析到原生 exe（跳过 .cmd 包装器），或设置 $env:PDFTOPPM 指向原生 exe
$exe = $env:PDFTOPPM
if (-not $exe) { $exe = (Get-Command pdftoppm -ErrorAction SilentlyContinue).Source }
if ($exe -and -not $exe.EndsWith('.cmd')) {
  & $exe -png -r 150 'out\input.pdf' 'out\page'
} else {
  pdftoppm -png -r 150 'out\input.pdf' 'out\page'
}
Get-ChildItem 'out\page-*.png'
```

如果只改公式，优先裁剪公式所在区域再 diff，避免正文排版噪声影响判断。
