"""
core/rearrange.py
Core logic for rearranging and deleting pages in a PDF document.
Uses pikepdf for lossless page tree manipulation and fitz (PyMuPDF)
for fast thumbnail generation.
"""

from pathlib import Path
from typing import Callable, Dict, List, Optional, Any

from core.dependencies import (
    HAS_PIKEPDF, pikepdf,
    HAS_PIL, Image,
    HAS_FITZ, fitz,
)


def get_pdf_info(pdf_path: str) -> Dict[str, Any]:
    """
    Return basic metadata for a PDF file: page count and file size in bytes.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    RuntimeError
        If pikepdf is missing or fails to open the document.
    """
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    if not HAS_PIKEPDF:
        raise RuntimeError("pikepdf is required to read PDF documents.")

    with pikepdf.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)

    return {
        'page_count': num_pages,
        'file_size': p.stat().st_size,
        'filename': p.name,
    }


def render_page_thumbnail(
    pdf_path: str,
    page_num: int,
    max_w: int = 120,
    max_h: int = 160,
) -> Optional[Any]:
    """
    Render a single page of a PDF as a PIL.Image thumbnail.

    Parameters
    ----------
    pdf_path : str
        Path to the PDF file.
    page_num : int
        0-based page index.
    max_w : int
        Maximum width in pixels.
    max_h : int
        Maximum height in pixels.

    Returns
    -------
    PIL.Image.Image or None
        Thumbnail image, or None if PyMuPDF or Pillow is unavailable.
    """
    if not (HAS_FITZ and HAS_PIL):
        return None

    try:
        doc = fitz.open(pdf_path)
        try:
            if page_num < 0 or page_num >= len(doc):
                return None
            page = doc.load_page(page_num)
            rect = page.rect
            if rect.width <= 0 or rect.height <= 0:
                return None

            scale = min(max_w / rect.width, max_h / rect.height)
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return img
        finally:
            doc.close()
    except Exception:
        return None


def save_rearranged_pdf(
    src_path: str,
    dst_path: str,
    page_order: List[int],
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
    """
    Build and save a new PDF containing only the pages specified in `page_order`,
    in that exact sequence.

    Parameters
    ----------
    src_path : str
        Source PDF file path.
    dst_path : str
        Destination path for the output PDF.
    page_order : List[int]
        0-based list of page indices to include, in desired order.
    progress_cb : Callable[[int, int], None], optional
        Called with (current_page_idx, total_pages) during export.

    Returns
    -------
    dict
        Statistics dict with keys:
        'orig_pages', 'new_pages', 'orig_size', 'new_size', 'output_path'
    """
    if not HAS_PIKEPDF:
        raise RuntimeError("pikepdf is required to manipulate PDF pages.")

    src = Path(src_path)
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src_path}")

    if not page_order:
        raise ValueError("Cannot save a PDF with 0 pages.")

    orig_size = src.stat().st_size
    dst = Path(dst_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    with pikepdf.open(src_path) as src_pdf:
        total_orig_pages = len(src_pdf.pages)
        # Validate indices
        for p in page_order:
            if p < 0 or p >= total_orig_pages:
                raise IndexError(f"Page index {p} is out of bounds (document has {total_orig_pages} pages).")

        new_pdf = pikepdf.new()
        total_to_add = len(page_order)

        for i, page_idx in enumerate(page_order):
            new_pdf.pages.append(src_pdf.pages[page_idx])
            if progress_cb:
                progress_cb(i + 1, total_to_add)

        new_pdf.save(dst_path)

    new_size = dst.stat().st_size

    return {
        'orig_pages': total_orig_pages,
        'new_pages': len(page_order),
        'orig_size': orig_size,
        'new_size': new_size,
        'output_path': str(dst),
    }
