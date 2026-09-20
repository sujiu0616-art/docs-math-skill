# Performance

公式密集型文档（>50 公式）执行 checklist：

- [ ] 公式去重：唯一公式只转换一次并缓存，重复出现时 `deepcopy` 复用。
- [ ] XSLT transform：整个 MathML -> OMML 用 C-level 单遍，不用 Python 逐元素递归。
- [ ] 全局样式：Normal/Heading 样式只设一次，run 继承。
- [ ] 延迟挂载：完整构建 OMML 子树后再 `append`，避免中间态 deepcopy。
- [ ] 批量验证：对最终 `.docx` 做一次 XPath 扫描，不做逐元素 Python 检查。
- [ ] 空格审计：生成文本中不留装饰性字面空格。

## C-Level Parsing

优先 XSLT 和 XPath；Python 层只做 regex/占位符/组装。

```python
# Pattern: load and compile the XSLT once, reuse across all formulas.
# scripts/latex_to_omml.py::_get_xslt() 就是这个模式：
#   首次调用编译 MML2OMML.XSL 并缓存到模块级变量，之后所有公式复用同一个
#   已编译的 XSLT 对象 —— 每次转换重新 parse + 编译 XSL 是数量级的浪费。

def _get_xslt():
    global _xslt
    if _xslt is None:
        _xslt = etree.XSLT(etree.parse(xsl_path, parser=_xml_parser()))
    return _xslt
```

不要另写一个「LaTeX -> OMML」的包装函数：入口只有一个，就是
`latex_to_omml`（见 `references/omml.md` 的 Canonical Pipeline）。

## Formula Cache

```python
unique_formulas = set()
for formula in unique_formulas:
    cache[formula] = latex_to_omml(formula)

# reuse attached elements only after deepcopy
p2._element.append(copy.deepcopy(cache['x']))
```

首次构建的子树没有 parent，可以安全缓存；一旦 append 后，复用必须 `deepcopy`。

## Stress Test Guideline

- 公式出现次数 > 100：必须启用缓存统计，记录 unique/total/hits，并确认重复公式没有重复执行 LaTeX 转换。
- 公式出现次数 > 200：必须运行内存检查，建议在构建前后采样 RSS 或 `tracemalloc`，确认缓存不会无界增长、文档不会因重复 deepcopy 导致峰值内存异常。

```python
import json

stats = {
    "total_formula_occurrences": cache.total,
    "unique_formulas": cache.unique,
    "cache_hits": cache.hits,
}
with open("cache_stats.json", "w", encoding="utf-8") as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)
```
