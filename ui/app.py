"""
ui/app.py
Main application shell — window setup, header, tab bar, and tab switching.
Delegates all tab content to CompressTab and MergeTab.
"""

import tkinter as tk
import webbrowser

from core import HAS_DND, MISSING_LIBS
from core.dependencies import TkinterDnD
from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT_H,
    TXT, TXT2, TXT3, FF,
)
from ui.compress_tab import CompressTab
from ui.merge_tab import MergeTab
from ui.rearrange_tab import RearrangeTab


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
        W, H = 880, 760
        self.root.geometry(f'{W}x{H}')
        self.root.minsize(720, 620)
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f'{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}')

    # ── Main UI ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_header()
        self._build_tab_bar()

        # Allocate one Frame per tab; only the active one is packed
        self._compress_frame  = tk.Frame(self.root, bg=BG)
        self._merge_frame     = tk.Frame(self.root, bg=BG)
        self._rearrange_frame = tk.Frame(self.root, bg=BG)

        # Instantiate tab controllers
        self._compress_tab  = CompressTab(self._compress_frame,   self.root)
        self._merge_tab     = MergeTab(self._merge_frame,         self.root)
        self._rearrange_tab = RearrangeTab(self._rearrange_frame, self.root)

        # Show Compress tab by default
        self._compress_frame.pack(fill='both', expand=True)

        # Wire up DnD on drop zones (needs root to be fully set up)
        if HAS_DND:
            self._compress_tab._setup_dnd()
            self._rearrange_tab.setup_dnd()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill='x', padx=28, pady=(20, 0))

        # ── Row 1: icon + title + buttons ────────────────────────────────────
        row1 = tk.Frame(header, bg=BG)
        row1.pack(fill='x')

        tk.Label(row1, text='⊛', font=(FF, 22, 'bold'), bg=BG, fg=ACCENT).pack(
            side='left', padx=(0, 10))

        tk.Label(row1, text='OpenSource PDF Toolbox',
                 font=(FF, 16, 'bold'), bg=BG, fg=TXT).pack(side='left', anchor='w')

        # Buy Me a Coffee (far right)
        coffee_btn = tk.Button(
            row1,
            text='☕  Buy me a coffee',
            font=(FF, 9, 'bold'),
            bg='#FFDD00', fg='#1E1E1E',
            activebackground='#FFE54D', activeforeground='#000000',
            bd=0, relief='flat', cursor='hand2',
            padx=10, pady=5,
            command=lambda: webbrowser.open('https://buymeacoffee.com/sreeragrnandan'),
        )
        coffee_btn.pack(side='right', pady=2)
        coffee_btn.bind('<Enter>', lambda _: coffee_btn.config(bg='#FFE54D'))
        coffee_btn.bind('<Leave>', lambda _: coffee_btn.config(bg='#FFDD00'))

        # GitHub
        github_btn = tk.Button(
            row1,
            text='⭐  GitHub',
            font=(FF, 9, 'bold'),
            bg='#24292E', fg='#FFFFFF',
            activebackground='#2F363D', activeforeground='#FFFFFF',
            bd=0, relief='flat', cursor='hand2',
            padx=10, pady=5,
            command=lambda: webbrowser.open('https://github.com/sreeragrnandan/opensource-pdf-toolbox'),
        )
        github_btn.pack(side='right', padx=(0, 8), pady=2)
        github_btn.bind('<Enter>', lambda _: github_btn.config(bg='#2F363D'))
        github_btn.bind('<Leave>', lambda _: github_btn.config(bg='#24292E'))

        # LinkedIn
        linkedin_btn = tk.Button(
            row1,
            text='in  LinkedIn',
            font=(FF, 9, 'bold'),
            bg='#0A66C2', fg='#FFFFFF',
            activebackground='#0958A8', activeforeground='#FFFFFF',
            bd=0, relief='flat', cursor='hand2',
            padx=10, pady=5,
            command=lambda: webbrowser.open('https://www.linkedin.com/in/srnofficial'),
        )
        linkedin_btn.pack(side='right', padx=(0, 8), pady=2)
        linkedin_btn.bind('<Enter>', lambda _: linkedin_btn.config(bg='#0958A8'))
        linkedin_btn.bind('<Leave>', lambda _: linkedin_btn.config(bg='#0A66C2'))

        # ── Row 2: subtitle ───────────────────────────────────────────────────
        row2 = tk.Frame(header, bg=BG)
        row2.pack(fill='x', pady=(2, 0))

        tk.Label(row2,
                 text='Compress, Merge, Rearrange & Delete Pages  ·  Offline  ·  Your files never leave your machine',
                 font=(FF, 9), bg=BG, fg=TXT3).pack(side='left', padx=(36, 0))

        if MISSING_LIBS:
            warn = f'⚠  Missing: {", ".join(MISSING_LIBS)}   →   pip install {" ".join(MISSING_LIBS)}'
            tk.Label(row2, text=warn, font=(FF, 9), bg=BG, fg='#F59E0B').pack(side='right')

    # ── Tab bar ───────────────────────────────────────────────────────────────

    def _build_tab_bar(self) -> None:
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill='x', padx=28, pady=(14, 0))

        self._tab_btns: dict = {}
        tabs = [
            ('compress', '⚡  Compress'),
            ('merge', '🔗  Merge'),
            ('rearrange', '📑  Rearrange & Delete Pages'),
        ]
        for key, label_text in tabs:
            btn = tk.Button(
                bar, text=label_text,
                font=(FF, 10, 'bold'), bd=0, relief='flat',
                cursor='hand2', padx=16, pady=8,
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

        # Hide all frames
        self._compress_frame.pack_forget()
        self._merge_frame.pack_forget()
        self._rearrange_frame.pack_forget()

        # Show selected frame
        if tab == 'compress':
            self._compress_frame.pack(fill='both', expand=True)
        elif tab == 'merge':
            self._merge_frame.pack(fill='both', expand=True)
        elif tab == 'rearrange':
            self._rearrange_frame.pack(fill='both', expand=True)
