import os
import subprocess
from pathlib import Path
from typing import Optional
import tempfile
import shutil
from functools import lru_cache

class ConversionError(Exception):
    pass

class DocumentConverter:
    def __init__(self):
        self.supported_formats = {
            'pdf': ['docx', 'pptx', 'html', 'markdown', 'odt', 'ods', 'odp', 'jpg', 'png'],
            'docx': ['pdf', 'pptx', 'html', 'markdown', 'odt', 'txt', 'rtf', 'jpg', 'png'],
            'pptx': ['pdf', 'docx', 'html', 'odt', 'odp', 'jpg', 'png'],
            'odt': ['pdf', 'docx', 'pptx', 'html', 'txt', 'rtf', 'jpg', 'png'],
            'ods': ['pdf', 'xlsx', 'xls', 'csv', 'html', 'jpg', 'png'],
            'odp': ['pdf', 'pptx', 'html', 'jpg', 'png'],
            'odg': ['pdf', 'svg', 'png', 'jpg'],
            'html': ['pdf', 'docx', 'pptx', 'markdown', 'txt', 'jpg', 'png'],
            'md': ['pdf', 'docx', 'pptx', 'html', 'txt', 'jpg', 'png'],
            'markdown': ['pdf', 'docx', 'pptx', 'html', 'txt', 'jpg', 'png'],
            'txt': ['pdf', 'docx', 'html', 'markdown', 'rtf', 'jpg', 'png'],
            'rtf': ['pdf', 'docx', 'odt', 'txt', 'html', 'jpg', 'png'],
            'xlsx': ['pdf', 'ods', 'xls', 'csv', 'html', 'jpg', 'png'],
            'xls': ['pdf', 'xlsx', 'ods', 'csv', 'html', 'jpg', 'png'],
            'epub': ['pdf', 'html', 'txt', 'jpg', 'png'],
            'jpg': ['pdf', 'png', 'heic', 'gif'],
            'jpeg': ['pdf', 'png', 'heic', 'gif'],
            'png': ['pdf', 'jpg', 'heic', 'gif'],
            'gif': ['pdf', 'png', 'jpg', 'heic'],
            'heic': ['jpg', 'png', 'pdf', 'gif'],
            'heif': ['jpg', 'png', 'pdf', 'gif'],
            'svg': ['pdf', 'png', 'jpg'],
        }
        # PERFORMANCE: Cache für Tool-Pfade und Lazy Loading
        self._soffice_path = None
        self._pandoc_available = None
        self._docling_converter = None
        self._pil_loaded = False
        self._pillow_heif_registered = False
    
    def convert(self, input_file: str, output_format: str, output_dir: str, options: dict = None) -> str:
        """Konvertiert eine Datei in das gewünschte Format"""
        input_path = Path(input_file)
        output_format = output_format.lower()
        options = options or {}
        
        if not input_path.exists():
            raise ConversionError(f"Datei nicht gefunden: {input_file}")
        
        # Ausgabeordner erstellen
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Ausgabedatei
        output_file = output_path / f"{input_path.stem}.{output_format}"
        
        # Format-Erkennung
        input_ext = input_path.suffix.lower().lstrip('.')
        
        # Konvertierungsstrategie wählen
        try:
            # Image conversions
            if input_ext in ['jpg', 'jpeg', 'png', 'gif', 'heic', 'heif'] and output_format in ['jpg', 'jpeg', 'png', 'gif', 'heic', 'heif']:
                return self._convert_image_format(input_file, output_file, output_format, options)
            elif input_ext in ['jpg', 'jpeg', 'png', 'gif', 'heic', 'heif'] and output_format == 'pdf':
                return self._convert_image_to_pdf(input_file, output_file, options)
            # SVG conversions
            elif input_ext == 'svg':
                return self._convert_svg(input_file, output_file, output_format, options)
            # EPUB conversions
            elif input_ext == 'epub':
                return self._convert_epub(input_file, output_file, output_format, options)
            # PDF with Docling
            elif input_ext == 'pdf' and output_format in ['docx', 'markdown', 'html']:
                return self._convert_with_docling(input_file, output_file, output_format, options)
            # Document to image (via PDF intermediate)
            elif output_format in ['jpg', 'jpeg', 'png'] and input_ext not in ['jpg', 'jpeg', 'png', 'gif', 'heic', 'heif', 'svg']:
                # First convert to PDF, then to image
                temp_pdf = output_path / f"{input_path.stem}_temp.pdf"
                self.convert(input_file, 'pdf', str(output_path), options)
                result = self._convert_pdf_to_image(str(temp_pdf), output_file, output_format, options)
                temp_pdf.unlink(missing_ok=True)
                return result
            # Markdown/Pandoc conversions
            elif input_ext in ['md', 'markdown'] or output_format in ['md', 'markdown']:
                return self._convert_with_pandoc(input_file, output_file, output_format, options)
            # LibreOffice conversions (Office formats)
            else:
                return self._convert_with_libreoffice(input_file, output_file, output_format, options)
        except Exception as e:
            raise ConversionError(f"Konvertierung fehlgeschlagen: {str(e)}")
    
    def _get_docling_converter(self):
        """Lazy loading für Docling (schwere Bibliothek)"""
        if self._docling_converter is None:
            try:
                from docling.document_converter import DocumentConverter as DoclingConverter
                self._docling_converter = DoclingConverter()
            except ImportError:
                raise ConversionError("Docling nicht installiert. Bitte 'pip install docling' ausführen.")
        return self._docling_converter
    
    def _convert_with_docling(self, input_file: str, output_file: Path, output_format: str, options: dict) -> str:
        """Konvertierung mit Docling (KI-gestützt für PDFs) - OPTIMIERT"""
        try:
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            
            # PERFORMANCE: Lazy loading des Converters
            converter = self._get_docling_converter()
            
            # PERFORMANCE: Optimierte Pipeline-Optionen
            pipeline_options = PdfPipelineOptions()
            if options.get('ocr', False):
                pipeline_options.do_ocr = True
            
            # Qualitäts-basierte Optimierung
            quality = options.get('quality', 2)
            if quality == 1:  # Niedrig = schnell
                pipeline_options.do_table_structure = False
            
            result = converter.convert(input_file, pipeline_options=pipeline_options)
            
            if output_format == 'markdown' or output_format == 'md':
                content = result.document.export_to_markdown()
                output_file = output_file.with_suffix('.md')
                output_file.write_text(content, encoding='utf-8')
            elif output_format == 'html':
                content = result.document.export_to_html()
                output_file = output_file.with_suffix('.html')
                output_file.write_text(content, encoding='utf-8')
            elif output_format == 'docx':
                # PERFORMANCE: Direkte Konvertierung ohne Zwischenschritt wenn möglich
                md_content = result.document.export_to_markdown()
                temp_md = Path(tempfile.gettempdir()) / f"{output_file.stem}_{os.getpid()}.md"
                temp_md.write_text(md_content, encoding='utf-8')
                try:
                    return self._convert_with_pandoc(str(temp_md), output_file, 'docx', options)
                finally:
                    temp_md.unlink(missing_ok=True)
            
            return str(output_file)
        except ImportError:
            raise ConversionError("Docling nicht installiert. Bitte 'pip install docling' ausführen.")
        except Exception as e:
            raise ConversionError(f"Docling-Fehler: {str(e)}")
    
    @lru_cache(maxsize=1)
    def _check_pandoc_available(self) -> bool:
        """Cached Pandoc-Verfügbarkeit"""
        if self._pandoc_available is not None:
            return self._pandoc_available
        self._pandoc_available = shutil.which('pandoc') is not None
        return self._pandoc_available
    
    def _convert_with_pandoc(self, input_file: str, output_file: Path, output_format: str, options: dict) -> str:
        """Konvertierung mit Pandoc - OPTIMIERT mit BOM-Bereinigung"""
        
        # Wenn Pandoc nicht verfügbar ist, nutze alternative Methoden
        if not self._check_pandoc_available():
            # Für Markdown zu PDF: Nutze markdown-pdf Library
            if output_format == 'pdf':
                return self._convert_markdown_to_pdf_native(input_file, output_file, options)
            # Für andere Formate: Fehler
            raise ConversionError("Pandoc nicht installiert. Bitte Terminal neu starten oder von https://pandoc.org installieren.")
        
        try:
            # BOM-Bereinigung für Markdown-Dateien
            input_path = Path(input_file)
            if input_path.suffix.lower() in ['.md', '.markdown']:
                # Versuche verschiedene Encodings
                content = None
                for encoding in ['utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'utf-8', 'latin-1']:
                    try:
                        with open(input_file, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                
                if content is None:
                    raise ConversionError("Konnte Markdown-Datei nicht lesen. Unbekanntes Encoding.")
                
                # Entferne BOM-Zeichen
                content = content.replace('\ufeff', '').replace('ÿþ', '')
                
                # Erstelle temporäre bereinigte Datei
                temp_input = input_path.parent / f"{input_path.stem}_clean{input_path.suffix}"
                with open(temp_input, 'w', encoding='utf-8') as f:
                    f.write(content)
                input_file = str(temp_input)
                cleanup_temp = True
            else:
                cleanup_temp = False
            
            format_map = {
                'markdown': 'md',
                'md': 'md',
                'docx': 'docx',
                'html': 'html',
                'pdf': 'pdf',
                'pptx': 'pptx'
            }
            
            output_ext = format_map.get(output_format, output_format)
            output_file = output_file.with_suffix(f'.{output_ext}')
            
            # PERFORMANCE: Timeout basierend auf Qualität
            quality = options.get('quality', 2)
            timeout = 90 if quality == 3 else 45
            
            cmd = ['pandoc', input_file, '-o', str(output_file)]
            
            # PERFORMANCE: Qualitäts-basierte Optimierung
            if quality == 3:
                cmd.extend(['--standalone', '--toc', '--number-sections'])
            elif quality == 1:
                cmd.append('--no-highlight')  # Schneller ohne Syntax-Highlighting
            
            # PDF-Engine: Nutze LibreOffice als Fallback
            if output_format == 'pdf':
                # Konvertiere erst zu HTML, dann mit LibreOffice zu PDF
                html_temp = output_file.with_suffix('.html')
                cmd_html = ['pandoc', input_file, '-o', str(html_temp), '--standalone']
                subprocess.run(cmd_html, capture_output=True, text=True, check=True, timeout=timeout)
                
                # Jetzt HTML zu PDF mit LibreOffice
                result = self._convert_with_libreoffice(str(html_temp), output_file, 'pdf', options)
                html_temp.unlink(missing_ok=True)  # Cleanup
                
                # Cleanup temp input
                if cleanup_temp:
                    Path(input_file).unlink(missing_ok=True)
                
                return result
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True, 
                timeout=timeout
            )
            
            # Cleanup temp input
            if cleanup_temp:
                Path(input_file).unlink(missing_ok=True)
            
            if not output_file.exists():
                raise ConversionError("Ausgabedatei wurde nicht erstellt")
            
            return str(output_file)
        except FileNotFoundError:
            raise ConversionError("Pandoc nicht installiert. Bitte von https://pandoc.org installieren.")
        except subprocess.CalledProcessError as e:
            raise ConversionError(f"Pandoc-Fehler: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise ConversionError(f"Pandoc-Konvertierung dauerte zu lange (>{timeout}s)")
        finally:
            # Cleanup temp file falls Exception
            if 'cleanup_temp' in locals() and cleanup_temp and 'input_file' in locals():
                Path(input_file).unlink(missing_ok=True)
    
    @lru_cache(maxsize=1)
    def _find_soffice_path(self) -> str:
        """Cached LibreOffice Pfad-Suche"""
        if self._soffice_path:
            return self._soffice_path
            
        soffice_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            "soffice",
            "libreoffice"
        ]
        
        for path in soffice_paths:
            if shutil.which(path) or os.path.exists(path):
                self._soffice_path = path
                return path
        
        raise ConversionError("LibreOffice nicht gefunden. Bitte installieren: https://www.libreoffice.org")
    
    def _convert_with_libreoffice(self, input_file: str, output_file: Path, output_format: str, options: dict) -> str:
        """Konvertierung mit LibreOffice (headless) - OPTIMIERT"""
        try:
            format_map = {
                'pdf': 'pdf',
                'docx': 'docx',
                'pptx': 'pptx',
                'odt': 'odt',
                'html': 'html'
            }
            
            lo_format = format_map.get(output_format, output_format)
            output_dir = output_file.parent
            
            soffice = self._find_soffice_path()
            
            # PERFORMANCE: Optimierte Flags für schnellere Konvertierung
            cmd = [
                soffice,
                '--headless',
                '--invisible',
                '--nocrashreport',
                '--nodefault',
                '--nofirststartwizard',
                '--nolockcheck',
                '--nologo',
                '--norestore',
                '--convert-to', lo_format,
                '--outdir', str(output_dir),
                input_file
            ]
            
            # PERFORMANCE: Erhöhtes Timeout für große Dateien
            timeout = 120 if options.get('quality', 2) == 3 else 60
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            expected_output = output_dir / f"{Path(input_file).stem}.{lo_format}"
            
            if expected_output.exists() and expected_output != output_file:
                expected_output.rename(output_file)
            
            if not output_file.exists():
                raise ConversionError(f"Konvertierung fehlgeschlagen: {result.stderr}")
            
            return str(output_file)
        except subprocess.TimeoutExpired:
            raise ConversionError(f"LibreOffice-Konvertierung dauerte zu lange (>{timeout}s)")
        except Exception as e:
            raise ConversionError(f"LibreOffice-Fehler: {str(e)}")
    
    def _load_pil(self):
        """Lazy loading für PIL"""
        if not self._pil_loaded:
            try:
                from PIL import Image
                self._pil_loaded = True
                return Image
            except ImportError:
                raise ConversionError("Pillow nicht installiert. Bitte 'pip install Pillow' ausführen.")
        from PIL import Image
        return Image
    
    def _convert_image_to_pdf(self, input_file: str, output_file: Path, options: dict) -> str:
        """Konvertiert Bilder zu PDF - OPTIMIERT"""
        try:
            Image = self._load_pil()
            self._register_heif()
            
            # PERFORMANCE: Lazy loading mit Context Manager
            with Image.open(input_file) as img:
                # RGB konvertieren falls nötig
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # PERFORMANCE: Qualitäts-basierte DPI
                quality = options.get('quality', 2)
                dpi = {1: 72, 2: 150, 3: 300}.get(quality, 150)
                
                output_file = output_file.with_suffix('.pdf')
                
                # PERFORMANCE: Optimierte Save-Parameter
                save_kwargs = {
                    'format': 'PDF',
                    'resolution': float(dpi),
                    'optimize': quality < 3  # Nur bei niedriger/mittlerer Qualität
                }
                
                img.save(output_file, **save_kwargs)
            
            return str(output_file)
        except ImportError:
            raise ConversionError("Pillow nicht installiert. Bitte 'pip install Pillow' ausführen.")
        except Exception as e:
            raise ConversionError(f"Bild-Konvertierung fehlgeschlagen: {str(e)}")
    
    def _register_heif(self):
        """Register HEIF support for Pillow"""
        if not self._pillow_heif_registered:
            try:
                from pillow_heif import register_heif_opener
                register_heif_opener()
                self._pillow_heif_registered = True
            except ImportError:
                pass  # HEIF support optional
    
    def _convert_image_format(self, input_file: str, output_file: Path, output_format: str, options: dict) -> str:
        """Konvertiert zwischen Bildformaten (JPG, PNG, GIF, HEIC, HEIF)"""
        try:
            Image = self._load_pil()
            self._register_heif()
            
            quality = options.get('quality', 2)
            quality_value = {1: 60, 2: 85, 3: 95}.get(quality, 85)
            
            with Image.open(input_file) as img:
                # Format-spezifische Konvertierung
                if output_format in ['jpg', 'jpeg']:
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    output_file = output_file.with_suffix('.jpg')
                    img.save(output_file, 'JPEG', quality=quality_value, optimize=True)
                
                elif output_format == 'png':
                    output_file = output_file.with_suffix('.png')
                    compress_level = {1: 1, 2: 6, 3: 9}.get(quality, 6)
                    img.save(output_file, 'PNG', compress_level=compress_level, optimize=True)
                
                elif output_format == 'gif':
                    output_file = output_file.with_suffix('.gif')
                    if img.mode not in ('P', 'L'):
                        img = img.convert('P', palette=Image.ADAPTIVE)
                    img.save(output_file, 'GIF', optimize=True)
                
                elif output_format in ['heic', 'heif']:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    output_file = output_file.with_suffix('.heic')
                    img.save(output_file, 'HEIF', quality=quality_value)
            
            return str(output_file)
        except Exception as e:
            raise ConversionError(f"Bildformat-Konvertierung fehlgeschlagen: {str(e)}")
    
    def _convert_svg(self, input_file: str, output_file: Path, output_format: str, options: dict) -> str:
        """Konvertiert SVG zu anderen Formaten"""
        try:
            if output_format == 'pdf':
                try:
                    import cairosvg
                    output_file = output_file.with_suffix('.pdf')
                    cairosvg.svg2pdf(url=input_file, write_to=str(output_file))
                    return str(output_file)
                except (ImportError, OSError):
                    # Fallback: SVG -> PNG -> PDF
                    return self._convert_svg_fallback(input_file, output_file, 'pdf', options)
            
            elif output_format == 'png':
                try:
                    import cairosvg
                    output_file = output_file.with_suffix('.png')
                    quality = options.get('quality', 2)
                    dpi = {1: 72, 2: 150, 3: 300}.get(quality, 150)
                    cairosvg.svg2png(url=input_file, write_to=str(output_file), dpi=dpi)
                    return str(output_file)
                except (ImportError, OSError):
                    # Fallback: Nutze Pillow mit SVG-Support
                    return self._convert_svg_fallback(input_file, output_file, 'png', options)
            
            elif output_format in ['jpg', 'jpeg']:
                try:
                    import cairosvg
                    Image = self._load_pil()
                    temp_png = output_file.with_suffix('.png')
                    quality = options.get('quality', 2)
                    dpi = {1: 72, 2: 150, 3: 300}.get(quality, 150)
                    cairosvg.svg2png(url=input_file, write_to=str(temp_png), dpi=dpi)
                    
                    with Image.open(temp_png) as img:
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        output_file = output_file.with_suffix('.jpg')
                        quality_value = {1: 60, 2: 85, 3: 95}.get(quality, 85)
                        img.save(output_file, 'JPEG', quality=quality_value, optimize=True)
                    
                    temp_png.unlink(missing_ok=True)
                    return str(output_file)
                except (ImportError, OSError):
                    return self._convert_svg_fallback(input_file, output_file, 'jpg', options)
            
            else:
                raise ConversionError(f"SVG zu {output_format} nicht unterstützt")
        
        except Exception as e:
            raise ConversionError(f"SVG-Konvertierung fehlgeschlagen: {str(e)}")
    
    def _convert_svg_fallback(self, input_file: str, output_file: Path, output_format: str, options: dict) -> str:
        """Fallback für SVG-Konvertierung ohne CairoSVG (nutzt LibreOffice)"""
        try:
            # LibreOffice kann SVG zu PDF konvertieren
            if output_format == 'pdf':
                return self._convert_with_libreoffice(input_file, output_file, 'pdf', options)
            else:
                # SVG -> PDF -> Image
                temp_pdf = output_file.with_suffix('.pdf')
                self._convert_with_libreoffice(input_file, temp_pdf, 'pdf', options)
                result = self._convert_pdf_to_image(str(temp_pdf), output_file, output_format, options)
                temp_pdf.unlink(missing_ok=True)
                return result
        except Exception as e:
            raise ConversionError(f"SVG-Fallback fehlgeschlagen: {str(e)}")
    
    def _convert_epub(self, input_file: str, output_file: Path, output_format: str, options: dict) -> str:
        """Konvertiert EPUB zu anderen Formaten"""
        try:
            if output_format == 'pdf':
                # EPUB -> HTML -> PDF via LibreOffice
                import ebooklib
                from ebooklib import epub
                
                book = epub.read_epub(input_file)
                html_content = []
                
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        html_content.append(item.get_content().decode('utf-8'))
                
                temp_html = output_file.with_suffix('.html')
                temp_html.write_text('\n'.join(html_content), encoding='utf-8')
                
                result = self._convert_with_libreoffice(str(temp_html), output_file, 'pdf', options)
                temp_html.unlink(missing_ok=True)
                return result
            
            elif output_format == 'html':
                import ebooklib
                from ebooklib import epub
                
                book = epub.read_epub(input_file)
                html_content = ['<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>']
                
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        html_content.append(item.get_content().decode('utf-8'))
                
                html_content.append('</body></html>')
                output_file = output_file.with_suffix('.html')
                output_file.write_text('\n'.join(html_content), encoding='utf-8')
                return str(output_file)
            
            elif output_format == 'txt':
                import ebooklib
                from ebooklib import epub
                from html.parser import HTMLParser
                
                class HTMLTextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                    
                    def handle_data(self, data):
                        self.text.append(data)
                    
                    def get_text(self):
                        return ''.join(self.text)
                
                book = epub.read_epub(input_file)
                text_content = []
                
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        parser = HTMLTextExtractor()
                        parser.feed(item.get_content().decode('utf-8'))
                        text_content.append(parser.get_text())
                
                output_file = output_file.with_suffix('.txt')
                output_file.write_text('\n\n'.join(text_content), encoding='utf-8')
                return str(output_file)
            
            else:
                raise ConversionError(f"EPUB zu {output_format} nicht unterstützt")
        
        except ImportError:
            raise ConversionError("ebooklib nicht installiert. Bitte 'pip install ebooklib' ausführen.")
        except Exception as e:
            raise ConversionError(f"EPUB-Konvertierung fehlgeschlagen: {str(e)}")
    
    def _convert_pdf_to_image(self, input_file: str, output_file: Path, output_format: str, options: dict) -> str:
        """Konvertiert PDF zu Bild (erste Seite)"""
        try:
            from pdf2image import convert_from_path
            
            quality = options.get('quality', 2)
            dpi = {1: 72, 2: 150, 3: 300}.get(quality, 150)
            
            images = convert_from_path(input_file, dpi=dpi, first_page=1, last_page=1)
            
            if images:
                img = images[0]
                
                if output_format in ['jpg', 'jpeg']:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    output_file = output_file.with_suffix('.jpg')
                    quality_value = {1: 60, 2: 85, 3: 95}.get(quality, 85)
                    img.save(output_file, 'JPEG', quality=quality_value, optimize=True)
                
                elif output_format == 'png':
                    output_file = output_file.with_suffix('.png')
                    compress_level = {1: 1, 2: 6, 3: 9}.get(quality, 6)
                    img.save(output_file, 'PNG', compress_level=compress_level, optimize=True)
                
                return str(output_file)
            else:
                raise ConversionError("Keine Seiten im PDF gefunden")
        
        except ImportError:
            raise ConversionError("pdf2image nicht installiert. Bitte 'pip install pdf2image' ausführen.")
        except Exception as e:
            raise ConversionError(f"PDF zu Bild Konvertierung fehlgeschlagen: {str(e)}")
    
    def _convert_markdown_to_pdf_native(self, input_file: str, output_file: Path, options: dict) -> str:
        """Konvertiert Markdown zu PDF mit markdown-pdf Library (ohne BOM-Probleme)"""
        try:
            from markdown_pdf import MarkdownPdf, Section
            
            # Lese Markdown-Datei mit korrektem Encoding (entfernt BOM)
            with open(input_file, 'r', encoding='utf-8-sig') as f:
                markdown_content = f.read()
            
            # Entferne zusätzliche BOM-Zeichen falls vorhanden
            markdown_content = markdown_content.replace('\ufeff', '')
            
            # Erstelle temporäre bereinigte Markdown-Datei
            temp_md = output_file.parent / f"{output_file.stem}_clean.md"
            with open(temp_md, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            output_file = output_file.with_suffix('.pdf')
            
            # Erstelle PDF
            pdf = MarkdownPdf()
            pdf.add_section(Section(markdown_content))
            pdf.save(str(output_file))
            
            # Cleanup
            temp_md.unlink(missing_ok=True)
            
            return str(output_file)
        
        except ImportError:
            # Fallback: Bereinige Markdown und nutze LibreOffice
            with open(input_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            content = content.replace('\ufeff', '')
            
            temp_md = output_file.parent / f"{output_file.stem}_clean.md"
            with open(temp_md, 'w', encoding='utf-8') as f:
                f.write(content)
            
            try:
                result = self._convert_with_libreoffice(str(temp_md), output_file, 'pdf', options)
                return result
            finally:
                temp_md.unlink(missing_ok=True)
        
        except Exception as e:
            raise ConversionError(f"Markdown zu PDF Konvertierung fehlgeschlagen: {str(e)}")
