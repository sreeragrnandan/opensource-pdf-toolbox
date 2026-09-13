#!/usr/bin/env python3
"""
pdf_tool_main.py — Entry point for OpenSource PDF Toolbox.

Usage:
    python pdf_tool_main.py

Dependencies:
    pip install pikepdf Pillow tkinterdnd2
"""

import tkinter as tk

from core.dependencies import HAS_DND, TkinterDnD
from ui.app import PDFToolsApp


def main() -> None:
    root = TkinterDnD.Tk() if HAS_DND else tk.Tk()

    try:
        root.iconbitmap(default='')  # suppress default Tk icon warning on Windows
    except Exception:
        pass

    PDFToolsApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
