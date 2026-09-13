"""
ui/theme.py
Design tokens (colours, font) and shared widget factory functions.
Import from here everywhere instead of repeating constants.
"""

import tkinter as tk

# ── Colour palette ────────────────────────────────────────────────────────────

BG       = '#0D0D1A'   # window background
SURFACE  = '#13132A'   # slightly lighter surface (canvas backgrounds)
CARD     = '#1B1B33'   # card / panel background
BORDER   = '#2B2B4A'   # card border
ACCENT   = '#7C3AED'   # primary purple
ACCENT_H = '#9D5CF8'   # accent hover
ACC_LT   = '#A78BFA'   # accent light (for secondary highlights)
SUCCESS  = '#10B981'   # green for "saved / ok"
ERROR_C  = '#EF4444'   # red for errors
TXT      = '#F0EFF9'   # primary text
TXT2     = '#9694C2'   # secondary text
TXT3     = '#5C5A88'   # muted / hint text

# ── Typography ────────────────────────────────────────────────────────────────

FF = 'Segoe UI'        # system font on Windows; falls back gracefully elsewhere


# ── Reusable widget factories ─────────────────────────────────────────────────

def card(parent: tk.Widget, **kw) -> tk.Frame:
    """A dark-themed card frame with a 1-px border."""
    return tk.Frame(parent, bg=CARD,
                    highlightthickness=1, highlightbackground=BORDER, **kw)


def label(parent: tk.Widget, text: str, size: int = 11,
          bold: bool = False, color: str = TXT, **kw) -> tk.Label:
    """A consistently-styled label that inherits the parent bg."""
    weight = 'bold' if bold else 'normal'
    return tk.Label(parent, text=text, font=(FF, size, weight),
                    bg=parent['bg'], fg=color, **kw)


def progress_bar(canvas: tk.Canvas, pct: float) -> None:
    """
    Draw a filled progress bar inside *canvas*.
    The canvas height should be 6 px; width is read dynamically.
    """
    canvas.delete('all')
    W = canvas.winfo_width() or 400
    canvas.create_rectangle(0, 0, W, 6, fill=BORDER, outline='')
    if pct > 0:
        canvas.create_rectangle(0, 0, int(W * pct / 100), 6, fill=ACCENT, outline='')


def stat_cell(parent: tk.Widget, col: int, title: str, color: str) -> tk.Label:
    """
    One cell of a horizontal stats row (title label above value label).
    Grids itself at (row=0, column=col). Returns the value Label.
    """
    f = tk.Frame(parent, bg=CARD)
    f.grid(row=0, column=col, sticky='ew', padx=6)
    tk.Label(f, text=title, font=(FF, 8, 'bold'), bg=CARD, fg=TXT3).pack()
    v = tk.Label(f, text='—', font=(FF, 16, 'bold'), bg=CARD, fg=color)
    v.pack()
    return v
