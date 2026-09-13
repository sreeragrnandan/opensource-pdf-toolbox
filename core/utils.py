"""core/utils.py — Shared utility functions."""

import os
import sys
import subprocess


def fmt_bytes(n: float) -> str:
    """Format a byte count as a human-readable string (B / KB / MB / GB)."""
    for unit in ('B', 'KB', 'MB', 'GB'):
        if abs(n) < 1024.0:
            return f'{n:.1f} {unit}'
        n /= 1024.0
    return f'{n:.1f} TB'


def open_path(path: str) -> None:
    """Open a file or folder with the OS default application."""
    try:
        if sys.platform == 'win32':
            os.startfile(path)           # uses default PDF viewer on Windows
        elif sys.platform == 'darwin':
            subprocess.call(['open', path])
        else:
            subprocess.call(['xdg-open', path])
    except Exception:
        pass  # silently ignore if no default app is registered
