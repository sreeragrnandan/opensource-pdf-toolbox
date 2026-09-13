"""
ui/rearrange_tab.py
Rearrange & Delete Pages tab UI — interactive visual page grid with reordering,
deletion, thumbnail previews, and instant default-viewer launch.
"""

import os
import re
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
import tkinter as tk
from tkinter import filedialog, messagebox

from core import (
    HAS_PIKEPDF, HAS_PIL, HAS_DND, HAS_FITZ,
    fmt_bytes, open_path,
    get_pdf_info, render_page_thumbnail, save_rearranged_pdf,
)
from core.dependencies import DND_FILES
from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT_H, ACC_LT, SUCCESS, ERROR_C,
    TXT, TXT2, TXT3, FF,
    card, label, progress_bar,
)

# Pillow ImageTk import (safe fallback)
try:
    from PIL import ImageTk
except ImportError:
    ImageTk = None


class RearrangeTab:
    """
    Builds and manages the Rearrange & Delete Pages tab.

    Parameters
    ----------
    parent : tk.Frame
        The frame allocated for this tab by the parent App.
    root : tk.Tk
        The root window (needed for .after() thread-safe callbacks).
    """

    CARD_W = 140
    CARD_H = 190
    THUMB_MAX_W = 110
    THUMB_MAX_H = 115

    def __init__(self, parent: tk.Frame, root: tk.Tk) -> None:
        self._parent = parent
        self._root   = root

        # ── State ─────────────────────────────────────────────────────────────
        self.current_pdf: Optional[str] = None
        self.total_orig_pages: int = 0
        self.orig_file_size: int = 0

        # List of 0-based page indices currently retained, in display order
        self.page_order: List[int] = []
        self.selected_idx: Optional[int] = None

        # Thumbnail cache: orig_page_index -> ImageTk.PhotoImage
        self._thumb_cache: Dict[int, Any] = {}
        self._thumb_loading = False

        # Card widgets: list of dicts with widget references
        self._card_widgets: List[dict] = []

        self._progress = 0.0
        self._cols = 4

        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_top_bar()
        self._build_toolbar()
        self._build_grid_area()
        self._build_output_and_action()

    # ── Top bar: file info or drop prompt ─────────────────────────────────────

    def _build_top_bar(self) -> None:
        self._top_outer = tk.Frame(self._parent, bg=BG)
        self._top_outer.pack(fill='x', padx=28, pady=(12, 0))

        # Drop/Browse card when no file is loaded
        self._drop_card = tk.Frame(
            self._top_outer, bg=SURFACE,
            highlightthickness=2, highlightbackground=BORDER,
            cursor='hand2',
        )
        self._drop_card.pack(fill='x', ipady=12)
        self._drop_card.bind('<Button-1>', lambda _: self._browse_file())
        self._drop_card.bind('<Enter>', lambda _: self._drop_card.config(highlightbackground=ACCENT))
        self._drop_card.bind('<Leave>', lambda _: self._drop_card.config(highlightbackground=BORDER))

        tk.Label(self._drop_card, text='📄', font=(FF, 22), bg=SURFACE, fg=ACC_LT).pack(pady=(4, 2))
        tk.Label(
            self._drop_card,
            text='Click to select or drop a PDF file to rearrange and delete pages',
            font=(FF, 11, 'bold'), bg=SURFACE, fg=TXT,
        ).pack()
        tk.Label(
            self._drop_card,
            text='Visually reorder pages, remove unwanted pages, and export your new PDF',
            font=(FF, 9), bg=SURFACE, fg=TXT3,
        ).pack(pady=(2, 4))

        # Loaded file banner (hidden until file is loaded)
        self._banner = card(self._top_outer)
        self._banner_label = tk.Label(
            self._banner, text='', font=(FF, 10, 'bold'),
            bg=CARD, fg=TXT, anchor='w',
        )
        self._banner_label.pack(side='left', padx=14, pady=10)

        self._banner_sub = tk.Label(
            self._banner, text='', font=(FF, 9),
            bg=CARD, fg=TXT2, anchor='w',
        )
        self._banner_sub.pack(side='left', padx=(0, 14), pady=10)

        change_btn = tk.Button(
            self._banner, text='↺  Change File',
            font=(FF, 9), bg=BORDER, fg=TXT2,
            activebackground=SURFACE, activeforeground=TXT,
            bd=0, relief='flat', cursor='hand2',
            padx=12, pady=5, command=self._browse_file,
        )
        change_btn.pack(side='right', padx=14, pady=10)

    # ── Action toolbar ────────────────────────────────────────────────────────

    def _build_toolbar(self) -> None:
        self._tb_outer = tk.Frame(self._parent, bg=BG)
        self._tb_outer.pack(fill='x', padx=28, pady=(10, 6))

        def tb_btn(text: str, cmd, bg: str = BORDER, fg: str = TXT2, **kw) -> tk.Button:
            return tk.Button(
                self._tb_outer, text=text, font=(FF, 9),
                bg=bg, fg=fg, activebackground=SURFACE, activeforeground=TXT,
                bd=0, relief='flat', cursor='hand2',
                padx=10, pady=5, command=cmd, **kw,
            )

        self._btn_first = tb_btn('⏮  First', self._move_to_first)
        self._btn_first.pack(side='left', padx=(0, 4))

        self._btn_left  = tb_btn('◀  Move Left', self._move_left)
        self._btn_left.pack(side='left', padx=(0, 4))

        self._btn_right = tb_btn('▶  Move Right', self._move_right)
        self._btn_right.pack(side='left', padx=(0, 4))

        self._btn_last  = tb_btn('⏭  Last', self._move_to_last)
        self._btn_last.pack(side='left', padx=(0, 8))

        self._btn_del   = tb_btn('✕  Delete Page', self._delete_selected, bg='#3B1824', fg=ERROR_C)
        self._btn_del.pack(side='left', padx=(0, 8))

        self._btn_reset = tb_btn('↺  Reset Order', self._reset_order)
        self._btn_reset.pack(side='left')

        # Status badge on the right
        self._counter_label = tk.Label(
            self._tb_outer, text='No file loaded',
            font=(FF, 9), bg=BG, fg=TXT3,
        )
        self._counter_label.pack(side='right', pady=4)

    # ── Scrollable Grid Canvas ────────────────────────────────────────────────

    def _build_grid_area(self) -> None:
        outer = tk.Frame(self._parent, bg=BG)
        outer.pack(fill='both', expand=True, padx=28, pady=(4, 0))

        c_frame = card(outer)
        c_frame.pack(fill='both', expand=True)

        self._canvas = tk.Canvas(
            c_frame, bg=CARD, bd=0, highlightthickness=0,
        )
        self._canvas.pack(side='left', fill='both', expand=True)

        self._sb = tk.Scrollbar(
            c_frame, orient='vertical', command=self._canvas.yview,
            bg=SURFACE, troughcolor=SURFACE, activebackground=BORDER,
            bd=0, relief='flat', highlightthickness=0,
        )
        self._sb.pack(side='right', fill='y', pady=4, padx=(0, 2))
        self._canvas.configure(yscrollcommand=self._sb.set)

        self._inner_grid = tk.Frame(self._canvas, bg=CARD)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._inner_grid, anchor='nw',
        )

        self._inner_grid.bind('<Configure>', self._on_inner_configure)
        self._canvas.bind('<Configure>', self._on_canvas_configure)

        # Mousewheel scroll support
        self._canvas.bind_all('<MouseWheel>', self._on_mousewheel)

        # Empty state prompt
        self._empty_label = tk.Label(
            self._canvas,
            text='No PDF loaded.\n\nOpen a PDF above to view and rearrange pages.',
            font=(FF, 11), bg=CARD, fg=TXT3, justify='center',
        )
        self._empty_label.place(relx=0.5, rely=0.5, anchor='center')

    def _on_mousewheel(self, event) -> None:
        # Only scroll if this tab's canvas is visible and has scrollable content
        if self._canvas.winfo_ismapped():
            try:
                self._canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
            except Exception:
                pass

    def _on_inner_configure(self, _) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    def _on_canvas_configure(self, event) -> None:
        # Expand inner grid width to fill canvas
        canvas_w = event.width
        self._canvas.itemconfig(self._canvas_window, width=canvas_w)
        # Recalculate columns
        new_cols = max(1, canvas_w // (self.CARD_W + 16))
        if new_cols != self._cols and self.page_order:
            self._cols = new_cols
            self._relayout_cards()

    # ── Bottom controls: output file & save action ────────────────────────────

    def _build_output_and_action(self) -> None:
        outer = tk.Frame(self._parent, bg=BG)
        outer.pack(fill='x', padx=28, pady=(10, 14))

        # Destination file picker row
        dest_row = tk.Frame(outer, bg=BG)
        dest_row.pack(fill='x', pady=(0, 8))

        label(dest_row, 'Save As:', bold=True, size=10).pack(side='left', padx=(0, 8))

        ef = tk.Frame(dest_row, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        ef.pack(side='left', fill='x', expand=True)

        self._out_entry = tk.Entry(
            ef, font=(FF, 10), bg=CARD, fg=TXT,
            insertbackground=TXT, bd=0, relief='flat',
        )
        self._out_entry.pack(fill='x', padx=10, pady=6)
        self._out_entry.insert(0, 'rearranged_output.pdf')

        browse_out_btn = tk.Button(
            dest_row, text='Browse…', font=(FF, 9),
            bg=BORDER, fg=TXT2, activebackground=SURFACE, activeforeground=TXT,
            bd=0, relief='flat', cursor='hand2', padx=12, pady=5,
            command=self._browse_save_location,
        )
        browse_out_btn.pack(side='right', padx=(8, 0))

        # Action button and progress
        act_row = tk.Frame(outer, bg=BG)
        act_row.pack(fill='x')

        self._save_btn = tk.Button(
            act_row, text='📑  Save Rearranged PDF',
            font=(FF, 11, 'bold'), bg=ACCENT, fg='white',
            activebackground=ACCENT_H, activeforeground='white',
            bd=0, relief='flat', cursor='hand2',
            padx=20, pady=8, command=self._start_save,
        )
        self._save_btn.pack(side='left', padx=(0, 14))

        prog_col = tk.Frame(act_row, bg=BG)
        prog_col.pack(side='left', fill='x', expand=True)

        self._bar = tk.Canvas(prog_col, height=6, bg=BORDER, bd=0, highlightthickness=0)
        self._bar.pack(fill='x', pady=(6, 4))
        self._bar.bind('<Configure>', lambda _: progress_bar(self._bar, self._progress))

        self._status = tk.Label(
            prog_col, text='Ready', font=(FF, 9), bg=BG, fg=TXT3, anchor='w',
        )
        self._status.pack(anchor='w')

    # ── Drag and Drop Setup ───────────────────────────────────────────────────

    def setup_dnd(self) -> None:
        """Register DND drop targets on drop zone and canvas."""
        if not HAS_DND:
            return
        for target in (self._drop_card, self._canvas):
            try:
                target.drop_target_register(DND_FILES)
                target.dnd_bind('<<Drop>>', self._on_drop)
            except Exception:
                pass

    def _on_drop(self, event) -> None:
        parts = re.findall(r'\{([^}]+)\}|(\S+)', event.data)
        paths = [a or b for a, b in parts]
        pdfs  = [p for p in paths if p.lower().endswith('.pdf') and os.path.isfile(p)]
        if pdfs:
            self._load_file(pdfs[0])

    # ── File loading & Thumbnails ─────────────────────────────────────────────

    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(
            title='Select PDF file to rearrange & delete pages',
            filetypes=[('PDF files', '*.pdf'), ('All files', '*.*')],
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str) -> None:
        try:
            info = get_pdf_info(path)
        except Exception as err:
            messagebox.showerror('Error Opening PDF', f'Could not read PDF:\n{err}')
            return

        self.current_pdf = path
        self.total_orig_pages = info['page_count']
        self.orig_file_size = info['file_size']
        self.page_order = list(range(self.total_orig_pages))
        self.selected_idx = 0 if self.total_orig_pages > 0 else None
        self._thumb_cache.clear()

        # Update banners
        p = Path(path)
        self._drop_card.pack_forget()
        self._banner_label.config(text=p.name)
        self._banner_sub.config(
            text=f'·  {self.total_orig_pages} pages  ·  {fmt_bytes(self.orig_file_size)}'
        )
        self._banner.pack(fill='x')

        # Suggest output name in same folder
        out_suggest = str(p.parent / f'{p.stem}_modified.pdf')
        self._out_entry.delete(0, 'end')
        self._out_entry.insert(0, out_suggest)

        self._empty_label.place_forget()
        self._update_counter()
        self._rebuild_cards()

        # Trigger background thumbnail renderer
        self._start_thumbnail_rendering(path)

    def _start_thumbnail_rendering(self, path: str) -> None:
        if not (HAS_FITZ and HAS_PIL and ImageTk):
            return

        def worker():
            for orig_idx in range(self.total_orig_pages):
                if self.current_pdf != path:
                    break  # file changed
                if orig_idx in self._thumb_cache:
                    continue
                pil_img = render_page_thumbnail(
                    path, orig_idx, self.THUMB_MAX_W, self.THUMB_MAX_H
                )
                if pil_img:
                    self._root.after(0, self._store_thumbnail, orig_idx, pil_img)

        threading.Thread(target=worker, daemon=True).start()

    def _store_thumbnail(self, orig_idx: int, pil_img) -> None:
        if not ImageTk:
            return
        try:
            photo = ImageTk.PhotoImage(pil_img)
            self._thumb_cache[orig_idx] = photo
            # Update any displayed card that uses this thumbnail
            for card_info in self._card_widgets:
                if card_info['orig_idx'] == orig_idx:
                    card_info['thumb_label'].config(image=photo, text='')
                    card_info['thumb_label'].image = photo
        except Exception:
            pass

    # ── Cards Building & Layout ───────────────────────────────────────────────

    def _rebuild_cards(self) -> None:
        # Clear existing card widgets
        for c in self._inner_grid.winfo_children():
            c.destroy()
        self._card_widgets.clear()

        if not self.page_order:
            self._empty_label.place(relx=0.5, rely=0.5, anchor='center')
            self._update_counter()
            return

        self._empty_label.place_forget()

        # Build card widgets for each item in self.page_order
        for pos, orig_idx in enumerate(self.page_order):
            w = self._create_card(pos, orig_idx)
            self._card_widgets.append(w)

        self._relayout_cards()
        self._update_selection_highlight()
        self._update_counter()

    def _create_card(self, pos: int, orig_idx: int) -> dict:
        is_sel = (pos == self.selected_idx)
        border_color = ACCENT if is_sel else BORDER
        bw = 2 if is_sel else 1

        card_frame = tk.Frame(
            self._inner_grid, bg=CARD,
            width=self.CARD_W, height=self.CARD_H,
            highlightthickness=bw, highlightbackground=border_color,
            cursor='hand2',
        )
        card_frame.pack_propagate(False)

        # Header row inside card: position & orig reference
        hdr = tk.Frame(card_frame, bg=CARD)
        hdr.pack(fill='x', padx=8, pady=(6, 2))

        pos_lbl = tk.Label(
            hdr, text=f'Page {pos + 1}',
            font=(FF, 9, 'bold'), bg=CARD, fg=TXT,
        )
        pos_lbl.pack(side='left')

        orig_lbl = tk.Label(
            hdr, text=f'#{orig_idx + 1}',
            font=(FF, 8), bg=CARD, fg=TXT3,
        )
        orig_lbl.pack(side='right')

        # Thumbnail area
        thumb_frame = tk.Frame(
            card_frame, bg=SURFACE,
            width=self.THUMB_MAX_W + 6, height=self.THUMB_MAX_H + 6,
        )
        thumb_frame.pack_propagate(False)
        thumb_frame.pack(pady=3)

        thumb_lbl = tk.Label(thumb_frame, bg=SURFACE, fg=TXT3, font=(FF, 9))
        thumb_lbl.pack(fill='both', expand=True)

        if orig_idx in self._thumb_cache:
            photo = self._thumb_cache[orig_idx]
            thumb_lbl.config(image=photo, text='')
            thumb_lbl.image = photo
        else:
            thumb_lbl.config(text=f'📄\n\nPage {orig_idx + 1}')

        # Footer row: move left, delete, move right
        ftr = tk.Frame(card_frame, bg=CARD)
        ftr.pack(fill='x', padx=6, pady=(4, 6))

        def mini_btn(text: str, cmd, fg: str = TXT2, bg_col: str = SURFACE) -> tk.Button:
            return tk.Button(
                ftr, text=text, font=(FF, 8, 'bold'),
                bg=bg_col, fg=fg, activebackground=BORDER, activeforeground=TXT,
                bd=0, relief='flat', cursor='hand2', padx=4, pady=2, command=cmd,
            )

        btn_l = mini_btn('◀', lambda p=pos: self._move_page_left(p))
        btn_l.pack(side='left', expand=True, fill='x', padx=(0, 2))

        btn_d = mini_btn('✕', lambda p=pos: self._delete_page(p), fg=ERROR_C)
        btn_d.pack(side='left', expand=True, fill='x', padx=2)

        btn_r = mini_btn('▶', lambda p=pos: self._move_page_right(p))
        btn_r.pack(side='left', expand=True, fill='x', padx=(2, 0))

        card_info = {
            'frame': card_frame,
            'pos_lbl': pos_lbl,
            'orig_lbl': orig_lbl,
            'thumb_label': thumb_lbl,
            'orig_idx': orig_idx,
            'btn_l': btn_l,
            'btn_d': btn_d,
            'btn_r': btn_r,
        }

        # Click on card or any child to select
        def on_click(event, p=pos):
            self._select_page(p)

        for widget in (card_frame, hdr, pos_lbl, orig_lbl, thumb_frame, thumb_lbl, ftr):
            widget.bind('<Button-1>', on_click)

        return card_info

    def _relayout_cards(self) -> None:
        cols = self._cols
        for i, card_info in enumerate(self._card_widgets):
            row = i // cols
            col = i % cols
            card_info['frame'].grid(
                row=row, column=col, padx=8, pady=8, sticky='nw',
            )

    def _update_selection_highlight(self) -> None:
        for i, card_info in enumerate(self._card_widgets):
            is_sel = (i == self.selected_idx)
            bw = 2 if is_sel else 1
            bc = ACCENT if is_sel else BORDER
            card_info['frame'].config(highlightthickness=bw, highlightbackground=bc)

    def _select_page(self, pos: int) -> None:
        if 0 <= pos < len(self.page_order):
            self.selected_idx = pos
            self._update_selection_highlight()

    # ── Page Reordering & Deletion Actions ───────────────────────────────────

    def _move_page_left(self, pos: int) -> None:
        if pos <= 0 or pos >= len(self.page_order):
            return
        self.page_order[pos], self.page_order[pos - 1] = (
            self.page_order[pos - 1], self.page_order[pos]
        )
        self.selected_idx = pos - 1
        self._rebuild_cards()

    def _move_page_right(self, pos: int) -> None:
        if pos < 0 or pos >= len(self.page_order) - 1:
            return
        self.page_order[pos], self.page_order[pos + 1] = (
            self.page_order[pos + 1], self.page_order[pos]
        )
        self.selected_idx = pos + 1
        self._rebuild_cards()

    def _move_left(self) -> None:
        if self.selected_idx is not None:
            self._move_page_left(self.selected_idx)

    def _move_right(self) -> None:
        if self.selected_idx is not None:
            self._move_page_right(self.selected_idx)

    def _move_to_first(self) -> None:
        if self.selected_idx is None or self.selected_idx <= 0:
            return
        idx = self.page_order.pop(self.selected_idx)
        self.page_order.insert(0, idx)
        self.selected_idx = 0
        self._rebuild_cards()

    def _move_to_last(self) -> None:
        if self.selected_idx is None or self.selected_idx >= len(self.page_order) - 1:
            return
        idx = self.page_order.pop(self.selected_idx)
        self.page_order.append(idx)
        self.selected_idx = len(self.page_order) - 1
        self._rebuild_cards()

    def _delete_page(self, pos: int) -> None:
        if 0 <= pos < len(self.page_order):
            self.page_order.pop(pos)
            if self.page_order:
                self.selected_idx = min(pos, len(self.page_order) - 1)
            else:
                self.selected_idx = None
            self._rebuild_cards()

    def _delete_selected(self) -> None:
        if self.selected_idx is not None:
            self._delete_page(self.selected_idx)

    def _reset_order(self) -> None:
        if not self.current_pdf:
            return
        self.page_order = list(range(self.total_orig_pages))
        self.selected_idx = 0 if self.total_orig_pages > 0 else None
        self._rebuild_cards()

    def _update_counter(self) -> None:
        if not self.current_pdf:
            self._counter_label.config(text='No file loaded')
            return
        retained = len(self.page_order)
        deleted = self.total_orig_pages - retained
        del_str = f'  ({deleted} deleted)' if deleted > 0 else ''
        self._counter_label.config(
            text=f'{retained} of {self.total_orig_pages} pages retained{del_str}'
        )

    # ── Export / Save ─────────────────────────────────────────────────────────

    def _browse_save_location(self) -> None:
        init_file = 'rearranged_output.pdf'
        if self.current_pdf:
            p = Path(self.current_pdf)
            init_file = f'{p.stem}_modified.pdf'

        path = filedialog.asksaveasfilename(
            title='Save Rearranged PDF As',
            defaultextension='.pdf',
            initialfile=init_file,
            filetypes=[('PDF files', '*.pdf'), ('All files', '*.*')],
        )
        if path:
            self._out_entry.delete(0, 'end')
            self._out_entry.insert(0, path)

    def _start_save(self) -> None:
        if not self.current_pdf:
            messagebox.showwarning('No File', 'Please open a PDF file first.')
            return

        if not self.page_order:
            messagebox.showwarning(
                'No Pages', 'All pages have been deleted. At least 1 page is required.'
            )
            return

        out_path = self._out_entry.get().strip()
        if not out_path:
            messagebox.showwarning('Missing Output', 'Please specify an output file path.')
            return

        if not out_path.lower().endswith('.pdf'):
            out_path += '.pdf'

        # Check if overwriting the original file
        try:
            if Path(out_path).resolve() == Path(self.current_pdf).resolve():
                messagebox.showerror(
                    'Cannot Overwrite',
                    'Cannot overwrite the original input file while it is open.\n'
                    'Please choose a different output file name.',
                )
                return
        except Exception:
            pass

        self._save_btn.config(state='disabled', text='⏳  Saving…', bg=BORDER)
        self._draw_bar(0)
        self._status.config(text='Generating new PDF…')

        order_copy = list(self.page_order)
        src = self.current_pdf

        def worker():
            err_msg: Optional[str] = None
            stats: Optional[dict] = None

            def progress_cb(current, total):
                pct = int((current / total) * 100)
                self._root.after(0, self._draw_bar, pct)

            try:
                stats = save_rearranged_pdf(src, out_path, order_copy, progress_cb)
            except Exception as e:
                err_msg = str(e)

            self._root.after(0, self._on_save_done, stats, err_msg)

        threading.Thread(target=worker, daemon=True).start()

    def _draw_bar(self, pct: int) -> None:
        self._progress = pct
        progress_bar(self._bar, pct)

    def _on_save_done(self, stats: Optional[dict], err_msg: Optional[str]) -> None:
        self._save_btn.config(state='normal', text='📑  Save Rearranged PDF', bg=ACCENT)
        self._draw_bar(100)

        if err_msg:
            self._status.config(text=f'❌ Error: {err_msg}')
            messagebox.showerror('Save Failed', f'Could not save PDF:\n{err_msg}')
            return

        if stats:
            out_file = stats['output_path']
            new_sz_str = fmt_bytes(stats['new_size'])
            retained = stats['new_pages']
            orig_p = stats['orig_pages']

            self._status.config(
                text=f'✅ Saved {retained} pages ({new_sz_str}) to {Path(out_file).name}'
            )

            if messagebox.askyesno(
                'Open PDF?',
                f'PDF saved successfully!\n\n'
                f'File: {Path(out_file).name}\n'
                f'Pages: {retained} (originally {orig_p})\n'
                f'Size: {new_sz_str}\n\n'
                f'Would you like to view the file now?',
            ):
                open_path(out_file)
