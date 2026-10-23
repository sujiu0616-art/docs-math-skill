# DOCX Style Standard

> 格式优先级见 `SKILL.md`；默认值 / baseline / 本机环境边界见 `references/project-scope.md`。
> 本文只写现行规则；默认数值以 `scripts/specs.py` 为准，不在文档里复述。

## Font

- 中文标题：章节标题（Heading 1-3）用黑体，二级标题黑体加粗；大标题（Title 或文档首行大标题）用方正小标宋简体。
- 中文正文：宋体。
- 数字、英文：Times New Roman。
- 公式字体：不手动指定，保留兼容性最好的数学字体（Word/WPS 默认，通常 Cambria Math）；必须显式设置时用 Times New Roman。
- 项目 baseline 可能使用仿宋、方正小标宋或其它中文字体：那是 baseline 约定，**不是本 skill 默认标准**；有 baseline 时按 baseline，不要把它当成与“宋体”并列的第二套默认。
- 正文与章节标题通过 `doc.styles` 设置一次，不逐 run 写；大标题/元信息等一次性段落例外。
- **主题字体陷阱**：`w:rFonts` 的 `w:asciiTheme`/`w:hAnsiTheme`/`w:eastAsiaTheme`/`w:cstheme` 优先于显式字体。设置字体前必须删除 `*Theme` 属性；检查项与修复见 `references/validator.md` 的 S4、`specs.THEME_FONT_ATTRS`。
- Markdown/HTML 用 CSS 映射同名字体；LaTeX 用 `ctex` 的 CJK 字体映射。

字体检测不能只依赖 `InstalledFontCollection`：要枚举实际字族并同时检查系统/用户字体目录（具体路径见 `references/project-scope.md` 的“本机环境示例”）；全部找不到时才回退宋体。XML 断言通过不等于渲染字体正确——有渲染工具时用 PDF 内嵌字体名复核（见 `references/validator.md` 的 PDF Rendering）。

样式实现：`scripts/mathdoc_cli.py` 的 `build_docx()` 设置一次 Normal/Heading/Title；不要在文档示例里复制一份硬编码样式代码。只有语义强调才做 per-run 格式化（粗体、斜体、彩色标签），优先用 character style。

## Spacing

- 非必要不加空格；先判断空格是否有语义。
- 中文与中文、中文与标点之间不加空格。
- 中文与行内公式之间不加空格；需要间距时用排版间距。
- 文本段不允许首尾空格；Markdown 提取的 text/bold/italic 片段必须 `.strip()`。
- 公式内不用空格做对齐或视觉留白；`=`、`+`、`-` 两侧不加空格，减号用 U+2212。
- 文内混排公式与正文同段、同行距；不要让混排公式单独居中或独占一行。
- 确需空格时只保留语义需要的：英文单词间、标准数学记号约定、用户明确要求处。

## Page

- 页面尺寸与页边距：`specs.PAGE_WIDTH_IN` / `PAGE_HEIGHT_IN` / `MARGIN_*`。
- 正文、章节标题的字号/行距/颜色：`specs.BODY_*` / `HEADING_*` / `COLOR_*`。
- 大标题与模板元信息：`specs.TITLE_SIZE_PT` / `META_SIZE_PT`。
- 层级：Title > Heading 1 > Heading 2 > Heading 3；章节标题左对齐，大标题/标题块居中（见 Alignment）。
- 无 baseline 或 baseline 不可读时，以上常量是回退预设；A4、2.1cm/2.54cm 边距等是项目 baseline 的习惯，不是第二套默认标准。
- 字体名、字号、行距、颜色、页边距统一以 `scripts/specs.py` 为单一真相源；validator 与生成侧共用同一份常量。

## Table

必做：

- 表题（表N xxx）：位于表格**下方**、**居中**、常规字体**不加粗**、不用黑体（Latin 用 Times New Roman）。实现：表格后追加居中段落，`space_before=4 / space_after=6`。
- 表头跨页重复：第一行 `w:tblHeader`。
- 表头底纹：`specs.TABLE_HEADER_FILL`（不要在文档里写死色值）。
- 所有单元格 `vAlign=center`。
- 表头行 `cantSplit`，表头单元格段落 `keepNext`。
- 单元格边距 top/bottom 80、left/right 120 twips。
- 列宽按内容自适应，但必须同时写 `w:tblGrid/gridCol` 和 `w:tcW`；不要只设 `cell.width`。
- `python-docx` 对 `w:shd` 写入不稳定；保存后若检查不到底纹，直接补丁 `word/document.xml`。

列宽实现：调用 `mathdoc_cli.set_table_widths(table, widths_cm)`（固定 `tblLayout`、写 `gridCol`/`tcW`/`tblW`）。该 helper 只支持不含水平合并的简单表；`w:gridSpan` 或列数不匹配会抛 `ValueError`。列宽不要硬编码固定值，应按内容长度、公式复杂度和可读性估计后缩放到可用页宽；内容列必须写实际内容名。

## Alignment

### 文档标题与元信息（默认）

- **大标题**：Title 样式段落或文档首行大标题段落，**居中**；多行标题整体居中，不缩进、不编号。
- **副标题、作者、日期、模板元信息**：默认随大标题**居中**。
- **章节标题**：Heading 1-3 默认**左对齐**，不居中（期刊/模板另有要求除外）。
- **正文**：默认左对齐（不强制两端对齐；模板要求时以模板为准）。

以上服从开头的格式优先级；用户/模板明确要求左对齐标题时以要求/模板为准。

### 表格列对齐

- 表头：始终居中。
- 短标签、状态、时间、勾选项：居中，列宽收窄。
- 长描述、要求、疑问、结论、复习要求：左对齐，列宽给足。
- 公式短表（如性质表）：整表居中。
- 混合表：按列判断，不能整表一刀切。

## Equation Alignment

公式对齐同样服从格式优先级：用户/期刊/学校模板明确要求（左对齐、编号在左、逐行编号、无编号等）时以要求/模板为准；否则按以下默认。

### 默认规则

- **行内公式**：随正文排版，不居中、不单独成段；不要让它把所在段落变成居中。
- **独立单行公式**：公式居中，编号 `(n)` 放右侧（右制表位 / 右对齐）；编号不塞进公式内部。
- **多行推导**：整组作为一个公式块居中，组内按 `=`、`≈`、`≤`、`⇒` 等关系符垂直对齐；编号逐行右对齐或按模板只标首/末行。
- **长公式**：只在关系符/运算符处折行，折行后整体仍居中，编号在最后一行右侧；不缩字号、不强行溢出。
- **cases / 分段函数 / 矩阵 / 行列式**：独立成行、整体居中；cases 内部条件文字列左对齐。
- **表格单元格公式**：随单元格内容对齐，不套用独立公式的换行/编号规则。
- **列表/定理/证明内的独立公式**：相对于所属块版心居中，不按整页版心重新居中。

### 实现约定

- 编号独立公式用「左对齐 + center tab（半版心）+ right tab（版心右边界）」，内容序列为 `TAB → m:oMath → TAB → (n)`；不要用段落 `CENTER`（编号也参与居中，公式会偏左）。实现见 `mathdoc_cli.add_numbered_equation`。
- 仅含公式的段落会被 Word 当 display math，水平位置受 `m:oMathParaPr/m:jc` 影响（默认 `centerGroup`）；需要整段左/右对齐时按模板显式覆盖并注明。
- 多行公式用 `aligned`（生成侧改写为 `array{rl}` → OMML `m:m`）作为单个公式块，不要拆成多段。
- **编号公式的 inline 陷阱**：行内 `m:oMath` + 编号制表位会被 Word 按 inline math 排，`naryPr/limLoc` 不生效；∑/∏ 必须用 `latex_to_omml(..., stack_limits=True)` 结构化为 `m:limUpp(m:limLow(...))`。详见 `references/omml.md`。
- 禁止：用空格/全角空格“推”居中；把编号写进 `m:oMath`；行内/表格公式按独立公式居中；把一组对齐公式拆成多个无关居中段落。

编号公式的段落 XML 形状（简化）：

```xml
<w:p>
  <w:pPr>
    <w:jc w:val="left"/>
    <w:tabs>
      <w:tab w:val="center" w:pos="4680"/>  <!-- 半版心 -->
      <w:tab w:val="right"  w:pos="9360"/>  <!-- 版心右边界 -->
    </w:tabs>
  </w:pPr>
  <w:r><w:tab/></w:r>
  <m:oMath>…</m:oMath>
  <w:r><w:tab/><w:t>(1)</w:t></w:r>
</w:p>
```

自检：段落 `p.text` 为 `\t\t(1)`，oMath 位于两个 tab run 之间；Word/LO 中公式在页面中心、编号贴右边界。

## Baseline Extraction

生成前先打开最相似的已有 docx，记录 Normal/Heading 字体、页边距、表格样式、表头填充/对齐、网格宽度和 OMML 约定；生成后按 checklist 对比。参考 docx 打不开时直接读 `word/document.xml` 和 `word/styles.xml`，仍失败才使用回退预设。
