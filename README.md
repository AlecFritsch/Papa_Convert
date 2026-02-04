# Universal Document Converter Pro 🔄

The ultimate desktop app for document conversion with AI-powered layout preservation and performance optimizations.

## 🚀 Features

- **🎯 Drag & Drop GUI** - Intuitive desktop app (PyQt6)
- **🤖 AI Layout Preservation** - Docling AI for perfect PDF conversion
- **⚡ Multi-Engine** - Docling (AI) + LibreOffice + Pandoc + CairoSVG
- **🔥 Performance-Optimized** - Multiprocessing, Lazy Loading, Caching
- **📦 Batch Processing** - Multiple files in parallel (CPU-optimized)
- **🤖 Auto-Converter** - Watchdog for automatic conversion
- **💻 CLI Tool** - For power users and automation
- **🖥️ 100% Local** - No cloud, your data stays with you
- **🌈 Modern UI** - Clean, flat design with smooth interactions

## 📊 Supported Formats

### Documents
**Input/Output:** PDF, DOCX, PPTX, ODT, ODS, ODP, ODG, XLSX, XLS, HTML, Markdown, TXT, RTF, EPUB

### Images
**Input/Output:** JPG, PNG, GIF, HEIC/HEIF, SVG

### Special Features
- ✅ **Any document → JPG/PNG** (via PDF intermediate)
- ✅ **HEIC/HEIF support** (iPhone photos)
- ✅ **SVG to raster** (PDF, PNG, JPG)
- ✅ **EPUB to document** (PDF, HTML, TXT)
- ✅ **Office formats** (XLSX, XLS, ODS, ODP, ODG)

## ⚡ Performance Optimizations

### Implemented
- ✅ **Multiprocessing** instead of threading (GIL-free, true parallelism)
- ✅ **Lazy Loading** for heavy libraries (Docling, PIL, pillow-heif)
- ✅ **LRU-Caching** for tool paths (LibreOffice, Pandoc)
- ✅ **Optimized LibreOffice flags** (--invisible, --nolockcheck, etc.)
- ✅ **Quality-based timeouts** (45-120s depending on settings)
- ✅ **Context Manager** for resources (PIL Images)
- ✅ **Process-specific temp files** (prevents collisions)
- ✅ **Auto-worker detection** (optimal for CPU cores)

### Benchmark Results
- **Single file:** 1-5 seconds
- **Batch (10 PDFs):** 3-4x faster than sequential
- **Memory:** ~100-200 MB (Lazy Loading)
- **Startup:** <2 seconds

## 📦 Installation

### Quick Start (Windows)
```cmd
# 1. Double-click install.bat (installs EVERYTHING automatically)
# 2. RESTART terminal (important for Pandoc!)
# 3. Double-click start.bat
```

**Important:** After install.bat, restart your terminal/CMD so Pandoc works!

### What Gets Installed?
- ✅ Python packages (PyQt6, Pillow, pillow-heif, cairosvg, ebooklib, etc.)
- ✅ LibreOffice (for Office formats)
- ✅ Pandoc (for Markdown/HTML)

### Manual Installation

#### 1. LibreOffice
```cmd
winget install TheDocumentFoundation.LibreOffice
```

#### 2. Pandoc
```cmd
winget install JohnMacFarlane.Pandoc
# IMPORTANT: Restart terminal!
```

#### 3. Python Packages
```cmd
pip install -r requirements.txt
```

## 🎯 Usage

### Desktop App (GUI)
```cmd
python converter_app.py
```

### Command-Line (CLI)
```cmd
# Single file
python cli.py document.pdf -f docx

# Batch with wildcards
python cli.py *.pdf -f html -o ./output

# With performance options
python cli.py *.docx -f pdf --batch --workers 4 --quality high

# Analyze file
python cli.py document.pdf --analyze

# Image conversions
python cli.py photo.heic -f jpg
python cli.py document.pdf -f png
python cli.py logo.svg -f pdf
```

### Auto-Converter (Watchdog)
```cmd
python auto_converter.py
# Configuration: auto_convert_config.json
```

### Quick-Start Menu
```cmd
quick_start.bat
```

## 🎨 GUI Features

- **Modern Flat Design** - Clean, professional interface
- **19 Output Formats** - PDF, DOCX, PPTX, ODT, ODS, ODP, ODG, XLSX, XLS, HTML, Markdown, TXT, RTF, EPUB, JPG, PNG, GIF, HEIC, SVG
- **Quality Settings** - Fast, Balanced, Best
- **OCR Support** - Extract text from images
- **Layout Preservation** - Keep original formatting
- **Drag & Drop** - Easy file selection
- **Batch Processing** - Convert multiple files at once
- **Auto-Open** - Automatically open output folder

## 🔧 Technology Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| **PDF-AI** | Docling (IBM) | AI layout recognition |
| **Office** | LibreOffice | DOCX/PPTX/ODT/ODS/ODP/ODG/XLSX/XLS |
| **Markup** | Pandoc | Markdown/HTML/RTF |
| **Images** | Pillow + pillow-heif | JPG/PNG/GIF/HEIC/HEIF |
| **SVG** | CairoSVG | Vector graphics |
| **EPUB** | ebooklib | E-books |
| **GUI** | PyQt6 | Desktop interface |
| **Parallel** | ProcessPoolExecutor | Multiprocessing |
| **Watch** | Watchdog | Auto-conversion |

## 💡 Performance Tips

### Fastest Conversion
```cmd
python cli.py *.pdf -f docx --batch --workers 4 --quality low
```

### Best Quality
```cmd
python cli.py document.pdf -f docx --quality high --ocr
```

### Batch Optimization
- **4-8 Workers** for I/O-bound (documents)
- **2-4 Workers** for CPU-bound (images)
- **Quality "Fast"** for quick preview
- **Quality "Best"** for archiving

## 🏗️ Project Structure

```
├── converter_app.py          # Desktop app (GUI)
├── converter_engine.py        # Core engine (optimized)
├── batch_processor.py         # Multiprocessing
├── file_analyzer.py           # Metadata analysis
├── auto_converter.py          # Watchdog
├── cli.py                     # Command-line
├── install.bat                # Installation
├── start.bat                  # Start app
├── quick_start.bat            # Interactive menu
├── presets.json               # Predefined presets
└── requirements.txt           # Dependencies
```

## 🐛 Troubleshooting

### "LibreOffice not found"
```cmd
# Check path
where soffice

# Reinstall
winget install TheDocumentFoundation.LibreOffice
```

### "Pandoc not found"
```cmd
winget install JohnMacFarlane.Pandoc
# Restart terminal
```

### "cairosvg not working"
```cmd
# Install GTK runtime for Windows
# Download from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
```

### "Conversion too slow"
```cmd
# Reduce quality
--quality low

# Fewer workers
--workers 2

# Disable OCR (if not needed)
```

### "Memory error"
```cmd
# Fewer parallel processes
--workers 2

# Process files individually
python cli.py file1.pdf -f docx
python cli.py file2.pdf -f docx
```

## 📝 License

MIT License - Free for private and commercial use

## 🎯 Use Cases

- **Business:** Batch conversion of contracts, invoices
- **Students:** Essays to PDF, notes conversion
- **Developers:** Documentation to Markdown, README to HTML
- **Photographers:** HEIC to JPG conversion
- **Designers:** SVG to PDF/PNG
- **Archiving:** High-quality PDF conversion with OCR
- **E-books:** EPUB to PDF/HTML

## 🔮 Roadmap

- [ ] PyMuPDF integration (10x faster than Docling)
- [ ] GPU acceleration for OCR
- [ ] PDF merge/split
- [ ] Watermarks
- [ ] Web interface
- [ ] Docker container
- [ ] Multi-page PDF to images
- [ ] Image compression options

---

**Made with ❤️ and ⚡ Performance in mind**
