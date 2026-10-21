# Markdown Parser Rules

## Pipeline

```text
Markdown -> block parsing -> inline parsing (placeholder) -> latex2mathml -> MathML -> OMML -> docx
```

## Inline bold across `$...$`

先把每个 `$...$` 替换为占位符 `<<<MATH0>>>`，在统一文本上匹配 `**...**`，再恢复数学占位符。这避免粗体标记被公式切分。

```python
text = re.sub(r'\$(.*?)\$', lambda m: f'<<<MATH{i}>>>', text)
text = re.sub(r'\*\*(.*?)\*\*', lambda m: f'<b>{m.group(1)}</b>', text)
# restore math placeholders after bold parsing
```

## Literal `$...$`

如果捕获内容是 `...`、`$`，或匹配 `^[$]+[.]*$`，保留为字面文本，不送入 latex2mathml。

## `\tfrac` and `mstyle`

latex2mathml 可能把 `\tfrac` 包在 `<mstyle>` 中。XSLT 必须处理 `mstyle` 子节点，不能返回 `None`，否则分数静默消失。

```xml
<xsl:template match="m:mstyle">
  <xsl:apply-templates/>
</xsl:template>
```

## CJK text and spaces

所有 text/bold/italic 片段在添加 run 前 `.strip()`。OMML 元素自带视觉间隔，不保留 Markdown 源码空格作为可见 padding。

## Same-paragraph line breaks

Markdown 段落内单个 `\n` 是空格，不是硬换行。用 `' '.join()` 合并段落行，不用 `'\n'.join()`。

## Mixed text and math paragraphs

`segments` 约定：`('t', 中文)`、`('m', [omml children])`、`('b', 粗体)`。

```python
p = doc.add_paragraph()
for kind, data in segments:
    if kind == 't':
        p.add_run(data)
    elif kind == 'm':
        p._element.append(omath(*data))
    elif kind == 'b':
        r = p.add_run(data)
        r.bold = True
```

同一个 helper 在 `scripts/omml_helpers.py` 中可用：`mpara_mix()`。
