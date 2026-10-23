# Pitfalls: 现象 → 规则 → 依据

> 只放可复用的硬经验，不写项目名/日期/叙事。完整历史见 `CHANGELOG.md` 的 H-01…H-09。

## P1 公式预检必须先于生成

- 现象：生成中途才发现某个 LaTeX 语法不可转换，定位成本高。
- 规则：写生成器前先跑 `scripts/formula_check.py` 批量验证全部新公式，0 失败再生成。
- 依据：CHANGELOG H-01；理由：预检是最便宜的验证点。

## P2 绝对值不能写成裸 `|...|`

- 现象：裸 `|x|` 会产出空 `m:e`，validator 报 B2。
- 规则：生成侧统一写 `\left|...\right|`；手工 OMML 用 `mabs`。
- 依据：CHANGELOG H-02 / `references/omml.md` Absolute Value Safety Rule。

## P3 主题字体会覆盖显式字体

- 现象：标题设了黑体/小标宋，Word 实际仍按主题字体渲染，XML 字体断言可能漏过。
- 规则：设置字体前删除 `w:rFonts` 上的 `*Theme` 属性；生成后转 PDF 读内嵌字体名复核（validator S4 只覆盖 XML 侧）。
- 依据：CHANGELOG H-03。

## P4 编号公式的 ∑/∏ 必须结构化

- 现象：行内 oMath + 编号制表位时 `limLoc` 不生效，上下限被压成侧标。
- 规则：编号公式用 `latex_to_omml(..., stack_limits=True)` 产出 `m:limUpp(m:limLow(...))`，不依赖 `m:nary`。
- 依据：CHANGELOG H-04 / `references/omml.md`。

## P5 大标题默认居中

- 现象：只写了正文/表格/公式对齐规则，标题没有约束，生成器默认左对齐。
- 规则：Title/标题块默认居中，章节标题左对齐；validator S5 断言，有模板时以模板为准。
- 依据：CHANGELOG H-05。

## P6 渲染 probe 必须与文档字节级一致

- 现象：probe MISSING 可能只是用词/全半角/空格不一致，不是渲染失败。
- 规则：probe 用文档实际用词并保持字节级一致；MISSING 先查文档是否真有该词，再判断渲染。
- 依据：CHANGELOG H-06。

## P7 baseline 模板继承要保留 sectPr

- 现象：从零重建样式会与既有模板不一致，页边距/节属性丢失。
- 规则：以成品 docx 为模板打开，清空 body 但保留 `sectPr`；样式、页边距、节属性随模板继承。
- 依据：CHANGELOG H-07。

## P8 页码 `PAGE` 是域代码

- 现象：`python-docx` 不能直接写页码域，直接放文本不会自动更新。
- 规则：手工 append `w:fldChar(begin)` + `w:instrText(" PAGE ")` + `w:fldChar(end)`；页眉/页脚先设 `is_linked_to_previous = False`。
- 依据：CHANGELOG H-08。
