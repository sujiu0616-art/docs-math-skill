# math-doc Skill

A Claude Code / Codex / ZCode skill for generating professional mathematical documents (proofs, derivations, notes, formula-heavy reports) as `.docx`, LaTeX, or Markdown.

## Features

- **OMML math pipeline**: LaTeX → MathML → Word-native OMML via Microsoft's `MML2OMML.XSL` — formulas are native Word equations, not Unicode approximations or images.
- **Chinese typography rules**: 方正小标宋简体 body, 黑体 headings, Times New Roman for Latin/digits.
- **Three-level validation**: `validator.py --level 1|2|3` checks equations, fonts, table grids, header rows (`cantSplit`/`tblHeader`/`E8EEF5` shading), page layout — as executable assertions, not eyeballing.
- **Rendering QA**: pixel diff between PDFs (`render_diff.py`) or a lightweight text-probe smoke test (`render_check.py`).
- **Pre-generation formula check**: `formula_check.py` batch-verifies every LaTeX formula against the converter before you write the generator.

## Installation

Copy (or symlink) the `math-doc` folder into your agent's skills directory:

```bash
# Claude Code
cp -r math-doc ~/.claude/skills/

# Codex
cp -r math-doc ~/.codex/skills/

# ZCode
cp -r math-doc ~/.zcode/skills/
```

## Dependencies

- Python: `latex2mathml`, `python-docx`, `lxml`, `pypdf`
- Microsoft Word with `MML2OMML.XSL` (Office 16) — or set `MATHDOC_MML2OMML` to point at the XSL
- LibreOffice for PDF rendering (`MATHDOC_SOFFICE` to override its location)
- Poppler (`pdftoppm`) for pixel diff — `PDFTOPPM` to point at a native exe

## Usage

```bash
# Generate a skeleton
python scripts/mathdoc_cli.py --template proof --title 证明 --output proof.docx

# Verify a generated document
python scripts/validator.py proof.docx --level 2

# Pre-check formulas before generating
python scripts/formula_check.py --file new_formulas.txt

# Lightweight render smoke test
python scripts/render_check.py proof.docx 定理 证明 复习清单
```

## Layout

```
SKILL.md            entry point: purpose, pipeline, mandatory rules, failure handling
references/         docx-style, omml, markdown-parser, validator, performance, lessons
scripts/            latex_to_omml.py, omml_helpers.py, mathdoc_cli.py,
                    validator.py, formula_check.py, render_check.py, render_diff.py
```

## License

Not specified — contact the author for reuse terms.
