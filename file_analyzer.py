"""Datei-Analyse und Metadaten-Extraktion"""
import os
from pathlib import Path
from typing import Dict, Any
import mimetypes

class FileAnalyzer:
    """Analysiert Dateien und extrahiert Metadaten"""
    
    def __init__(self):
        mimetypes.init()
    
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """Analysiert eine Datei und gibt Metadaten zurück"""
        path = Path(file_path)
        
        if not path.exists():
            return {'error': 'Datei nicht gefunden'}
        
        stats = path.stat()
        mime_type, _ = mimetypes.guess_type(str(path))
        
        info = {
            'name': path.name,
            'size': self._format_size(stats.st_size),
            'size_bytes': stats.st_size,
            'extension': path.suffix.lower(),
            'mime_type': mime_type or 'unknown',
            'modified': stats.st_mtime,
            'is_image': self._is_image(path),
            'is_document': self._is_document(path),
            'recommended_formats': self._get_recommended_formats(path)
        }
        
        # Spezifische Analysen
        if info['is_image']:
            info.update(self._analyze_image(path))
        elif path.suffix.lower() == '.pdf':
            info.update(self._analyze_pdf(path))
        
        return info
    
    def _format_size(self, size_bytes: int) -> str:
        """Formatiert Dateigröße lesbar"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _is_image(self, path: Path) -> bool:
        """Prüft ob Datei ein Bild ist"""
        return path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    
    def _is_document(self, path: Path) -> bool:
        """Prüft ob Datei ein Dokument ist"""
        return path.suffix.lower() in ['.pdf', '.docx', '.doc', '.odt', '.txt', '.rtf', '.pptx', '.xlsx']
    
    def _get_recommended_formats(self, path: Path) -> list:
        """Empfiehlt Zielformate basierend auf Eingabeformat"""
        ext = path.suffix.lower()
        
        recommendations = {
            '.pdf': ['DOCX', 'HTML', 'Markdown'],
            '.docx': ['PDF', 'HTML', 'ODT'],
            '.pptx': ['PDF', 'HTML'],
            '.jpg': ['PDF'],
            '.png': ['PDF'],
            '.html': ['PDF', 'DOCX'],
            '.md': ['PDF', 'DOCX', 'HTML']
        }
        
        return recommendations.get(ext, ['PDF'])
    
    def _analyze_image(self, path: Path) -> Dict[str, Any]:
        """Analysiert Bild-Dateien"""
        try:
            from PIL import Image
            with Image.open(path) as img:
                return {
                    'dimensions': f"{img.width}x{img.height}",
                    'format': img.format,
                    'mode': img.mode
                }
        except:
            return {}
    
    def _analyze_pdf(self, path: Path) -> Dict[str, Any]:
        """Analysiert PDF-Dateien"""
        try:
            import PyPDF2
            with open(path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                return {
                    'pages': len(pdf.pages),
                    'encrypted': pdf.is_encrypted
                }
        except:
            return {}
    
    def batch_analyze(self, file_paths: list) -> Dict[str, Dict[str, Any]]:
        """Analysiert mehrere Dateien"""
        results = {}
        for file_path in file_paths:
            results[file_path] = self.analyze(file_path)
        return results
    
    def get_conversion_estimate(self, file_path: str, target_format: str) -> Dict[str, Any]:
        """Schätzt Konvertierungszeit und -größe"""
        info = self.analyze(file_path)
        size_bytes = info.get('size_bytes', 0)
        
        # Grobe Schätzungen basierend auf Dateigröße
        time_per_mb = {
            'pdf': 2,      # Sekunden pro MB
            'docx': 1,
            'html': 0.5,
            'markdown': 0.3
        }
        
        size_mb = size_bytes / (1024 * 1024)
        estimated_time = size_mb * time_per_mb.get(target_format.lower(), 1)
        
        return {
            'estimated_time_seconds': max(1, int(estimated_time)),
            'estimated_time_text': self._format_time(estimated_time),
            'complexity': 'niedrig' if size_mb < 1 else 'mittel' if size_mb < 10 else 'hoch'
        }
    
    def _format_time(self, seconds: float) -> str:
        """Formatiert Zeit lesbar"""
        if seconds < 60:
            return f"{int(seconds)} Sekunden"
        minutes = int(seconds / 60)
        return f"{minutes} Minute(n)"
