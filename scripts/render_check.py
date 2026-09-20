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

Exit codes: 0 = rendered and all probes found (or no probes given);
            1 = at least one probe missing; 2 = cannot render (no LibreOffice / bad input).

外部命令调用说明：``soffice`` 以**参数列表**方式调用，从不拼接 shell 字符串，
也不使用 ``shell=True``；可执行文件路径先校验为真实存在的文件。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from specs import find_soffice  # noqa: E402

from pypdf import PdfReader  # noqa: E402


def _trusted_soffice() -> str:
    """解析并校验 soffice 路径（``MATHDOC_SOFFICE`` 可覆盖）。"""
    exe = find_soffice()
    if exe is None:
        raise FileNotFoundError(
            'LibreOffice not found; set MATHDOC_SOFFICE to the soffice executable'
        )
    resolved = Path(exe).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f'soffice is not a file: {resolved}')
    return str(resolved)


def check(docx: Path, probes: list[str], keep_pdf: bool = False,
          pdf_dir: Path | None = None) -> int:
    """把 docx 渲染成 PDF 并逐条核对 probe 文本是否存活。

    ``keep_pdf=True`` 时把 PDF 留在 ``pdf_dir``（或 docx 同目录），否则写临时目录、
    用完即删 —— 不给用户文档目录留下副产物。
    """
    src = Path(docx).resolve()
    if not src.is_file():
        print(f'FAIL: not a file: {src}')
        return 2

    exe = _trusted_soffice()

    cleanup = None
    if keep_pdf:
        out_dir = Path(pdf_dir) if pdf_dir else src.parent
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        cleanup = tempfile.TemporaryDirectory()
        out_dir = Path(cleanup.name)

    try:
        # 参数列表调用，shell=False（默认）：没有 shell 解析。
        subprocess.run(
            [exe, '--headless', '--convert-to', 'pdf', '--outdir', str(out_dir), str(src)],
            check=True,
            capture_output=True,
            shell=False,
        )
        pdf = out_dir / (src.stem + '.pdf')
        if not pdf.exists():
            print(f'FAIL: no PDF produced at {pdf}')
            return 2
        reader = PdfReader(str(pdf))
        text = ''.join((p.extract_text() or '') for p in reader.pages)
        print(f'pages: {len(reader.pages)}')
        print(f'text chars: {len(text)}')

        if not probes:
            print('no probes given; pass keywords after the docx path')
            return 0
        fails = 0
        for probe in probes:
            found = probe in text
            print(f'  probe {probe!r}: {"OK" if found else "MISSING"}')
            if not found:
                fails += 1
        return 1 if fails else 0
    except subprocess.CalledProcessError as exc:
        print(f'FAIL: LibreOffice conversion failed (exit {exc.returncode})')
        return 2
    except FileNotFoundError as exc:
        print(f'FAIL: {exc}')
        return 2
    finally:
        if cleanup is not None:
            cleanup.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('docx', type=Path, help='generated .docx file')
    parser.add_argument('probes', nargs='*', help='关键词，必须与文档措辞逐字节一致')
    parser.add_argument('--keep-pdf', action='store_true',
                        help='把中间 PDF 留在磁盘上（默认写临时目录）')
    parser.add_argument('--pdf-dir', type=Path,
                        help='配合 --keep-pdf 指定 PDF 输出目录，默认 docx 同目录')
    args = parser.parse_args()
    return check(args.docx, args.probes, keep_pdf=args.keep_pdf, pdf_dir=args.pdf_dir)


if __name__ == '__main__':
    sys.exit(main())
