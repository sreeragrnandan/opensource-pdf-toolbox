"""
ui/app.py
Main application shell — window setup, header, tab bar, and tab switching.
Delegates all tab content to CompressTab and MergeTab.
"""

import tkinter as tk

from core import HAS_DND, MISSING_LIBS
from core.dependencies import TkinterDnD
from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT_H,
    TXT, TXT2, TXT3, FF,
)
from ui.compress_tab import CompressTab
from ui.merge_tab import MergeTab


class PDFToolsApp:
    """
    Top-level application.  Owns the window, header, and tab switcher.
    Each tab is an isolated class that receives (parent_frame, root).
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self._active_tab = 'compress'

        self._setup_window()
        self._build_ui()

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.root.title('OpenSource PDF Toolbox')
        self.root.configure(bg=BG)
        W, H = 840, 740
        self.root.geometry(f'{W}x{H}')
        self.root.minsize(680, 600)
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f'{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}')

    # ── Main UI ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_header()
        self._build_tab_bar()

        # Allocate one Frame per tab; only the active one is packed
        self._compress_frame = tk.Frame(self.root, bg=BG)
        self._merge_frame    = tk.Frame(self.root, bg=BG)

        # Instantiate tab controllers
        self._compress_tab = CompressTab(self._compress_frame, self.root)
        self._merge_tab    = MergeTab(self._merge_frame,    self.root)

        # Show Compress tab by default
        self._compress_frame.pack(fill='both', expand=True)

        # Wire up DnD on the compress drop zone (needs root to be fully set up)
        if HAS_DND:
            self._compress_tab._setup_dnd()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill='x', padx=28, pady=(20, 0))

        tk.Label(bar, text='⊛', font=(FF, 26, 'bold'), bg=BG, fg=ACCENT).pack(
            side='left', padx=(0, 10))

        col = tk.Frame(bar, bg=BG)
        col.pack(side='left')
        tk.Label(col, text='OpenSource PDF Toolbox',
                 font=(FF, 18, 'bold'), bg=BG, fg=TXT).pack(anchor='w')
        tk.Label(col, text='Compress & Merge PDFs  ·  Offline  ·  Your files never leave your machine',
                 font=(FF, 9), bg=BG, fg=TXT3).pack(anchor='w')

        if MISSING_LIBS:
            warn = f'⚠  Missing: {", ".join(MISSING_LIBS)}   →   pip install {" ".join(MISSING_LIBS)}'
            tk.Label(bar, text=warn, font=(FF, 9), bg=BG, fg='#F59E0B').pack(side='right')

    # ── Tab bar ───────────────────────────────────────────────────────────────

    def _build_tab_bar(self) -> None:
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill='x', padx=28, pady=(14, 0))

        self._tab_btns: dict = {}
        for key, label in [('compress', '⚡  Compress'), ('merge', '🔗  Merge')]:
            btn = tk.Button(
                bar, text=label,
                font=(FF, 11, 'bold'), bd=0, relief='flat',
                cursor='hand2', padx=20, pady=8,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(side='left', padx=(0, 4))
            self._tab_btns[key] = btn

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill='x', pady=(8, 0))
        self._refresh_tab_styles()

    def _refresh_tab_styles(self) -> None:
        for key, btn in self._tab_btns.items():
            if key == self._active_tab:
                btn.config(bg=ACCENT, fg='white',
                           activebackground=ACCENT_H, activeforeground='white')
            else:
                btn.config(bg=SURFACE, fg=TXT2,
                           activebackground=CARD, activeforeground=TXT)

    def _switch_tab(self, tab: str) -> None:
        if tab == self._active_tab:
            return
        self._active_tab = tab
        self._refresh_tab_styles()
        if tab == 'compress':
            self._merge_frame.pack_forget()
            self._compress_frame.pack(fill='both', expand=True)
        else:
            self._compress_frame.pack_forget()
            self._merge_frame.pack(fill='both', expand=True)
