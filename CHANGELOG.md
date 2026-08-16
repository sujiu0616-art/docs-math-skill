# math-doc Skill Changelog

## 2026-08-16 v2.6.1

- 修复求和/连乘/积分 naryPr 结构：`fix_sum_limits` 归一化为参考结构 `chr + limLoc + grow + ctrlPr(Cambria Math)`（移除 MML2OMML.XSL 默认输出的 `subHide/supHide="off"`），与上下标渲染正确的参考文档一致。某些查看器对带 subHide/supHide 的 naryPr 会按侧边角标渲染求和上限。
- `references/omml.md` 补充 naryPr 参考结构说明；examples 全部重新生成并通过 validator --level 2、render_check 与 94 个回归用例。

## 2026-08-16 v2.6

- 新增 `scripts/publish_report.py` 交付报告：对生成的 docx 跑 validator 并输出 `validation-report.md`（公式数、校验项、OMML 引擎来源），构成 source/result/report 三件套，可证明公式是原生 OMML。
- 新增 `examples/`：讲义/证明/习题集/论文 4 份样例 docx + 复现脚本 + 交付报告示例；新增 `tests/test_mathml_only.py` 无 Office 可跑的轻量测试。
- 新增 GitHub Actions CI（pytest，OMML 用例无 XSL 自动 skip）与 MIT LICENSE。
- README 重写：第一屏改为「能生成什么/为什么可靠/怎么验证」，能力对比表、通用目录表安装、测试徽章。

## 2026-08-16 v2.5.3

- 明确字体/排版规则的语义：SKILL.md 与 docx-style.md 标注为「用户未要求时的默认值」，用户明确指定格式时以用户为准，默认规则不覆盖用户格式。

## 2026-08-16 v2.5.2

- 新增 `tests/test_latex_to_omml.py` 回归测试：22 个生产公式（ch7-10 提取）× 4 项断言 + 3 个结构规则，91 用例全过；无 MML2OMML.XSL 时自动 skip。
- 新增本地 `sync_install.sh`：一键镜像本地源安装到各 agent 安装目录（排除 `__pycache__`），防止手动复制漏文件。

## 2026-08-16 v2.5.1

- `latex_to_omml.py` 本地点位改为环境变量 + 候选路径（`MATHDOC_MML2OMML` 优先，回退 Office 常用安装路径），与发布版一致，换机器不再需要改代码。
- 新增 `requirements.txt` 依赖清单（latex2mathml、lxml、python-docx、pypdf、Pillow）。

## 2026-08-16 v2.5

- 全面通用化：SKILL.md 描述与触发词不再枚举具体文档类型，任何数学 Word 文档需求（讲义、习题集、笔记、论文、报告）均可命中；Task Router 增加兜底路由，删除"复习清单"场景示例。
- `references/lessons.md` 去掉具体项目痕迹，改写为通用批量生成经验。

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
- 新增 `references/lessons.md`：批量章节文档生成实战（2026-08）——公式预验证、断言验证、渲染冒烟翻车记录（probe 空格/缩写/章节专属词）、GBK 乱码假警报、模板继承与页码 field、逐章流水线。
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

- 2026-08-02：批量章节 docx 只设置 `cell.width`，最终 `tblGrid` 仍是均分宽度，Word 按均分列渲染。修复：同时写 `tblGrid/gridCol`、`tcW`、`tblLayout fixed`。
- 2026-08-02：同一批章节 docx 只调列宽，漏掉表头底纹、垂直居中和跨页表头。修复：`tblHeader`、`cantSplit`、`keepNext`、`shd E8EEF5`、`vAlign=center`。
