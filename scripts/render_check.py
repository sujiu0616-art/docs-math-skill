# -*- coding: utf-8 -*-
"""Lightweight rendering smoke test: docx -> PDF (LibreOffice) -> extract text -> probes.

Pixel diff (render_diff.py) is heavy and needs two PDFs; render_check answers
"did the document render and do key strings survive" in one command.

IMPORTANT: probe strings must match the document text BYTE-FOR-BYTE, including
spaces — "z变换" will MISS if the document says "z 变换". When a probe MISSes,
first check whether the document actually contains that wording (content gap),
before suspecting a rendering failure.

Usage:
    python scripts/render_check.py path/to/doc.docx [probe probe ...]
"""
import os
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

# Override with env var MATHDOC_SOFFICE if LibreOffice is installed elsewhere.
SOFFICE = Path(os.environ.get("MATHDOC_SOFFICE", r"C:\Program Files\LibreOffice\program\soffice.exe"))


def check(docx: Path) -> int:
    pdf = docx.with_suffix(".pdf")
    subprocess.run(
        [str(SOFFICE), "--headless", "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx)],
        check=True,
        capture_output=True,
    )
    reader = PdfReader(str(pdf))
    text = "".join((p.extract_text() or "") for p in reader.pages)
    print(f"pages: {len(reader.pages)}")
    print(f"text chars: {len(text)}")

    probes = sys.argv[2:]
    if not probes:
        print("no probes given; pass keywords after the docx path")
        return 0
    fails = 0
    for probe in probes:
        found = probe in text
        print(f"  probe {probe!r}: {'OK' if found else 'MISSING'}")
        if not found:
            fails += 1
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(check(Path(sys.argv[1])))
