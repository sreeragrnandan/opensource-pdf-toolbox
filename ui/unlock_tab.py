"""
ui/unlock_tab.py
Unlock PDF tab UI — drop zone, password entry with show/hide toggle,
output folder picker, action button, and result messaging.
All unlock work runs on a background thread; UI updates use root.after().
"""

import re
import os
import threading
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import filedialog, messagebox

from core import remove_pdf_password, HAS_PIKEPDF, HAS_DND
from core.utils import fmt_bytes, open_path
from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT_H, ACC_LT, SUCCESS, ERROR_C,
    TXT, TXT2, TXT3, FF,
    card, label, progress_bar,
)

try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None


# Teal accent colour used exclusively on this tab so it feels distinct
UNLOCK_ACCENT   = '#0D9488'   # teal-600
UNLOCK_ACCENT_H = '#0F766E'   # teal-700
UNLOCK_LIGHT    = '#5EEAD4'   # teal-300


class UnlockTab:
    """
    Builds and manages the Unlock PDF tab.

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
        self._file:       str = ''
        self._progress    = 0.0
        self._out_mode    = tk.StringVar(value='same')
        self._custom_dir  = ''
        self._show_pw     = False
        self._running     = False

        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_dropzone()
        self._build_password_row()
        self._build_output_row()
        self._build_action_row()
        self._build_result_banner()

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
        self._dz.bind('<Enter>',     lambda _: self._dz.config(highlightbackground=UNLOCK_ACCENT))
        self._dz.bind('<Leave>',     lambda _: self._dz.config(highlightbackground=BORDER))

    def _draw_dz(self) -> None:
        c = self._dz
        c.delete('all')
        W  = c.winfo_width()  or 780
        H  = c.winfo_height() or 140
        cx, cy = W // 2, H // 2

        if self._file:
            c.create_text(cx, cy - 24, text='🔒', font=(FF, 24),
                          fill=UNLOCK_LIGHT, anchor='center')
            c.create_text(cx, cy + 8,
                          text=Path(self._file).name,
                          font=(FF, 13, 'bold'), fill=TXT, anchor='center',
                          width=W - 80)
            c.create_text(cx, cy + 32,
                          text=fmt_bytes(os.path.getsize(self._file)),
                          font=(FF, 9), fill=TXT3, anchor='center')
            c.create_text(cx, cy + 48, text='Click to change file',
                          font=(FF, 9), fill=TXT3, anchor='center')
        else:
            c.create_text(cx, cy - 24, text='🔒', font=(FF, 30),
                          fill=UNLOCK_ACCENT, anchor='center')
            hint = ('Drop a password-protected PDF here  ·  or  ·  Click to Browse'
                    if HAS_DND else 'Click to Browse a PDF File')
            c.create_text(cx, cy + 8, text=hint,
                          font=(FF, 13, 'bold'), fill=TXT, anchor='center')
            c.create_text(cx, cy + 30,
                          text='The password will be removed and a new file saved',
                          font=(FF, 9), fill=TXT3, anchor='center')

    def setup_dnd(self) -> None:
        """Register drag-and-drop on the drop zone (called by App after init)."""
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
            self._file = pdfs[0]   # only one file for unlock
            self._draw_dz()
            self._clear_result()

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title='Select a password-protected PDF',
            filetypes=[('PDF files', '*.pdf'), ('All files', '*.*')],
        )
        if path:
            self._file = path
            self._draw_dz()
            self._clear_result()

    # ── Password row ──────────────────────────────────────────────────────────

    def _build_password_row(self) -> None:
        outer = tk.Frame(self._parent, bg=BG)
        outer.pack(fill='x', padx=28, pady=(14, 0))

        label(outer, 'PDF Password', bold=True).pack(anchor='w', pady=(0, 6))

        c = card(outer)
        c.pack(fill='x')
        inner = tk.Frame(c, bg=CARD)
        inner.pack(fill='x', padx=16, pady=14)

        # Entry + show/hide side by side
        entry_row = tk.Frame(inner, bg=CARD)
        entry_row.pack(fill='x')

        ef = tk.Frame(entry_row, bg=CARD,
                      highlightthickness=1, highlightbackground=BORDER)
        ef.pack(side='left', fill='x', expand=True)

        self._pw_entry = tk.Entry(
            ef, show='●', font=(FF, 12),
            bg=SURFACE, fg=TXT, insertbackground=TXT,
            bd=0, relief='flat',
        )
        self._pw_entry.pack(fill='x', padx=10, pady=8)

        self._eye_btn = tk.Button(
            entry_row,
            text='👁',
            font=(FF, 11),
            bg=CARD, fg=TXT2,
            activebackground=BORDER, activeforeground=TXT,
            bd=0, relief='flat', cursor='hand2',
            padx=10, pady=6,
            command=self._toggle_pw_visibility,
        )
        self._eye_btn.pack(side='left', padx=(6, 0))

        tk.Label(inner, text='Enter the password used to open or protect the PDF.',
                 font=(FF, 8), bg=CARD, fg=TXT3).pack(anchor='w', pady=(6, 0))

    def _toggle_pw_visibility(self) -> None:
        self._show_pw = not self._show_pw
        self._pw_entry.config(show='' if self._show_pw else '●')
        self._eye_btn.config(text=('🙈' if self._show_pw else '👁'))

    # ── Output row ────────────────────────────────────────────────────────────

    def _build_output_row(self) -> None:
        outer = tk.Frame(self._parent, bg=BG)
        outer.pack(fill='x', padx=28, pady=(14, 0))

        label(outer, 'Output Folder', bold=True).pack(anchor='w', pady=(0, 6))

        c = card(outer)
        c.pack(fill='x')
        inner = tk.Frame(c, bg=CARD)
        inner.pack(fill='x', padx=16, pady=12)

        def radio(text: str, value: str) -> tk.Radiobutton:
            return tk.Radiobutton(
                inner, text=text,
                variable=self._out_mode, value=value,
                font=(FF, 10), bg=CARD, fg=TXT,
                selectcolor=CARD, activebackground=CARD,
                cursor='hand2', bd=0, relief='flat',
                command=self._toggle_out_entry,
            )

        radio('Same folder as source', 'same').pack(anchor='w')
        radio('Choose folder…',        'custom').pack(anchor='w', pady=(5, 0))

        ef = tk.Frame(inner, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        ef.pack(fill='x', pady=(8, 0))
        self._out_entry = tk.Entry(
            ef, font=(FF, 9), bg=SURFACE, fg=TXT2,
            insertbackground=TXT, bd=0, relief='flat', state='disabled',
        )
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
        return str(Path(base) / f'{stem}_unlocked.pdf')

    # ── Action row ────────────────────────────────────────────────────────────

    def _build_action_row(self) -> None:
        row = tk.Frame(self._parent, bg=BG)
        row.pack(fill='x', padx=28, pady=(14, 0))

        self._btn = tk.Button(
            row, text='🔓  Remove Password',
            font=(FF, 12, 'bold'),
            bg=UNLOCK_ACCENT, fg='white',
            activebackground=UNLOCK_ACCENT_H, activeforeground='white',
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
        # Use teal colour for this tab's progress bar
        self._bar.delete('all')
        W = self._bar.winfo_width() or 400
        self._bar.create_rectangle(0, 0, W, 6, fill=BORDER, outline='')
        if pct > 0:
            self._bar.create_rectangle(0, 0, int(W * pct / 100), 6,
                                       fill=UNLOCK_ACCENT, outline='')

    # ── Result banner ─────────────────────────────────────────────────────────

    def _build_result_banner(self) -> None:
        outer = tk.Frame(self._parent, bg=BG)
        outer.pack(fill='x', padx=28, pady=(12, 20))
        self._res_card = card(outer)

        inner = tk.Frame(self._res_card, bg=CARD)
        inner.pack(fill='x', padx=20, pady=14)

        self._res_icon  = tk.Label(inner, text='', font=(FF, 28),
                                   bg=CARD, fg=SUCCESS)
        self._res_icon.pack(side='left', padx=(0, 14))

        txt_col = tk.Frame(inner, bg=CARD)
        txt_col.pack(side='left', fill='x', expand=True)

        self._res_title = tk.Label(txt_col, text='', font=(FF, 13, 'bold'),
                                   bg=CARD, fg=TXT, anchor='w')
        self._res_title.pack(anchor='w')

        self._res_sub = tk.Label(txt_col, text='', font=(FF, 9),
                                 bg=CARD, fg=TXT3, anchor='w')
        self._res_sub.pack(anchor='w')

    def _clear_result(self) -> None:
        self._res_card.pack_forget()
        self._draw_bar(0)
        self._status.config(text='')

    def _show_result(self, success: bool, title: str, sub: str) -> None:
        self._res_icon.config(
            text=('✅' if success else '❌'),
            fg=(SUCCESS if success else ERROR_C),
        )
        self._res_title.config(text=title, fg=(TXT if success else ERROR_C))
        self._res_sub.config(text=sub)
        self._res_card.pack(fill='x')

    # ── Unlock runner (background thread) ────────────────────────────────────

    def _start(self) -> None:
        if not self._file:
            messagebox.showwarning('No File', 'Please select a password-protected PDF first.')
            return
        if not HAS_PIKEPDF:
            messagebox.showerror('Missing Library',
                                 'pikepdf is not installed.\nRun: pip install pikepdf')
            return
        if self._running:
            return

        password = self._pw_entry.get()
        out_path = self._resolve_output(self._file)
        fpath    = self._file

        self._running = True
        self._btn.config(state='disabled', text='Unlocking…',
                         bg=UNLOCK_ACCENT_H)
        self._clear_result()
        self._draw_bar(0)
        self._status.config(text='Opening encrypted PDF…')

        # Animate the progress bar while the background thread works
        self._animate_progress(0)

        def worker() -> None:
            try:
                result = remove_pdf_password(fpath, out_path, password)
                self._root.after(0, lambda: self._on_done(result, None))
            except Exception as exc:
                self._root.after(0, lambda e=exc: self._on_done(None, e))

        threading.Thread(target=worker, daemon=True).start()

    def _animate_progress(self, pct: float) -> None:
        """Smoothly advance the bar while work is in progress (stops at 90)."""
        if not self._running:
            return
        target = min(pct + 3, 90)
        self._draw_bar(target)
        if target < 90:
            self._root.after(80, lambda: self._animate_progress(target))

    def _on_done(self, result: Optional[dict], error: Optional[Exception]) -> None:
        self._running = False
        self._btn.config(state='normal', text='🔓  Remove Password',
                         bg=UNLOCK_ACCENT)

        if result:
            out = result['output']
            self._draw_bar(100)
            self._status.config(text='✅  Password removed successfully!')
            self._show_result(
                success=True,
                title='Password removed successfully!',
                sub=f'Saved as: {Path(out).name}   ({fmt_bytes(os.path.getsize(out))})',
            )
            if messagebox.askyesno(
                'Open File?',
                f'The unlocked PDF has been saved.\n\nOpen it now?\n\n{Path(out).name}',
            ):
                open_path(out)
        else:
            self._draw_bar(0)
            # Provide a friendly message for the most common error
            err_str = str(error)
            if 'password' in err_str.lower() or 'PasswordError' in type(error).__name__:
                msg = 'Incorrect password. Please check the password and try again.'
            elif 'not encrypted' in err_str.lower():
                msg = 'This PDF is not password-protected — nothing to unlock!'
            else:
                msg = f'Could not unlock the PDF:\n{err_str}'

            self._status.config(text='⚠️  Unlock failed')
            self._show_result(
                success=False,
                title='Unlock failed',
                sub=msg,
            )
