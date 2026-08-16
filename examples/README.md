# Examples

Four sample documents, generated and validated by this skill:

| File | Kind | Contents |
|---|---|---|
| `lecture_notes.docx` | 讲义 | notes template: 主题、要点、公式、待复习 |
| `proof.docx` | 证明 | proof template: 定理、已知条件、证明链、结论 |
| `exercises.docx` | 习题集 | 4 道带编号公式的习题 + 参考答案提示 |
| `paper.docx` | 论文 | 摘要 + 编号公式 (1)-(3) 的示例论文 |

`reports/validation-report.md` is the delivery report produced by
`scripts/publish_report.py` for `paper.docx` — it records equation count,
validation checks and the OMML engine, so a recipient can verify the equations
are native Word OMML (double-click editable), not Unicode text or images.

## Reproduce in one command

```bash
pip install -r requirements.txt
python examples/generate_samples.py          # regenerates the 4 .docx
python scripts/validator.py examples/paper.docx --level 2
python scripts/render_check.py examples/paper.docx 摘要 结论
python scripts/publish_report.py examples/paper.docx --level 2 \
    --report examples/reports/validation-report.md
```

All example documents pass `validator.py --level 2` and the render smoke test
(`pages: 1, probes OK`). The generated `.docx` files are committed so you can
open them in Word/WPS immediately — double-click any equation to edit it.
