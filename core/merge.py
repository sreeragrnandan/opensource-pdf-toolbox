"""
core/merge.py
PDF merge engine: combines multiple PDFs into a single output file.
"""

import os
from typing import Callable, List, Optional

from core.dependencies import Pdf, ObjectStreamMode


def merge_pdfs(
    input_paths: List[str],
    output_path: str,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> dict:
    """
    Merge multiple PDFs into a single output file in the order given.

    Returns a dict:
        files   int   number of input files merged
        pages   int   total page count in the output
        size    int   output file size in bytes
        output  str   path to the output file
    """
    merged = Pdf.new()
    total  = len(input_paths)

    for i, path in enumerate(input_paths):
        with Pdf.open(path) as pdf:
            merged.pages.extend(pdf.pages)
        if progress_cb:
            # Input files account for 0–90 % of progress
            progress_cb(int((i + 1) / total * 90))

    if progress_cb:
        progress_cb(95)

    total_pages = len(merged.pages)

    merged.save(
        output_path,
        compress_streams=True,
        object_stream_mode=ObjectStreamMode.generate,
    )

    if progress_cb:
        progress_cb(100)

    return {
        'files':  total,
        'pages':  total_pages,
        'size':   os.path.getsize(output_path),
        'output': output_path,
    }
