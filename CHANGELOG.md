# math-doc Skill Changelog

## 2026-08-16 v2.5

- 全面通用化：SKILL.md 描述与触发词不再枚举具体文档类型，任何数学 Word 文档需求（讲义、习题集、笔记、论文、报告）均可命中；Task Router 增加兜底路由，删除"复习清单"场景示例。
- `references/lessons.md` 去掉信号与系统项目痕迹，改写为通用批量生成经验。

## 2026-08-16 v2.4.3

- 西文与数字规则落地：validator 对 Normal 与 Heading 1-3 增加 `w:ascii`/`w:hAnsi` = Times New Roman 检查（规则原本已在 SKILL.md/docx-style.md）。
- 修正 Title 检查：仅当文档实际使用 Title 样式段落时才检查 eastAsia=方正小标宋简体，run 级大标题不再误报。

## 2026-08-16 v2.4.2

- 二级标题（Heading 2）规则明确为黑体加粗：SKILL.md 与 docx-style.md 补充规则，validator 对 Heading 2 增加 bold 检查。
- 章节标题字体体系：大标题（Title）方正小标宋简体、正文（Normal）宋体、章节标题（Heading 1-3）黑体（Heading 2 加粗）。

## 2026-08-16 v2.4.1

- 正文字体从 方正小标宋简体 改为 宋体（正文即 Normal 样式）。
- 大标题（Title/文档首行）固定为 方正小标宋简体：`mathdoc_cli.py` 新增 `TITLE_CN` 并写入 title run 的 `w:eastAsia`；validator 增加 Title 样式检查；docx-style.md 与 SKILL.md 同步规则。
- 章节标题（Heading 1-3）保持 黑体 不变。

## 2026-08-16 v2.4

- 新增 `scripts/formula_check.py`：生成前批量验证 LaTeX 公式与 latex_to_omml 的兼容性，避免生成中途失败。
- 新增 `scripts/render_check.py`：轻量渲染冒烟（soffice 转 PDF + pypdf 提取文本 + probes）；probe 需与文档用词字节级一致。
- 新增 `references/lessons.md`：信号与系统 7-10 章批量生成实战——公式预验证、断言验证、渲染冒烟翻车记录（probe 空格/缩写/章节专属词）、GBK 乱码假警报、模板继承与页码 field、逐章流水线。
- SKILL.md：Validation 增加"生成前 formula_check"步骤；Rendering 与 Scripts 补充新工具用法。

## 2026-08-10 v2.3

- `references/omml.md` 新增明确 `Absolute Value` 规则：禁止裸 `|x|` 和 `\|x\|`，必须使用 `\left|...\right|` 或 OMML `mabs` 分隔符结构。
- 说明根因：ASCII `|` 可能产生非法 MathML/OMML，典型表现为独立公式 `|X|^2` 生成空 `m:e`。

## 2026-08-10 v2.2

- Rendering 增加 Windows Poppler fallback：优先调用原生 `pdftoppm.exe`，避免 `.cmd` shim 报“找不到路径”。
- 同步更新 `SKILL.md` 与 `references/validator.md` 的 PDF 渲染步骤。

## 2026-08-10 v2.1

- 绝对值公式规则：LaTeX 统一使用 `\left|...\right|`，避免裸 `|X|^2` 生成空 `m:e`。
- validator 对空 `m:e` 增加可操作的修复提示；Heading 样式缺失或未显式设置 eastAsia 黑体时现在会报错。
- 更新 `references/omml.md` 与 `references/validator.md`，记录绝对值公式排查路径。

## 2026-08-10 v2.0

- 从单一长 SKILL.md 重构为入口 + `references/` + `scripts/` 分层结构。
- 新增任务路由、错误处理、版本管理和三级验证。
- 保留 latex2mathml -> XSLT -> OMML 管线、表格 tblGrid/表头规则、字体检测、公式缓存和 PDF diff 经验。

## 历史事故记录

- 2026-08-02：信号与系统第三章 docx 只设置 `cell.width`，最终 `tblGrid` 仍是均分宽度，Word 按均分列渲染。修复：同时写 `tblGrid/gridCol`、`tcW`、`tblLayout fixed`。
- 2026-08-02：同一批第三章 docx 只调列宽，漏掉表头底纹、垂直居中和跨页表头。修复：`tblHeader`、`cantSplit`、`keepNext`、`shd E8EEF5`、`vAlign=center`。
