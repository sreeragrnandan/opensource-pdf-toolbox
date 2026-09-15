# core/__init__.py
# Exposes the public API of the core package.

from core.dependencies import HAS_PIKEPDF, HAS_PIL, HAS_DND, HAS_FITZ, MISSING_LIBS
from core.utils import fmt_bytes, open_path
from core.compress import compress_pdf, PRESETS
from core.merge import merge_pdfs
from core.rearrange import get_pdf_info, render_page_thumbnail, save_rearranged_pdf
from core.unlock import remove_pdf_password

__all__ = [
    'HAS_PIKEPDF', 'HAS_PIL', 'HAS_DND', 'HAS_FITZ', 'MISSING_LIBS',
    'fmt_bytes', 'open_path',
    'compress_pdf', 'PRESETS',
    'merge_pdfs',
    'get_pdf_info', 'render_page_thumbnail', 'save_rearranged_pdf',
    'remove_pdf_password',
]

