# DOCX Style Standard

## Font

- 中文标题：章节标题（Heading 1-3）用黑体，其中二级标题（Heading 2）黑体加粗；大标题（Title、文档首行）用方正小标宋简体。
- 中文正文：宋体。
- 数字、英文：Times New Roman。
- 公式字体：不手动指定，保留兼容性最好的数学字体（Word/WPS 默认，通常为 Cambria Math）；必须显式设置时使用 Times New Roman。
- 字体通过 `doc.styles` 设置一次，不逐 run 写。
- Markdown/HTML 用 CSS 映射同名字体；LaTeX 用 `ctex` 的 CJK 字体映射。

字体检测不能只依赖 `InstalledFontCollection`。检查 `AppData\Local\Microsoft\Windows\Fonts`、注册表字体项、WPF `SystemFontFamilies` 或 `PrivateFontCollection`；只有全部找不到时才回退宋体。

```python
from docx.shared import Pt
from docx.oxml.ns import qn

def configure_styles(doc):
    normal = doc.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal.font.size = Pt(12)
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn('w:eastAsia'), '宋体')

    for lvl, (size, cn_font) in {
        1: (22, '黑体'),
        2: (16, '黑体'),
        3: (14, '黑体'),
    }.items():
        hs = doc.styles[f'Heading {lvl}']
        hs.font.size = Pt(size)
        hs.font.bold = True
        hs.font.name = 'Times New Roman'
        hs.element.rPr.rFonts.set(qn('w:eastAsia'), cn_font)
```

只有语义强调才做 per-run 格式化：粗体、斜体、彩色标签。优先创建 character style，不直接往每个 run 写完整字体属性。

## Spacing

- 非必要不添加空格；先判断空格是否有语义意义。
- 中文与中文、中文与标点之间不加空格。
- 中文与行内公式之间不加空格；需要间距时用排版间距。
- 文本段不允许首尾空格；从 Markdown 提取的 text/bold/italic 片段必须 `.strip()`。
- 公式内不用空格做对齐或视觉留白；`=`、`+`、`-` 两侧不加空格，减号用 U+2212。
- 确需空格时只保留语义需要的：英文单词间、标准数学记号约定、用户明确要求处。

## Page

无 baseline 文档或 baseline 不可读时的回退预设：

- Page: A4，页边距 2.54cm。
- Body: 宋体 + Times New Roman。
- Headings: 黑体 + Times New Roman；H1 16pt、H2 13pt、H3 11pt；标题蓝 `#2E74B5`；Title 大标题 22pt bold black、中文用方正小标宋简体。
- Math: OMML via latex2mathml -> MML2OMML pipeline。

## Table

必做：

- 表头跨页重复：第一行 `w:tblHeader`。
- 表头底纹 `E8EEF5`。
- 所有单元格 `vAlign=center`。
- 表头行 `cantSplit`，表头单元格段落 `keepNext`。
- 单元格边距 top/bottom 80、left/right 120 twips。
- 列宽按内容自适应，但必须同时写 `w:tblGrid/gridCol` 和 `w:tcW`。
- `python-docx` 对 `w:shd` 写入支持不稳定；保存后若检查不到底纹，直接补丁 `word/document.xml`。

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm

def set_table_widths(table, widths_cm):
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    for existing in tbl_pr.findall(qn("w:tblLayout")):
        tbl_pr.remove(existing)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)

    grid = table._tbl.tblGrid
    grid_cols = grid.findall(qn("w:gridCol")) if grid is not None else []
    assert len(grid_cols) == len(widths_cm)
    total_twips = sum(int(col.get(qn("w:w"), 0)) for col in grid_cols)
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(total_twips))
    tbl_w.set(qn("w:type"), "dxa")

    for col, cm in zip(grid_cols, widths_cm):
        col.set(qn("w:w"), str(int(cm * 567)))
        col.set(qn("w:type"), "dxa")

    for row in table.rows:
        for cell, cm in zip(row.cells, widths_cm):
            cell.width = Cm(cm)
```

列宽不要硬编码固定值。应结合单元格文字长度、公式复杂度和可读性估计每列宽度，再缩放到可用页宽；内容列必须写实际内容名，不能只放章节号序列。

## Alignment

- 表头：始终居中。
- 短标签、状态、时间、勾选项：居中，列宽收窄。
- 长描述、要求、疑问、结论、复习要求：左对齐，列宽给足。
- 公式短表（如性质表）：整表居中。
- 混合表：按列判断，不能整表一刀切。

## Baseline Extraction

生成前先打开最相似的已有 docx，记录 Normal/Heading 字体、页边距、表格样式、表头填充/对齐、网格宽度和 OMML 约定。生成后按该 checklist 对比。如果参考 docx 打不开，直接读 `word/document.xml` 和 `word/styles.xml`；仍失败才使用回退预设。
