"""
core/compress.py
PDF compression engine: preset definitions and the compress_pdf() function.
"""

import io
import os
from pathlib import Path
from typing import Callable, Optional

from core.dependencies import (
    HAS_PIKEPDF, HAS_PIL,
    Pdf, Page, PdfImage, Name, ObjectStreamMode, Image,
)

# ── Compression presets ───────────────────────────────────────────────────────

PRESETS: dict = {
    'low': {
        'label': '🔵  Low — Lossless',
        'desc':  'Stream compression & object deduplication only. No image changes.',
        'compress_images': False,
        'max_pixels': None,
        'quality': None,
    },
    'medium': {
        'label': '🟣  Medium — Balanced',
        'desc':  'Lossless tricks + images resampled to ~150 DPI. Best for most docs.',
        'compress_images': True,
        'max_pixels': (1275, 1650),   # ≈150 DPI on US Letter
        'quality': 82,
    },
    'high': {
        'label': '🔴  High — Maximum',
        'desc':  'Aggressive: images to ~96 DPI. Smallest file; images slightly softer.',
        'compress_images': True,
        'max_pixels': (816, 1056),    # ≈96 DPI on US Letter
        'quality': 65,
    },
}


# ── Public API ────────────────────────────────────────────────────────────────

def compress_pdf(
    input_path: str,
    output_path: str,
    preset_key: str,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> dict:
    """
    Compress a PDF at the chosen preset level.

    Returns a dict:
        original    int   original file size in bytes
        compressed  int   compressed file size in bytes
        saved       int   bytes saved (may be negative if already optimised)
        percent     float percentage reduction
        output      str   path to the output file
    """
    preset    = PRESETS[preset_key]
    orig_size = os.path.getsize(input_path)

    with Pdf.open(input_path) as pdf:
        n_pages = len(pdf.pages)

        if preset['compress_images'] and HAS_PIL and n_pages > 0:
            for i, page in enumerate(pdf.pages):
                _compress_page_images(page, preset['max_pixels'], preset['quality'])
                if progress_cb:
                    # Pages account for 0–75 % of total progress
                    progress_cb(int((i + 1) / n_pages * 75))

        if progress_cb:
            progress_cb(85)

        pdf.save(
            output_path,
            compress_streams=True,
            object_stream_mode=ObjectStreamMode.generate,
        )

    if progress_cb:
        progress_cb(100)

    comp_size = os.path.getsize(output_path)
    saved     = orig_size - comp_size
    pct       = saved / orig_size * 100 if orig_size else 0.0

    return {
        'original':   orig_size,
        'compressed': comp_size,
        'saved':      saved,
        'percent':    pct,
        'output':     output_path,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _compress_page_images(page, max_pixels, quality: int) -> None:
    """Re-encode all raster images on a single PDF page as JPEG."""
    try:
        imgs = Page(page).images
    except Exception:
        return

    for name in list(imgs.keys()):
        try:
            raw = imgs[name]
            pil = PdfImage(raw).as_pil_image()

            # Flatten alpha onto white background before JPEG encoding
            if pil.mode == 'RGBA':
                bg = Image.new('RGB', pil.size, (255, 255, 255))
                bg.paste(pil, mask=pil.split()[3])
                pil = bg
            elif pil.mode not in ('RGB', 'L'):
                pil = pil.convert('RGB')

            # Optionally down-sample to DPI target
            if max_pixels:
                mw, mh = max_pixels
                w, h   = pil.size
                if w > mw or h > mh:
                    scale = min(mw / w, mh / h)
                    pil = pil.resize(
                        (max(1, int(w * scale)), max(1, int(h * scale))),
                        Image.LANCZOS,
                    )

            buf = io.BytesIO()
            pil.save(buf, format='JPEG', quality=quality, optimize=True, progressive=True)
            buf.seek(0)
            data = buf.read()

            raw.write(data, filter=Name('/DCTDecode'))
            raw['/ColorSpace'] = (
                Name('/DeviceRGB') if pil.mode == 'RGB' else Name('/DeviceGray')
            )
            raw['/BitsPerComponent'] = 8
            raw['/Width']  = pil.width
            raw['/Height'] = pil.height

        except Exception:
            continue   # skip images we cannot process
