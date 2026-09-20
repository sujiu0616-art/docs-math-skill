#!/usr/bin/env python3
"""Render two PDFs to PNGs and report page-level pixel differences.

差异图落盘：传 ``--out DIR`` 时，每页写一张放大的差异图（未变处为白、变化处为黑），
供人眼复核 ``DIFF`` 判定是否真的是版式问题。不传则不写任何文件。

Usage:
    python scripts/render_diff.py before.pdf after.pdf --dpi 150 --threshold 0.02 --out out/

外部命令调用说明：``pdftoppm`` 以**参数列表**方式调用，从不拼接 shell 字符串，
也不使用 ``shell=True``；可执行文件路径先经 ``_trusted_exe()`` 校验为真实存在的
文件，PDF/输出路径先经 ``_require_file()`` 校验为真实文件。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parent))
from specs import find_pdftoppm  # noqa: E402


def _trusted_exe() -> str:
    """解析并校验 pdftoppm 的可执行文件路径。

    只接受确实存在的普通文件（Windows 上还要求是原生 .exe，排除 .cmd 包装器），
    避免把任意字符串当程序名交给 subprocess。
    """
    exe = find_pdftoppm()
    if exe is None:
        raise FileNotFoundError(
            'pdftoppm not found; set PDFTOPPM to its location '
            '(Windows: point it at the native pdftoppm.exe, not the .cmd shim)'
        )
    resolved = Path(exe).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f'pdftoppm is not a file: {resolved}')
    if sys.platform == 'win32' and resolved.suffix.lower() != '.exe':
        raise FileNotFoundError(f'pdftoppm must be a native .exe on Windows: {resolved}')
    return str(resolved)


def _require_file(p: Path) -> Path:
    """校验输入确实是一个文件，避免把目录或设备路径传给外部命令。"""
    q = Path(p).resolve()
    if not q.is_file():
        raise FileNotFoundError(f'not a file: {q}')
    return q


def render_pdf(pdf_path: Path, out_dir: Path, dpi: int) -> list[Path]:
    exe = _trusted_exe()
    src = _require_file(pdf_path)
    prefix = out_dir / src.stem
    # 参数列表调用，shell=False（默认）：没有 shell 解析，参数不会被当作命令执行。
    subprocess.run(
        [exe, '-png', '-r', str(int(dpi)), str(src), str(prefix)],
        check=True,
        shell=False,
    )
    return sorted(out_dir.glob(src.stem + '-*.png'))


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


def write_diff_image(a: Path, b: Path, dest: Path) -> None:
    """把差异放大成可视图像：未变处白、变化处按差异强度加深。"""
    im_a = Image.open(a).convert('L')
    im_b = Image.open(b).convert('L')
    diff = ImageChops.difference(im_a, im_b)
    # 放大 4 倍并反相，让细微差异肉眼可见
    amplified = diff.point(lambda v: 255 - min(255, v * 4))
    dest.parent.mkdir(parents=True, exist_ok=True)
    amplified.save(dest)


def main() -> None:
    parser = argparse.ArgumentParser(description='Compare two rendered PDFs.')
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--dpi', type=int, default=150)
    parser.add_argument('--threshold', type=float, default=0.02)
    parser.add_argument('--out', type=Path,
                        help='write amplified per-page diff images into this directory')
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
        failed = False
        for bp, ap in zip(before_pages, after_pages):
            ratio, changed, total, max_diff = compare_images(bp, ap)
            status = 'OK' if ratio <= args.threshold else 'DIFF'
            print(f'{bp.stem}: {status} changed={ratio:.4%} pixels={changed}/{total} max={max_diff}')
            if ratio > args.threshold:
                failed = True
                if args.out:
                    dest = args.out / f'{bp.stem}-diff.png'
                    write_diff_image(bp, ap, dest)
                    print(f'    diff image -> {dest}')
        if failed:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
