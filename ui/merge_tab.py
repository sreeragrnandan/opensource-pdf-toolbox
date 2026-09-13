"""
ui/merge_tab.py
Merge tab UI — file list with reorder controls, output file picker,
progress bar, and results panel. Merge work runs on a background thread.
"""

import threading
from pathlib import Path
from typing import List
import tkinter as tk
from tkinter import filedialog, messagebox

from core import merge_pdfs, HAS_PIKEPDF
from core.utils import fmt_bytes, open_path
from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT_H, ACC_LT, SUCCESS, ERROR_C,
    TXT, TXT2, TXT3, FF,
    card, label, progress_bar, stat_cell,
)


class MergeTab:
    """
    Builds and manages the Merge tab.

    Parameters
    ----------
    parent : tk.Frame
        The frame allocated for this tab by the parent App.
    root : tk.Tk
        The root window (needed for .after() thread-safe callbacks).
    """

    def __init__(self, parent: tk.Frame, root: tk.Tk) -> None:
        self._parent = parent
        self._root   = root

        # ── State ─────────────────────────────────────────────────────────────
        self.files:       List[str] = []
        self._progress    = 0.0
        self._res_visible = False

        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_filelist()
        self._build_output()
        self._build_action_row()
        self._build_results()

    # ── File list with reorder controls ──────────────────────────────────────

    def _build_filelist(self) -> None:
        outer = tk.Frame(self._parent, bg=BG)
        outer.pack(fill='both', expand=True, padx=28, pady=(14, 0))

        # Header
        hdr = tk.Frame(outer, bg=BG)
        hdr.pack(fill='x', pady=(0, 6))
        label(hdr, 'Files to Merge', bold=True).pack(side='left')
        label(hdr, '  Select a file then use ▲ ▼ to reorder  ·  double-click to remove',
              size=8, color=TXT3).pack(side='left', pady=(3, 0))

        # Action buttons (top-right)
        btn_row = tk.Frame(hdr, bg=BG)
        btn_row.pack(side='right')

        def action_btn(text: str, cmd, bg: str = BORDER, fg: str = TXT2) -> tk.Button:
            return tk.Button(btn_row, text=text, font=(FF, 9),
                              bg=bg, fg=fg, activebackground=SURFACE,
                              activeforeground=TXT, bd=0, relief='flat',
                              cursor='hand2', padx=12, pady=5, command=cmd)

        action_btn('✕  Clear All', self._clear_files).pack(side='right', padx=(4, 0))
        action_btn('＋  Add Files', self._add_files, bg=ACCENT, fg='white').pack(side='right')

        # Card: listbox + side reorder controls
        c = card(outer)
        c.pack(fill='both', expand=True)

        list_area = tk.Frame(c, bg=CARD)
        list_area.pack(side='left', fill='both', expand=True)

        sb = tk.Scrollbar(list_area, bg=SURFACE, troughcolor=SURFACE,
                          activebackground=BORDER, bd=0, relief='flat',
                          highlightthickness=0)
        sb.pack(side='right', fill='y', pady=8, padx=(0, 4))

        self._lb = tk.Listbox(
            list_area,
            font=(FF, 10), bg=CARD, fg=TXT,
            selectbackground=ACCENT, selectforeground='white',
            activestyle='none', bd=0, relief='flat',
            highlightthickness=0, yscrollcommand=sb.set,
        )
        self._lb.pack(side='left', fill='both', expand=True, padx=14, pady=10)
        sb.config(command=self._lb.yview)
        self._lb.bind('<Double-Button-1>', lambda _: self._remove_selected())

        # Side reorder / remove controls
        ctrl = tk.Frame(c, bg=CARD)
        ctrl.pack(side='right', padx=(0, 12), pady=10, fill='y')

        for text, cmd in [('▲', self._move_up), ('▼', self._move_down)]:
            tk.Button(ctrl, text=text, font=(FF, 14),
                      bg=SURFACE, fg=TXT2, activebackground=BORDER, activeforeground=TXT,
                      bd=0, relief='flat', cursor='hand2', width=2, pady=6,
                      command=cmd).pack(pady=2)

        tk.Frame(ctrl, bg=BORDER, height=1).pack(fill='x', pady=8)

        tk.Button(ctrl, text='✕', font=(FF, 12),
                  bg=SURFACE, fg=ERROR_C, activebackground=BORDER, activeforeground=ERROR_C,
                  bd=0, relief='flat', cursor='hand2', width=2, pady=4,
                  command=self._remove_selected).pack()

        # Empty-state hint (overlaid with place geometry)
        self._hint = tk.Label(
            c,
            text='Click  ＋ Add Files  to get started.\n\n'
                 'Add 2 or more PDFs, arrange the order,\nthen click  🔗 Merge PDFs.',
            font=(FF, 10), bg=CARD, fg=TXT3, justify='center',
        )
        self._hint.place(relx=0.5, rely=0.5, anchor='center')

    def _refresh_lb(self) -> None:
        self._lb.delete(0, 'end')
        for i, f in enumerate(self.files):
            self._lb.insert('end', f'   {i + 1}.   {Path(f).name}')
        if self.files:
            self._hint.place_forget()
        else:
            self._hint.place(relx=0.5, rely=0.5, anchor='center')

    def _add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title='Select PDF files to merge',
            filetypes=[('PDF files', '*.pdf'), ('All files', '*.*')],
        )
        if paths:
            existing = set(self.files)
            for p in paths:
                if p not in existing:
                    self.files.append(p)
                    existing.add(p)
            self._refresh_lb()
            self._clear_results()

    def _clear_files(self) -> None:
        self.files.clear()
        self._refresh_lb()
        self._clear_results()

    def _move_up(self) -> None:
        sel = self._lb.curselection()
        if not sel or sel[0] == 0:
            return
        i = sel[0]
        self.files[i], self.files[i - 1] = self.files[i - 1], self.files[i]
        self._refresh_lb()
        self._lb.selection_set(i - 1)

    def _move_down(self) -> None:
        sel = self._lb.curselection()
        if not sel or sel[0] >= len(self.files) - 1:
            return
        i = sel[0]
        self.files[i], self.files[i + 1] = self.files[i + 1], self.files[i]
        self._refresh_lb()
        self._lb.selection_set(i + 1)

    def _remove_selected(self) -> None:
        sel = self._lb.curselection()
        if not sel:
            return
        i = sel[0]
        self.files.pop(i)
        self._refresh_lb()
        if self.files:
            self._lb.selection_set(min(i, len(self.files) - 1))

    # ── Output file picker ────────────────────────────────────────────────────

    def _build_output(self) -> None:
        outer = tk.Frame(self._parent, bg=BG)
        outer.pack(fill='x', padx=28, pady=(12, 0))
        label(outer, 'Output File', bold=True).pack(anchor='w', pady=(0, 6))

        row = tk.Frame(outer, bg=BG)
        row.pack(fill='x')

        ef = tk.Frame(row, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        ef.pack(side='left', fill='x', expand=True)
        self._out_entry = tk.Entry(ef, font=(FF, 10), bg=CARD, fg=TXT2,
                                    insertbackground=TXT, bd=0, relief='flat')
        self._out_entry.pack(fill='x', padx=10, pady=8)
        self._out_entry.insert(0, 'merged_output.pdf')

        tk.Button(
            row, text='Browse…', font=(FF, 10),
            bg=CARD, fg=TXT2, activebackground=SURFACE, activeforeground=TXT,
            bd=0, relief='flat', cursor='hand2', padx=14, pady=8,
            highlightthickness=1, highlightbackground=BORDER,
            command=self._browse_output,
        ).pack(side='left', padx=(8, 0))

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title='Save merged PDF as…',
            defaultextension='.pdf',
            filetypes=[('PDF files', '*.pdf')],
            initialfile='merged_output.pdf',
        )
        if path:
            self._out_entry.delete(0, 'end')
            self._out_entry.insert(0, path)

    def _resolve_output(self) -> str:
        raw = self._out_entry.get().strip() or 'merged_output.pdf'
        p   = Path(raw)
        if not p.is_absolute() and self.files:
            p = Path(self.files[0]).parent / p
        return str(p)

    # ── Action row ────────────────────────────────────────────────────────────

    def _build_action_row(self) -> None:
        row = tk.Frame(self._parent, bg=BG)
        row.pack(fill='x', padx=28, pady=(14, 0))

        self._btn = tk.Button(
            row, text='🔗  Merge PDFs',
            font=(FF, 12, 'bold'), bg=ACCENT, fg='white',
            activebackground=ACCENT_H, activeforeground='white',
            bd=0, relief='flat', cursor='hand2', padx=24, pady=10,
            command=self._start,
        )
        self._btn.pack(side='left')

        prog_col = tk.Frame(row, bg=BG)
        prog_col.pack(side='left', fill='x', expand=True, padx=(16, 0))

        self._status = tk.Label(prog_col, text='', font=(FF, 10), bg=BG, fg=TXT2)
        self._status.pack(anchor='w')

        self._bar = tk.Canvas(prog_col, height=6, bg=SURFACE,
                               highlightthickness=0, bd=0)
        self._bar.pack(fill='x', pady=(4, 0))
        self._bar.bind('<Configure>', lambda _: self._draw_bar(self._progress))

    def _draw_bar(self, pct: float) -> None:
        self._progress = pct
        progress_bar(self._bar, pct)

    # ── Results panel ─────────────────────────────────────────────────────────

    def _build_results(self) -> None:
        outer = tk.Frame(self._parent, bg=BG)
        outer.pack(fill='x', padx=28, pady=(12, 20))
        self._res_card = card(outer)

        inner = tk.Frame(self._res_card, bg=CARD)
        inner.pack(fill='x', padx=20, pady=14)
        inner.columnconfigure((0, 1, 2), weight=1)

        self._m_files = stat_cell(inner, 0, 'FILES MERGED', TXT2)
        self._m_pages = stat_cell(inner, 1, 'TOTAL PAGES',  ACC_LT)
        self._m_size  = stat_cell(inner, 2, 'OUTPUT SIZE',  SUCCESS)

    def _clear_results(self) -> None:
        self._res_card.pack_forget()
        self._res_visible = False
        self._draw_bar(0)
        self._status.config(text='')

    def _show_results(self, stats: dict) -> None:
        self._m_files.config(text=str(stats['files']))
        self._m_pages.config(text=str(stats['pages']))
        self._m_size.config(text=fmt_bytes(stats['size']))
        if not self._res_visible:
            self._res_card.pack(fill='x')
            self._res_visible = True

    # ── Merge runner (background thread) ─────────────────────────────────────

    def _start(self) -> None:
        if len(self.files) < 2:
            messagebox.showwarning('Not Enough Files',
                                   'Please add at least 2 PDF files to merge.')
            return
        if not HAS_PIKEPDF:
            messagebox.showerror('Missing Library',
                                  'pikepdf is not installed.\nRun: pip install pikepdf')
            return

        out_path = self._resolve_output()
        files    = list(self.files)

        self._btn.config(state='disabled', text='Merging…', bg='#5B21B6')
        self._draw_bar(0)
        self._status.config(text=f'Merging {len(files)} files…')

        def worker() -> None:
            try:
                def cb(pct: int) -> None:
                    self._root.after(0, lambda p=pct: (
                        self._draw_bar(p),
                        self._status.config(text=f'Merging…  {p}%'),
                    ))
                stats = merge_pdfs(files, out_path, cb)
                self._root.after(0, lambda s=stats: self._on_done(s, None))
            except Exception as exc:
                self._root.after(0, lambda e=exc: self._on_done(None, e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_done(self, stats, error) -> None:
        self._btn.config(state='normal', text='🔗  Merge PDFs', bg=ACCENT)
        if error:
            self._draw_bar(0)
            self._status.config(text='❌  Merge failed')
            messagebox.showerror('Merge Failed', str(error))
        else:
            self._draw_bar(100)
            self._show_results(stats)
            name = Path(stats['output']).name
            self._status.config(
                text=f'✅  Merged {stats["files"]} files  ·  {stats["pages"]} pages  ·  {name}'
            )
            if messagebox.askyesno(
                'Open Merged PDF?',
                f'Merge complete!  {stats["files"]} files · {stats["pages"]} pages\n\n'
                f'Open the merged file?\n\n{name}',
            ):
                open_path(stats['output'])
