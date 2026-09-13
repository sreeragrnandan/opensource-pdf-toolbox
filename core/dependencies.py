"""
core/dependencies.py
Centralised optional-library imports and availability flags.
All other modules import from here instead of repeating try/except blocks.
"""

from typing import List

MISSING_LIBS: List[str] = []

# ── pikepdf ───────────────────────────────────────────────────────────────────
try:
    import pikepdf
    from pikepdf import Pdf, Page, PdfImage, Name, ObjectStreamMode
    HAS_PIKEPDF = True
except ImportError:
    pikepdf = None          # type: ignore[assignment]
    Pdf = Page = PdfImage = Name = ObjectStreamMode = None  # type: ignore
    HAS_PIKEPDF = False
    MISSING_LIBS.append('pikepdf')

# ── Pillow ────────────────────────────────────────────────────────────────────
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    Image = None            # type: ignore[assignment]
    HAS_PIL = False
    MISSING_LIBS.append('Pillow')

# ── tkinterdnd2 (optional — drag-and-drop) ────────────────────────────────────
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    TkinterDnD = None       # type: ignore[assignment,misc]
    DND_FILES  = None       # type: ignore[assignment]
    HAS_DND = False

# ── PyMuPDF / fitz (optional — page thumbnail rendering) ─────────────────────
try:
    import fitz
    HAS_FITZ = True
except ImportError:
    fitz = None             # type: ignore[assignment]
    HAS_FITZ = False

