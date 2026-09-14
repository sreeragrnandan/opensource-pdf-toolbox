#!/usr/bin/env python3
"""
pdf_tool_main.py — Entry point for OpenSource PDF Toolbox.

Usage:
    python pdf_tool_main.py

Dependencies:
    pip install pikepdf Pillow tkinterdnd2
"""

import os
import sys
import tkinter as tk

from core.dependencies import HAS_DND, TkinterDnD
from ui.app import PDFToolsApp


def resource_path(relative: str) -> str:
    """Return the absolute path to a bundled resource.

    Works both when running as a plain script and when frozen by
    PyInstaller (sys._MEIPASS is the temp extraction directory).
    """
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def main() -> None:
    root = TkinterDnD.Tk() if HAS_DND else tk.Tk()

    # Set application icon (works in both script and .exe mode)
    try:
        icon_ico = resource_path(os.path.join('assets', 'icon.ico'))
        if os.path.exists(icon_ico):
            root.iconbitmap(default=icon_ico)
        else:
            icon_png = resource_path(os.path.join('assets', 'icon.png'))
            if os.path.exists(icon_png):
                from PIL import Image, ImageTk
                img = Image.open(icon_png)
                photo = ImageTk.PhotoImage(img)
                root.iconphoto(True, photo)
    except Exception:
        pass  # silently ignore if icon cannot be loaded

    PDFToolsApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
