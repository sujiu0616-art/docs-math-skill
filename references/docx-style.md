# DOCX Style Standard

> **格式优先级（与 `SKILL.md` 一致，铁律）**
> 1. 用户明确要求 → 以用户为唯一约束；
> 2. 从零新建文档且用户未提要求 → 本文默认值；
> 3. 基于已有文档且用户未提要求 → 以该文档原有格式为基准（baseline 优先），本文默认值只补缺失属性。
>
> 任何情况下不得覆盖用户明确要求；也不得用本文默认值覆盖已有文档格式。禁止串用。

## Font

- 中文标题：章节标题（Heading 1-3）用黑体，其中二级标题（Heading 2）黑体加粗；大标题（Title、文档首行）用方正小标宋简体。
- 中文正文：宋体。
- 数字、英文：Times New Roman。
- 公式字体：不手动指定，保留兼容性最好的数学字体（Word/WPS 默认，通常为 Cambria Math）；必须显式设置时使用 Times New Roman。
- 项目 baseline 可能使用仿宋、方正小标宋或其它中文字体：那是 baseline 的约定，**不是本 skill 的默认标准**；有 baseline 时按 baseline 执行，不要当成与「宋体」并列的第二套默认。
- 正文与章节标题通过 `doc.styles` 设置一次，不逐 run 写；大标题/元信息等一次性段落例外。
- Markdown/HTML 用 CSS 映射同名字体；LaTeX 用 `ctex` 的 CJK 字体映射。

字体检测不能只依赖 `InstalledFontCollection`。检查 `AppData\Local\Microsoft\Windows\Fonts`、注册表字体项、WPF `SystemFontFamilies` 或 `PrivateFontCollection`；只有全部找不到时才回退宋体。

```python
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn

def configure_styles(doc):
    normal = doc.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal.font.size = Pt(11)                       # specs.BODY_SIZE_PT
    normal.paragraph_format.line_spacing = 1.35     # specs.BODY_LINE_SPACING
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn('w:eastAsia'), '宋体')

    for lvl, size, color in (
        (1, 16, '2E74B5'),                          # specs.HEADING_SIZES_PT / COLOR_TITLE_BLUE
        (2, 13, '2E74B5'),
        (3, 12, '1F4D78'),                          # specs.COLOR_DARK_BLUE
    ):
        hs = doc.styles[f'Heading {lvl}']
        hs.font.size = Pt(size)
        hs.font.bold = True
        hs.font.color.rgb = RGBColor.from_string(color)
        hs.font.name = 'Times New Roman'
        hs.paragraph_format.line_spacing = 1.15     # specs.HEADING_LINE_SPACING
        hs.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
```

只有语义强调才做 per-run 格式化：粗体、斜体、彩色标签。优先创建 character style，不直接往每个 run 写完整字体属性。
大标题、模板元信息行（如 `mathdoc_cli` 的 Title/meta）是一次性段落，允许直接设 run 字体；正文/章节标题仍走样式；`omml_helpers` 的混排 helper 也属于按段落的局部处理。

## Spacing

- 非必要不添加空格；先判断空格是否有语义意义。
- 中文与中文、中文与标点之间不加空格。
- 中文与行内公式之间不加空格；需要间距时用排版间距。
- 文本段不允许首尾空格；从 Markdown 提取的 text/bold/italic 片段必须 `.strip()`。
- 公式内不用空格做对齐或视觉留白；`=`、`+`、`-` 两侧不加空格，减号用 U+2212。
- 确需空格时只保留语义需要的：英文单词间、标准数学记号约定、用户明确要求处。

## Page

无 baseline 文档或 baseline 不可读时的回退预设（取值与 `scripts/specs.py` 常量一致，`mathdoc_cli.py` 直接引用这些常量）：

- Page: 8.5 × 11 in；左/右页边距 1 in，上/下 0.8 in（`specs.PAGE_*` / `MARGIN_*`）。
- Body: 宋体 + Times New Roman，正文 **11pt、行距 1.35**（`specs.BODY_SIZE_PT` / `BODY_LINE_SPACING`）。
- Headings: 黑体 + Times New Roman；H1 16pt、H2 13pt、H3 12pt，**行距 1.15**；H1/H2 标题蓝 `#2E74B5`，H3 深蓝 `#1F4D78`；均加粗（`specs.HEADING_*` / `COLOR_*`）。
- Title 大标题：22pt bold，中文用方正小标宋简体，拉丁用 Times New Roman（`specs.TITLE_SIZE_PT`）。
- 模板元信息行（一次性）：10pt、灰色 `#595959`（`specs.META_SIZE_PT` / `COLOR_GRAY`）。
- Math: OMML via latex2mathml -> MML2OMML pipeline。

A4 与 2.1cm/2.54cm 边距是部分项目 **baseline** 的习惯取值（如逐章讲义的生产文档），**不是第二套默认标准**。
**有 baseline 文档时一律以 baseline 为准**；上面的回退预设只在无法读取 baseline 时使用。
字体名、字号、行距、颜色、页边距统一以 `scripts/specs.py` 常量为单一真相源（`FONT_*` / `BODY_*` / `HEADING_*` / `TITLE_SIZE_PT` / `MARGIN_*` / `COLOR_*`）；`validator.py` 用同一份字体常量断言，生成侧与文档同源。

字体名、字号、行距、颜色、页边距统一以 `scripts/specs.py` 常量为单一真相源；`validator.py` 用同一份字体常量断言，生成侧与文档同源，改一处不会两侧漂移。

## Table

必做：

- 表题（表N xxx）：位于表格**下方**、**居中**、常规字体**不加粗**、不用黑体（latin 用 Times New Roman）——用户格式要求，2026-08-16；旧约定「表上方黑体加粗」作废。实现：表格元素后追加居中段落，`space_before=4 / space_after=6`。
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

## Equation Alignment

公式对齐同样服从开头的格式优先级：**用户/期刊/学校模板明确要求**（左对齐、编号在左、逐行编号、无编号等）时以要求/模板为准；否则按以下默认。

### 默认规则（从零新建、用户未要求）

- **行内公式**：随正文排版，不居中、不单独成段；不要让行内公式把所在段落变成居中对齐。
- **独立单行公式**：公式**居中**，编号 `(n)` 放**右侧**（右制表位 / 右对齐）；公式与编号之间留空，编号不塞进公式内部。
- **多行推导 / 等价变形**：整组作为一个公式块**居中**，组内按 `=`、`≈`、`≤`、`⇒` 等关系符**垂直对齐**；编号逐行右对齐，或按模板要求只在首/末行编号。
- **长公式**（超出版心）：只在关系符/运算符处折行，折行后整体仍居中，编号放最后一行右侧；不缩字号、不强行溢出。
- **cases / 分段函数 / 矩阵 / 行列式**：独立成行、整体居中；cases 内部的条件文字列左对齐。
- **表格单元格里的公式**：随单元格内容居中或按该表既有对齐，不套用独立公式的换行/编号规则。
- **列表 / 定理 / 证明内的独立公式**：相对于所属块的版心居中；不要按整页版心重新居中而破坏缩进层级。

### 禁止

- 不要对所有公式一律居中：行内公式、表格内短公式、混排段落中的公式不居中；
- 不要用空格/全角空格手动"推"出居中效果，用段落对齐、制表位或两列表格；
- 不要把一组对齐公式拆成多个互不关联的居中段落；
- 不要把公式编号写进 `m:oMath` 内部（编号是段落文本/编号列，不是公式内容）；
- 模板未要求时，不要全局把 display math 设成左对齐/右对齐。

### Word / OMML 机制

- 独立公式段落：段落对齐 `CENTER` + 右侧制表位放编号；`mathdoc_cli.add_numbered_equation` 即此实现，编号制表位 = 版心右边界（页宽 − 左右页边距）。
- 仅含公式的段落会被 Word 当作 display math，水平位置还受 `m:oMathParaPr/m:jc` 影响（默认 `centerGroup`）；需要整段左/右对齐时按模板/用户要求显式覆盖，并在交付说明中注明。
- 多行公式用 `aligned`（生成侧自动改写为 `array{rl}` → OMML `m:m`）作为单个公式块，不要拆成多段分别居中。

## Baseline Extraction

生成前先打开最相似的已有 docx，记录 Normal/Heading 字体、页边距、表格样式、表头填充/对齐、网格宽度和 OMML 约定。生成后按该 checklist 对比。如果参考 docx 打不开，直接读 `word/document.xml` 和 `word/styles.xml`；仍失败才使用回退预设。
