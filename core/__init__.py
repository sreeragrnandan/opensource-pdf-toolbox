# core/__init__.py
# Exposes the public API of the core package.

from core.dependencies import HAS_PIKEPDF, HAS_PIL, HAS_DND, MISSING_LIBS
from core.utils import fmt_bytes, open_path
from core.compress import compress_pdf, PRESETS
from core.merge import merge_pdfs

__all__ = [
    'HAS_PIKEPDF', 'HAS_PIL', 'HAS_DND', 'MISSING_LIBS',
    'fmt_bytes', 'open_path',
    'compress_pdf', 'PRESETS',
    'merge_pdfs',
]
