"""Command-Line Interface für schnelle Konvertierungen"""
import argparse
import sys
from pathlib import Path
from converter_engine import DocumentConverter, ConversionError
from file_analyzer import FileAnalyzer
from batch_processor import BatchProcessor
import glob

def main():
    parser = argparse.ArgumentParser(
        description='🔄 Universal Document Converter - CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s document.pdf -f docx                    # PDF zu DOCX
  %(prog)s *.pdf -f html -o ./output              # Alle PDFs zu HTML
  %(prog)s file.docx -f pdf --quality high        # Hohe Qualität
  %(prog)s document.pdf --analyze                 # Datei analysieren
  %(prog)s *.jpg -f pdf --batch                   # Batch-Konvertierung
        """
    )
    
    parser.add_argument('input', nargs='+', help='Eingabedatei(en) oder Muster (z.B. *.pdf)')
    parser.add_argument('-f', '--format', required=True, 
                       choices=['pdf', 'docx', 'pptx', 'html', 'markdown', 'odt'],
                       help='Zielformat')
    parser.add_argument('-o', '--output', default='./converted',
                       help='Ausgabeordner (Standard: ./converted)')
    parser.add_argument('--quality', choices=['low', 'medium', 'high'], default='medium',
                       help='Konvertierungsqualität')
    parser.add_argument('--ocr', action='store_true',
                       help='OCR für gescannte PDFs aktivieren')
    parser.add_argument('--analyze', action='store_true',
                       help='Nur Datei-Analyse, keine Konvertierung')
    parser.add_argument('--batch', action='store_true',
                       help='Batch-Modus mit Parallelverarbeitung')
    parser.add_argument('--workers', type=int, default=4,
                       help='Anzahl paralleler Worker (Standard: 4)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Ausführliche Ausgabe')
    
    args = parser.parse_args()
    
    # Dateien sammeln (Wildcards expandieren)
    files = []
    for pattern in args.input:
        if '*' in pattern or '?' in pattern:
            files.extend(glob.glob(pattern))
        else:
            files.append(pattern)
    
    if not files:
        print("❌ Keine Dateien gefunden!")
        return 1
    
    # Prüfe ob Dateien existieren
    files = [f for f in files if Path(f).exists()]
    if not files:
        print("❌ Keine gültigen Dateien gefunden!")
        return 1
    
    print(f"📁 Gefunden: {len(files)} Datei(en)")
    
    # Nur Analyse?
    if args.analyze:
        return analyze_files(files, args.verbose)
    
    # Konvertierung
    quality_map = {'low': 1, 'medium': 2, 'high': 3}
    options = {
        'quality': quality_map[args.quality],
        'ocr': args.ocr,
        'preserve_layout': True
    }
    
    if args.batch and len(files) > 1:
        return batch_convert(files, args.format, args.output, options, args.workers, args.verbose)
    else:
        return sequential_convert(files, args.format, args.output, options, args.verbose)

def analyze_files(files, verbose):
    """Analysiert Dateien"""
    analyzer = FileAnalyzer()
    
    print("\n📊 Datei-Analyse\n" + "="*50)
    
    for file in files:
        info = analyzer.analyze(file)
        print(f"\n📄 {info['name']}")
        print(f"   Größe: {info['size']}")
        print(f"   Typ: {info['extension']}")
        
        if verbose:
            print(f"   MIME: {info['mime_type']}")
            if 'dimensions' in info:
                print(f"   Auflösung: {info['dimensions']}")
            if 'pages' in info:
                print(f"   Seiten: {info['pages']}")
        
        print(f"   Empfohlen: {', '.join(info['recommended_formats'])}")
    
    return 0

def sequential_convert(files, format, output_dir, options, verbose):
    """Sequentielle Konvertierung"""
    converter = DocumentConverter()
    success_count = 0
    
    print(f"\n🔄 Konvertiere zu {format.upper()}...\n")
    
    for i, file in enumerate(files, 1):
        try:
            if verbose:
                print(f"[{i}/{len(files)}] {Path(file).name}...", end=' ')
            else:
                print(f"[{i}/{len(files)}] {Path(file).name}")
            
            output = converter.convert(file, format, output_dir, options)
            
            if verbose:
                print(f"✅ → {Path(output).name}")
            
            success_count += 1
            
        except ConversionError as e:
            print(f"❌ Fehler: {e}")
    
    print(f"\n✨ Fertig! {success_count}/{len(files)} erfolgreich konvertiert")
    print(f"📁 Ausgabe: {output_dir}")
    
    return 0 if success_count == len(files) else 1

def batch_convert(files, format, output_dir, options, workers, verbose):
    """Parallele Batch-Konvertierung"""
    converter = DocumentConverter()
    processor = BatchProcessor(max_workers=workers)
    
    print(f"\n⚡ Batch-Konvertierung ({workers} Worker)...\n")
    
    def convert_file(file):
        return converter.convert(file, format, output_dir, options)
    
    def progress(current, total, message):
        if verbose:
            print(f"[{current}/{total}] {message}")
    
    results = processor.process_files(files, convert_file, progress)
    
    success_count = sum(1 for _, _, success in results if success)
    
    print(f"\n✨ Fertig! {success_count}/{len(files)} erfolgreich konvertiert")
    print(f"📁 Ausgabe: {output_dir}")
    
    # Fehler anzeigen
    if success_count < len(files):
        print("\n❌ Fehlgeschlagene Konvertierungen:")
        for file, error, success in results:
            if not success:
                print(f"   • {Path(file).name}: {error}")
    
    return 0 if success_count == len(files) else 1

if __name__ == "__main__":
    sys.exit(main())
