#!/usr/bin/env python3
"""Render two PDFs to PNGs and report page-level pixel differences."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops


def render_pdf(pdf_path: Path, out_dir: Path, dpi: int) -> list[Path]:
    # PDFTOPPM env var overrides PATH lookup (use it to point at a native
    # pdftoppm.exe on Windows instead of a .cmd shim).
    exe = os.environ.get('PDFTOPPM') or shutil.which('pdftoppm')
    if not exe or not Path(exe).exists():
        raise FileNotFoundError('pdftoppm not found; set PDFTOPPM to its location')
    prefix = out_dir / pdf_path.stem
    subprocess.run([exe, '-png', '-r', str(dpi), str(pdf_path), str(prefix)], check=True)
    return sorted(out_dir.glob(pdf_path.stem + '-*.png'))


def compare_images(a: Path, b: Path) -> tuple[float, int, int, int]:
    im_a = Image.open(a).convert('L')
    im_b = Image.open(b).convert('L')
    if im_a.size != im_b.size:
        raise ValueError(f'size mismatch: {a.name} {im_a.size} vs {b.name} {im_b.size}')
    diff = ImageChops.difference(im_a, im_b)
    hist = diff.histogram()
    changed = sum(hist[1:])
    total = im_a.size[0] * im_a.size[1]
    max_diff = max(i for i, count in enumerate(hist) if count)
    return changed / total, changed, total, max_diff


def main() -> None:
    parser = argparse.ArgumentParser(description='Compare two rendered PDFs.')
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--dpi', type=int, default=150)
    parser.add_argument('--threshold', type=float, default=0.02)
    parser.add_argument('--out', type=Path, default=Path('render_diff'))
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as td:
        before_dir = Path(td) / 'before'
        after_dir = Path(td) / 'after'
        before_dir.mkdir()
        after_dir.mkdir()
        before_pages = render_pdf(args.before, before_dir, args.dpi)
        after_pages = render_pdf(args.after, after_dir, args.dpi)
        if len(before_pages) != len(after_pages):
            raise SystemExit(f'page count mismatch: {len(before_pages)} vs {len(after_pages)}')
        for bp, ap in zip(before_pages, after_pages):
            ratio, changed, total, max_diff = compare_images(bp, ap)
            status = 'OK' if ratio <= args.threshold else 'DIFF'
            print(f'{bp.stem}: {status} changed={ratio:.4%} pixels={changed}/{total} max={max_diff}')
            if ratio > args.threshold:
                raise SystemExit(1)


if __name__ == '__main__':
    main()
