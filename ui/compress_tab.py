"""
ui/compress_tab.py
Compress tab UI — drop zone, preset selector, output folder picker,
progress bar, and results panel. All compression work runs on a
background thread; UI updates are scheduled via root.after().
"""

import re
import os
import threading
from pathlib import Path
from typing import List
import tkinter as tk
from tkinter import filedialog, messagebox

from core import compress_pdf, PRESETS, HAS_PIKEPDF, HAS_DND
from core.utils import fmt_bytes, open_path
from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT_H, ACC_LT, SUCCESS,
    TXT, TXT2, TXT3, FF,
    card, label, progress_bar, stat_cell,
)

try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None


class CompressTab:
    """
    Builds and manages the Compress tab.

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
        self._preset_var  = tk.StringVar(value='medium')
        self._out_mode    = tk.StringVar(value='same')
        self._custom_dir  = ''
        self._res_visible = False

        self._build()
        if HAS_DND:
            self._setup_dnd()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_dropzone()
        self._build_middle()
        self._build_action_row()
        self._build_results()

    # ── Drop zone ─────────────────────────────────────────────────────────────

    def _build_dropzone(self) -> None:
        outer = tk.Frame(self._parent, bg=BG)
        outer.pack(fill='x', padx=28, pady=(14, 0))

        self._dz = tk.Canvas(outer, height=140, bg=SURFACE,
                              highlightthickness=2, highlightbackground=BORDER,
                              cursor='hand2', bd=0)
        self._dz.pack(fill='x')
        self._dz.bind('<Configure>', lambda _: self._draw_dz())
        self._dz.bind('<Button-1>',  lambda _: self._browse())
        self._dz.bind('<Enter>',     lambda _: self._dz.config(highlightbackground=ACCENT))
        self._dz.bind('<Leave>',     lambda _: self._dz.config(highlightbackground=BORDER))

    def _draw_dz(self) -> None:
        c = self._dz
        c.delete('all')
        W  = c.winfo_width()  or 780
        H  = c.winfo_height() or 140
        cx, cy = W // 2, H // 2

        if self.files:
            c.create_text(cx, cy - 24, text='📂', font=(FF, 24), fill=ACC_LT, anchor='center')
            n = len(self.files)
            c.create_text(cx, cy + 8, text=f'{n} file{"s" if n > 1 else ""} selected',
                          font=(FF, 13, 'bold'), fill=TXT, anchor='center')
            preview = ', '.join(Path(f).name for f in self.files[:3])
            if n > 3:
                preview += f' +{n - 3} more'
            c.create_text(cx, cy + 30, text=preview, font=(FF, 9), fill=TXT3,
                          anchor='center', width=W - 80)
            c.create_text(cx, cy + 48, text='Click to change selection',
                          font=(FF, 9), fill=TXT3, anchor='center')
        else:
            c.create_text(cx, cy - 24, text='⬆', font=(FF, 30), fill=ACCENT, anchor='center')
            hint = ('Drop PDF files here  ·  or  ·  Click to Browse'
                    if HAS_DND else 'Click to Browse PDF Files')
            c.create_text(cx, cy + 8, text=hint, font=(FF, 13, 'bold'),
                          fill=TXT, anchor='center')
            c.create_text(cx, cy + 30,
                          text='Supports single files and batch compression',
                          font=(FF, 9), fill=TXT3, anchor='center')

    def _setup_dnd(self) -> None:
        try:
            self._dz.drop_target_register(DND_FILES)
            self._dz.dnd_bind('<<Drop>>', self._on_drop)
        except Exception:
            pass

    def _on_drop(self, event) -> None:
        parts = re.findall(r'\{([^}]+)\}|(\S+)', event.data)
        paths = [a or b for a, b in parts]
        pdfs  = [p for p in paths if p.lower().endswith('.pdf') and os.path.isfile(p)]
        if pdfs:
            self.files = pdfs
            self._draw_dz()
            self._clear_results()

    def _browse(self) -> None:
        paths = filedialog.askopenfilenames(
            title='Select PDF files to compress',
            filetypes=[('PDF files', '*.pdf'), ('All files', '*.*')],
        )
        if paths:
            self.files = list(paths)
            self._draw_dz()
            self._clear_results()

    # ── Middle row (presets + output) ─────────────────────────────────────────

    def _build_middle(self) -> None:
        row = tk.Frame(self._parent, bg=BG)
        row.pack(fill='x', padx=28, pady=(12, 0))
        row.columnconfigure(0, weight=3)
        row.columnconfigure(1, weight=2)
        self._build_presets(row)
        self._build_output(row)

    def _build_presets(self, parent: tk.Widget) -> None:
        col = tk.Frame(parent, bg=BG)
        col.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        label(col, 'Compression Level', bold=True).pack(anchor='w', pady=(0, 6))

        c = card(col)
        c.pack(fill='x')
        for key, preset in PRESETS.items():
            row = tk.Frame(c, bg=CARD)
            row.pack(fill='x', padx=16, pady=5)
            tk.Radiobutton(
                row, text=preset['label'],
                variable=self._preset_var, value=key,
                font=(FF, 10, 'bold'), bg=CARD, fg=TXT,
                selectcolor=CARD, activebackground=CARD,
                activeforeground=ACC_LT, cursor='hand2', bd=0, relief='flat',
            ).pack(side='left')
            tk.Label(row, text=f'— {preset["desc"].split(".")[0]}.',
                     font=(FF, 8), bg=CARD, fg=TXT3).pack(side='left', padx=(8, 0))

    def _build_output(self, parent: tk.Widget) -> None:
        col = tk.Frame(parent, bg=BG)
        col.grid(row=0, column=1, sticky='nsew')
        label(col, 'Output Folder', bold=True).pack(anchor='w', pady=(0, 6))

        c = card(col)
        c.pack(fill='both', expand=True)
        inner = tk.Frame(c, bg=CARD)
        inner.pack(fill='both', padx=16, pady=12)

        def radio(text: str, value: str) -> tk.Radiobutton:
            return tk.Radiobutton(inner, text=text,
                                   variable=self._out_mode, value=value,
                                   font=(FF, 10), bg=CARD, fg=TXT,
                                   selectcolor=CARD, activebackground=CARD,
                                   cursor='hand2', bd=0, relief='flat',
                                   command=self._toggle_out_entry)

        radio('Same folder as source', 'same').pack(anchor='w')
        radio('Choose folder…',        'custom').pack(anchor='w', pady=(5, 0))

        ef = tk.Frame(inner, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        ef.pack(fill='x', pady=(8, 0))
        self._out_entry = tk.Entry(ef, font=(FF, 9), bg=SURFACE, fg=TXT2,
                                    insertbackground=TXT, bd=0, relief='flat',
                                    state='disabled')
        self._out_entry.pack(fill='x', padx=8, pady=5)

        self._out_browse_btn = tk.Button(
            inner, text='Browse folder…', font=(FF, 9),
            bg=BORDER, fg=TXT2, activebackground=SURFACE, activeforeground=TXT,
            bd=0, relief='flat', cursor='hand2', padx=10, pady=4,
            command=self._browse_output, state='disabled',
        )
        self._out_browse_btn.pack(anchor='w', pady=(6, 0))

    def _toggle_out_entry(self) -> None:
        custom = self._out_mode.get() == 'custom'
        state  = 'normal' if custom else 'disabled'
        self._out_entry.config(state=state)
        self._out_browse_btn.config(state=state)
        if custom and self._custom_dir:
            self._out_entry.delete(0, 'end')
            self._out_entry.insert(0, self._custom_dir)

    def _browse_output(self) -> None:
        d = filedialog.askdirectory(title='Select output folder')
        if d:
            self._custom_dir = d
            self._out_entry.delete(0, 'end')
            self._out_entry.insert(0, d)

    def _resolve_output(self, source: str) -> str:
        stem = Path(source).stem
        base = (self._custom_dir
                if self._out_mode.get() == 'custom' and self._custom_dir
                else str(Path(source).parent))
        return str(Path(base) / f'{stem}_compressed.pdf')

    # ── Action row ────────────────────────────────────────────────────────────

    def _build_action_row(self) -> None:
        row = tk.Frame(self._parent, bg=BG)
        row.pack(fill='x', padx=28, pady=(14, 0))

        self._btn = tk.Button(
            row, text='⚡  Compress PDF',
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
        inner.columnconfigure((0, 1, 2, 3), weight=1)

        self._r_orig  = stat_cell(inner, 0, 'ORIGINAL',   TXT2)
        self._r_comp  = stat_cell(inner, 1, 'COMPRESSED', TXT2)
        self._r_saved = stat_cell(inner, 2, 'SAVED',       SUCCESS)
        self._r_pct   = stat_cell(inner, 3, 'REDUCTION',   ACC_LT)

    def _clear_results(self) -> None:
        self._res_card.pack_forget()
        self._res_visible = False
        self._draw_bar(0)
        self._status.config(text='')

    def _show_results(self, stats_list: List[dict]) -> None:
        orig  = sum(s['original']   for s in stats_list)
        comp  = sum(s['compressed'] for s in stats_list)
        saved = orig - comp
        pct   = saved / orig * 100 if orig else 0.0

        self._r_orig.config(text=fmt_bytes(orig))
        self._r_comp.config(text=fmt_bytes(comp))
        self._r_saved.config(text=fmt_bytes(max(0, saved)))
        self._r_pct.config(text=f'{max(0.0, pct):.1f}%')

        if not self._res_visible:
            self._res_card.pack(fill='x')
            self._res_visible = True

    # ── Compression runner (background thread) ────────────────────────────────

    def _start(self) -> None:
        if not self.files:
            messagebox.showwarning('No Files', 'Please select at least one PDF file first.')
            return
        if not HAS_PIKEPDF:
            messagebox.showerror('Missing Library',
                                  'pikepdf is not installed.\nRun: pip install pikepdf Pillow')
            return

        self._btn.config(state='disabled', text='Compressing…', bg='#5B21B6')
        self._draw_bar(0)
        self._status.config(text='Starting…')

        preset_key = self._preset_var.get()
        files      = list(self.files)

        def worker() -> None:
            results: List[dict] = []
            errors:  List[str]  = []
            total = len(files)

            for idx, fpath in enumerate(files):
                out = self._resolve_output(fpath)

                def cb(pct: int, _idx: int = idx, _total: int = total) -> None:
                    overall = int((_idx + pct / 100) / _total * 100)
                    name    = Path(files[_idx]).name
                    self._root.after(
                        0, lambda p=overall, n=name, i=_idx:
                        self._on_progress(p, n, i, _total)
                    )

                try:
                    results.append(compress_pdf(fpath, out, preset_key, cb))
                except Exception as exc:
                    errors.append(f'{Path(fpath).name}: {exc}')

            self._root.after(0, lambda: self._on_done(results, errors))

        threading.Thread(target=worker, daemon=True).start()

    def _on_progress(self, pct: int, name: str, idx: int, total: int) -> None:
        self._draw_bar(pct)
        self._status.config(text=f'[{idx + 1}/{total}]  {name}   {pct}%')

    def _on_done(self, results: List[dict], errors: List[str]) -> None:
        self._btn.config(state='normal', text='⚡  Compress PDF', bg=ACCENT)
        self._draw_bar(100)

        n = len(results)
        if n:
            self._show_results(results)
            self._status.config(
                text=f'✅  {n} file{"s" if n > 1 else ""} compressed successfully!')

            if n == 1:
                out = results[0].get('output', '')
                if out and messagebox.askyesno(
                    'Open PDF?',
                    f'Compression complete!\n\nOpen the compressed file?\n\n{Path(out).name}',
                ):
                    open_path(out)
            else:
                out_dir = str(Path(results[0].get('output', '')).parent)
                if out_dir and messagebox.askyesno(
                    'Open Output Folder?',
                    f'{n} files compressed successfully!\n\nOpen the output folder?',
                ):
                    open_path(out_dir)

        if errors:
            self._status.config(text=f'⚠️  Done with {len(errors)} error(s)')
            messagebox.showerror('Compression Errors', '\n'.join(errors))
