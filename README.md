# OpenSource PDF Toolbox

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white" alt="Python 3.9+"/>
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT"/>
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform"/>
  <img src="https://img.shields.io/badge/GUI-Tkinter-orange" alt="Tkinter"/>
  <img src="https://img.shields.io/badge/status-active-brightgreen" alt="Status"/>
</p>

<p align="center">
  A lightweight, privacy-focused open-source desktop toolbox to <b>compress</b>, <b>merge</b>, and manipulate PDFs locally — with zero cloud dependencies.
</p>

---

## ✨ Features

### ⚡ Compress
- **3 compression presets** — choose between lossless, balanced, or maximum compression
- **Batch processing** — compress multiple PDFs in one go
- **Drag & drop** — drop files directly onto the window
- **Live progress** — real-time progress bar with per-file status
- **Results panel** — see original size, compressed size, bytes saved, and % reduction
- **Custom output folder** — save anywhere or next to the original
- **Quick preview prompt** — open the compressed PDF immediately in your default viewer

### 🔗 Merge
- **Combine any number of PDFs** into a single output file
- **Reorder files** using ▲ ▼ buttons before merging
- **Double-click to remove** a file from the list
- **Custom output file name & location** via Save As dialog
- **Results panel** — shows files merged, total pages, and output size
- **Quick preview prompt** — open the merged PDF directly after creation

### 🛡️ Privacy & Performance
- **Non-destructive** — originals are never modified
- **100% Offline** — your files never leave your local machine

---

## 📸 Preview

```
┌─────────────────────────────────────────────┐
│  ⊛  OpenSource PDF Toolbox                  │
│     Compress & Merge PDFs · Offline         │
├─────────────────────────────────────────────┤
│  [ ⚡ Compress ]   [ 🔗 Merge ]             │
├─────────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐    │
│  │  ⬆  Drop PDF files here · Browse   │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  Compression Level     Output Folder        │
│  🔵 Low — Lossless    ● Same as source     │
│  🟣 Medium — Balanced ○ Choose folder…     │
│  🔴 High — Maximum                         │
│                                             │
│  [ ⚡ Compress PDF ]  ████████░░░  80%      │
│                                             │
│  ORIGINAL   COMPRESSED   SAVED   REDUCTION  │
│   4.2 MB      1.1 MB    3.1 MB    73.8%    │
└─────────────────────────────────────────────┘
```

---

## 🗂️ Compression Levels

| Level | Technique | Quality Impact |
|---|---|---|
| **🔵 Low — Lossless** | Stream compression + object deduplication | None — pixel-perfect |
| **🟣 Medium — Balanced** | Above + image resampling to ~150 DPI | Minimal — excellent for documents |
| **🔴 High — Maximum** | Above + images compressed to ~96 DPI (JPEG 65) | Slight softening on photos |

> **Tip:** For text-heavy PDFs (reports, invoices, contracts), even **High** mode looks identical — image quality only matters for photo-heavy documents.

---

## 🚀 Getting Started

### Prerequisites

- Python **3.9** or higher
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/opensource-pdf-toolbox.git
cd opensource-pdf-toolbox

# 2. Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python pdf_tool_main.py
```

**Windows users:** double-click `Launch PDF Tool.bat` — no terminal needed.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| [`pikepdf`](https://pikepdf.readthedocs.io/) | ≥ 8.0 | PDF parsing, stream compression, object deduplication, and merging |
| [`Pillow`](https://pillow.readthedocs.io/) | ≥ 10.0 | Image extraction and JPEG re-encoding |
| [`tkinterdnd2`](https://github.com/pmgagne/tkinterdnd2) | ≥ 0.3 | Drag-and-drop support (optional) |

> `tkinter` is part of Python's standard library and requires no separate install.

---

## 🗃️ Project Structure

```
opensource-pdf-toolbox/
│
├── pdf_tool_main.py              # Main entry point (Tkinter bootstrapping)
├── Launch PDF Tool.bat           # Windows one-click launcher
│
├── core/                         # Core logic & algorithms (headless, zero GUI)
│   ├── __init__.py               # Core API exports
│   ├── dependencies.py           # Dependency checks (pikepdf, Pillow, TkinterDnD)
│   ├── utils.py                  # Format utilities, open_path helper
│   ├── compress.py               # Compression presets & processing
│   └── merge.py                  # Multi-file PDF merger
│
├── ui/                           # User Interface components
│   ├── __init__.py               # UI module export
│   ├── theme.py                  # Colors, fonts, reusable widget factories
│   ├── compress_tab.py           # Compression tab UI & worker thread
│   ├── merge_tab.py              # Merge tab UI & worker thread
│   └── app.py                    # App shell, header, and tab navigation
│
├── requirements.txt              # Python dependencies
├── LICENSE                       # MIT License
└── README.md                     # Project documentation
```

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Commit** your changes: `git commit -m 'Add some feature'`
4. **Push** to the branch: `git push origin feature/your-feature`
5. **Open** a Pull Request

Please make sure your code follows the existing style and modular architecture.

### Ideas for contributions

- [ ] macOS/Linux `.sh` launcher script
- [ ] Split PDF tab (extract page ranges or split into individual pages)
- [ ] Metadata viewer & editor (title, author, creation date)
- [ ] PDF watermark / page number stamp tool
- [ ] PDF/A compliance export mode
- [ ] Dark / Light theme toggle

---

## 🐛 Reporting Issues

Found a bug? Please [open an issue](https://github.com/your-username/opensource-pdf-toolbox/issues) and include:

- Your OS and Python version (`python --version`)
- The error message or screenshot
- Steps to reproduce

---

## 📄 License

Distributed under the MIT License. See [`LICENSE`](./LICENSE) for more information.

---

## 🙏 Acknowledgements

- [pikepdf](https://pikepdf.readthedocs.io/) — PDF manipulation engine
- [Pillow](https://pillow.readthedocs.io/) — image processing
- [tkinterdnd2](https://github.com/pmgagne/tkinterdnd2) — drag-and-drop for Tkinter

---

<p align="center">Made with ❤️ · MIT Licensed · Open Source</p>
