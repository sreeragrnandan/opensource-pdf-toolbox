"""
core/unlock.py
PDF password-removal engine: open an encrypted PDF and save it unencrypted.
"""

import os
from pathlib import Path
from typing import Optional

from core.dependencies import HAS_PIKEPDF, Pdf


# ── Public API ────────────────────────────────────────────────────────────────

def remove_pdf_password(
    input_path: str,
    output_path: str,
    password: str = '',
) -> dict:
    """
    Open a password-protected PDF and save it without encryption.

    Parameters
    ----------
    input_path  : str   Path to the encrypted PDF.
    output_path : str   Destination path for the unlocked PDF.
    password    : str   Owner or user password (empty string → try no password).

    Returns
    -------
    dict with keys:
        original   int   Original file size in bytes.
        output     str   Path of the saved unlocked file.
        unlocked   bool  Always True (exception raised on failure).

    Raises
    ------
    RuntimeError  – if pikepdf is not installed.
    pikepdf.PasswordError – if the password is wrong.
    Exception     – for other I/O or format errors.
    """
    if not HAS_PIKEPDF:
        raise RuntimeError(
            'pikepdf is not installed. Run: pip install pikepdf'
        )

    orig_size = os.path.getsize(input_path)

    # pikepdf raises pikepdf.PasswordError automatically on wrong password
    with Pdf.open(input_path, password=password) as pdf:
        pdf.save(output_path)   # saved without any encryption

    return {
        'original': orig_size,
        'output':   output_path,
        'unlocked': True,
    }
