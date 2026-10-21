# math-doc Skill Changelog

## 2026-09-20 v2.8.0 — 整理轮：修缺陷、去重复、打通同步

本轮以「清理 + 修缺陷 + 结构去重」为目标，不新增能力；对外接口保持兼容。

**修复的真实缺陷**

- `validator.py`：回流代码块豁免（此前滞留在 `.agents` 副本，是唯一产生功能分叉的改动）。含 Consolas 代码块（正文里带 `**`/`$`/首尾空格）的文档不再被误判为 markdown 残留。
- `publish_report.py`：`_find_xsl()` 不抛异常且返回值被丢弃，导致「OMML 引擎来源」可能在引擎缺失时照样写 "local Office installation"。改为真实编译一次 XSLT 作为探测；引擎不可用时报告如实标注并警告其不能作为「公式是原生 OMML」的证据。
- `publish_report.py`：报告产物名硬编码 `source.md`，与 `--source` 传入的实际文件名矛盾；失败路径直接退出、报告恒为 PASS。现在按实际文件名写入，且**失败也会产出报告**（结论 FAIL + 失败原因）。
- `render_diff.py`：`--out` 解析后从未使用，差异图不落盘 —— 现在真正写出放大的逐页差异图，供人眼复核 DIFF 判定。
- `render_check.py`：`check()` 直接读 `sys.argv`，无法作为模块调用；中间 PDF 会写进用户文档目录。现在 `check(docx, probes, keep_pdf=False)` 接受参数，PDF 默认写临时目录（`--keep-pdf` 可保留），转换失败返回退出码 2 而不是抛栈。
- `render_check.py` / `render_diff.py`：外部工具改为「环境变量 → PATH → 常见安装路径」解析（`specs.find_soffice` / `specs.find_pdftoppm`），并自动跳过 Windows 上会报「找不到路径」的 `.cmd` 包装器。
- `formula_check.py`：删除未使用的 `HERE`；`open()` 补上下文管理。
- `omml_helpers.py`：删除与 `FONT_CN` 同值的冗余常量 `FONT_CN_FALLBACK`。
- `latex_to_omml.py` / XSLT：XML 解析显式关闭外部实体与网络访问（XXE 防护）。

**结构去重**

- 新增 `scripts/specs.py` 零依赖叶子模块，收纳两侧共用的事实：`NARY_LIM_LOC`（此前生成侧与校验侧各写一份字面量）、`FONT_*` 字体名（此前散在 `mathdoc_cli`、`omml_helpers` 与 validator 的裸字符串）、表头底纹、页面预设、外部工具定位。
- `latex_to_omml` 四个入口收敛为 `latex_to_omml(latex, alttext=None, fix_limits=True)`，旧名 `latex_to_omml_alt/_fixed/_fixed_alt` 保留为等价别名 —— 文档反复警告「必须走 `_fixed_alt`」正是入口过多的症状。
- `fix_sum_limits` 的 limLow 构造改为复用 `omml_helpers.mlim`；`publish_report` 的公式计数改为复用 `validator.collect_stats`。

**文档订正**

- `references/omml.md`：删除重复的 `## Absolute Value Safety Rule` 标题。
- `references/docx-style.md`：三套互相矛盾的字号统一为 16/13/12（与 `mathdoc_cli.py` 实际取值一致），修正 H3 颜色（深蓝 `#1F4D78` 而非标题蓝），页边距与页面预设改写为与代码一致，并标明 A4/2.1cm 属部分项目习惯、有 baseline 时以 baseline 为准。
- `references/lessons.md`：删除把裸 `|z|` 列为「验证通过的语法」的表述（与绝对值守则冲突），补上它作为反面样本的说明；n-ary 限位一节补记「limLoc 在行内公式里不一定被遵守」这一实测边界，避免把 naryPr 归一化当成已完全解决。
- `references/performance.md`：示例引用了不存在的 `mathml_to_omml.xsl` 且函数名遮蔽真实入口，改为反映 `_get_xslt()` 单次编译 + 缓存的真实模式。
- `references/validator.md`：补代码块豁免与 `\left(...\right)` 内以正负号开头（`\left({-}x\right)`）这两个 `empty m:e` 来源；补字体断言以 `specs.py` 为准、项目基线另有约定时不适用的说明；PDF 段改为指向脚本而非硬编码路径。
- `SKILL.md`：删除硬编码的个人机器路径与三条指向个人目录的「Reference Implementations」；渲染段改为工具定位说明；与 references 逐字重复的细则改为指路。

**同步与清理**

- `sync_install.sh` 纳入仓库并重写：源改为**仓库自身**（此前把某个安装目录当源头，导致仓库的通用化修复同步不进来），目标覆盖本机实际存在的 4 个安装位置（含此前遗漏的 `.agents` —— 正是分叉根因），同步时清理 `__pycache__` 与 `.pytest_cache`，支持 `--dry-run`。
- `.gitignore` 补 `.pytest_cache/`；删除 `examples/paper.pdf`（无人引用，且已被 `.gitignore` 忽略）。
- README 用例数订正为 107（此前 91/94/107 三处不一致）。

## 2026-08-16 v2.7.2

- 修复 aligned 环境转换崩溃：latex2mathml 不识别 `aligned`，把对齐符 `&` 当普通字符输出成 `<mi>&</mi>`（裸 `&`，非法 XML），整条链在 etree 解析处崩溃。`latex_to_omml_alt` 入口新增 `_rewrite_aligned` 生成侧预处理：aligned → `array{rl}`（`&` 前右对齐、后左对齐，语义等价），latex2mathml 正确转成 OMML `m:m` 多行对齐数组；`[t]/[b]/[c]` 垂直参数安全剥离；嵌套 aligned 递归处理。
- 回归测试新增 13 个 aligned 用例（两行/三行/单行/`[t]`/含求和/嵌套/前后内容/普通公式不误伤），共 107 用例全过。
- `references/omml.md` 新增 aligned Safety Rule；SKILL.md Formula 规则补充。

## 2026-08-16 v2.7.1

- 表格标题格式规则更新：表题（表N xxx）位于表格**下方**、**居中**、常规字体**不加粗**、不用黑体（latin=Times New Roman）。旧约定「表上方黑体加粗」作废。SKILL.md Styles 节与 `references/docx-style.md` Table 节同步。
- 该规则经 `mathdoc_learn.py` 沉淀为第一条个人经验（`~/.config/math-doc/user-lessons.md`），动态 skill 首次产出。

## 2026-08-16 v2.7

- 动态 skill：新增 `scripts/mathdoc_learn.py`，任务完成自动把经验追加到个人经验库 `~/.config/math-doc/user-lessons.md`（自动带日期、问题/根因/修复/验证格式、同天合并、去重）；经验库在 skill 目录之外，`sync_install.sh` 不覆盖。
- SKILL.md 新增 Auto-Learning 章节：任务开始前自动读取 user-lessons.md（优先级：用户明确要求 > 个人经验 > 内置默认规则），完成后自动追加新踩坑/用户格式要求/新验证语法，用户无需手动操作。
- `references/lessons.md` 明确保持只读（内置通用经验），个人经验一律进 user-lessons.md。

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
