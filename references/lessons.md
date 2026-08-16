# Lessons: 批量章节文档生成实战（2026-08）

多章节内容用同一流水线批量生成 docx 的实战记录：遇到的问题、解法、与 skill 现有能力的关系。每章约一小时，全部通过验证与渲染冒烟。

## 1. 生成前：公式批量预验证（新增工具 formula_check.py）

- 问题：`latex_to_omml` 的兼容性边界未知。新章节会用到未验证过的 LaTeX 语法（`|z|`、`\oint`、`\tilde{X}`、`z^{-n_0}`、`\ast` 等），生成中途报错或产出坏公式时难定位。
- 解决：写生成脚本前先跑 `scripts/formula_check.py` 批量验证全部新公式，0 failures 再动笔。
- 本次验证通过的新语法（30 个公式全过）：`\sum` 带上下限、`\frac`、`\oint`、`|z|`、`\tilde{X}`、`\lim_{z\rightarrow\infty}`、`z^{-n_0}`、`z^{-1}`、`\ast`、`\mathrm`、`\supseteq`、`\leftrightarrow`、`e^{-j\omega_{0}}`、方括号 `[...]` 中的 `\cos` 项。`\sum`/`\lim` 上下限需要 `fix_sum_limits` 后处理。
- 经验：新内容先过一遍公式清单，是最便宜的验证点；FAIL 时换等价写法（如绝对值改 `\left|...\right|`），而不是绕过转换器用 Unicode。

## 2. 内联公式与文字混排

- 高频需求：同一段落里「文字 + 粗体 + 内联 OMML」混排（如"**性质**：绝对值恒有 `|z|\ge 0`"）。
- 实现：python-docx 中 `p._element.append(omml(latex))` 即可把 OMML 内联进普通段落；独立公式才用独占一行。`omml_helpers.py` 的 `mpara/mrn/mnary` 是底层积木，本项目用 `latex_to_omml + append` 更省事。
- 经验：混排段保持行距一致（1.25）、公式基线自动对齐；不要在混排段里塞整段居中。

## 3. 生成后：可执行断言验证

- 问题：表头底纹、跨页重复表头、列宽这些属性"隐形"，肉眼打开 docx 看不出来。
- 解决：`scripts/validator.py --level 2` 已覆盖 tblGrid/gridCol、cantSplit、tblHeader、shd E8EEF5、垂直居中——章节级 verify 脚本只需对齐 level 2 再加定制检查（标题文本比对、禁词列表）。
- 列宽换算：`567 twips/cm`；A4 页宽 21cm 减页边距后可用宽度 ≤16.8cm（2.1cm 边距），超宽 Word 会重新均分。
- 经验：样式正确性靠断言不靠眼；验证脚本十几秒跑完，比事后发现改版便宜一个量级。

## 4. 渲染冒烟：文本 probes（新增工具 render_check.py）

- 问题：像素 diff（render_diff.py）需要两张 PDF、开销大；章节级快速检查只需要"能否渲染 + 关键文本是否存活"。
- 解决：`scripts/render_check.py`（soffice 转 PDF + pypdf 提取文本 + probe 关键词）。
- 三次翻车记录（全部是 probe 设计问题，不是渲染问题）：
  - 章节没有某概念时 probe MISSING（某章不含该概念）→ probe 用章节专属词，不要全局硬编码。
  - 文档用缩写而 probe 用全称（文档写 "ROC" 而 probe 写 "收敛域"）→ probe 与文档实际用词一致。
  - 空格不匹配（"z变换" vs 文档的 "z 变换"）→ probe 必须字节级一致。
- 经验：MISSING 时先查文档是否真有该词，区分「内容缺失」和「渲染失败」；PDF 是临时产物，验证完删除。

## 5. Windows 中文输出乱码是假警报

- 问题：Windows 控制台 GBK，Python 中文输出全部显示为乱码，看起来像全错。
- 解决：不修。probe 匹配是字节级匹配并返回 OK，verify 的标题断言也通过——以 exit code 和字节匹配为判断依据，不是终端显示。
- 需要正常显示时：`PYTHONIOENCODING=utf-8 python ...` 或 `sys.stdout.reconfigure(encoding="utf-8")`。
- 经验：别为"修乱码"重写已验证逻辑；也别因显示乱码误判失败。

## 6. 模板继承与页码 field

- 样式一致性做法：以成品 docx 为模板（`Document(str(BASELINE))`），清空 body 但保留 sectPr——段落样式、页边距、节属性全继承。
- 页脚「第 PAGE 页」的 PAGE 是域代码，python-docx 不能直接写：手工 append `w:fldChar(begin)` + `w:instrText(" PAGE ")` + `w:fldChar(end)` 三个元素。
- 页眉/页脚设置后要 `is_linked_to_previous = False`，否则沿用前一节。
- 经验：模板 + 清正文是保样式一致的最稳路径，比从零建样式快且不出错。

## 7. 逐章流水线

固定八步：读原文 dump → 提取章节结构 → 翻译原表格 → 写生成脚本 → 生成 → 验证 → 渲染冒烟 → 清理临时 PDF。脚本间复制改参（mapping 表 + 性质表 + 变换对表 + 对比表），验证通过率从第一章稳定到最后一章。

## 与 skill 现有能力的关系

| 经验 | 状态 |
|---|---|
| 公式批量预验证 | 新增 `scripts/formula_check.py` |
| 渲染文本冒烟 | 新增 `scripts/render_check.py` |
| 表格可执行断言 | 已有 `validator.py --level 2`，复用即可 |
| 内联混排积木 | 已有 `omml_helpers.py` |
| 像素 diff | 已有 `render_diff.py`（重，按需用） |
