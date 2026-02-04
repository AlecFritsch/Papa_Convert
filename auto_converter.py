"""Automatische Konvertierung bei Dateiänderungen"""
import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from converter_engine import DocumentConverter, ConversionError
import json

class ConversionRule:
    """Regel für automatische Konvertierung"""
    def __init__(self, watch_dir: str, extensions: list, target_format: str, output_dir: str):
        self.watch_dir = watch_dir
        self.extensions = [ext.lower() for ext in extensions]
        self.target_format = target_format.lower()
        self.output_dir = output_dir

class AutoConvertHandler(FileSystemEventHandler):
    """Handler für Datei-Events"""
    
    def __init__(self, rules: list):
        self.rules = rules
        self.converter = DocumentConverter()
        self.processing = set()  # Verhindert Doppel-Verarbeitung
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        self._process_file(file_path)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        # Nur verarbeiten wenn Datei nicht gerade bearbeitet wird
        if file_path not in self.processing:
            time.sleep(0.5)  # Warte bis Datei fertig geschrieben
            self._process_file(file_path)
    
    def _process_file(self, file_path: str):
        """Verarbeitet Datei basierend auf Regeln"""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        # Prüfe alle Regeln
        for rule in self.rules:
            if ext in rule.extensions:
                if file_path in self.processing:
                    return
                
                self.processing.add(file_path)
                
                try:
                    print(f"🔄 Auto-Konvertierung: {path.name} → {rule.target_format.upper()}")
                    output = self.converter.convert(
                        file_path, 
                        rule.target_format, 
                        rule.output_dir
                    )
                    print(f"✅ Fertig: {output}")
                except ConversionError as e:
                    print(f"❌ Fehler: {e}")
                finally:
                    self.processing.discard(file_path)

class AutoConverter:
    """Automatischer Konverter mit Watchdog"""
    
    def __init__(self, config_file: str = "auto_convert_config.json"):
        self.config_file = config_file
        self.rules = []
        self.observer = None
        self.load_config()
    
    def load_config(self):
        """Lädt Konfiguration aus JSON"""
        if not os.path.exists(self.config_file):
            self.create_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            for rule_data in config.get('rules', []):
                rule = ConversionRule(
                    rule_data['watch_dir'],
                    rule_data['extensions'],
                    rule_data['target_format'],
                    rule_data['output_dir']
                )
                self.rules.append(rule)
                
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
    
    def create_default_config(self):
        """Erstellt Standard-Konfiguration"""
        default_config = {
            'rules': [
                {
                    'watch_dir': str(Path.home() / 'Documents' / 'AutoConvert'),
                    'extensions': ['.pdf', '.docx'],
                    'target_format': 'html',
                    'output_dir': str(Path.home() / 'Documents' / 'Converted')
                }
            ]
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"📝 Standard-Konfiguration erstellt: {self.config_file}")
    
    def start(self):
        """Startet automatische Überwachung"""
        if not self.rules:
            print("⚠️ Keine Regeln definiert!")
            return
        
        print("🚀 Auto-Converter gestartet")
        print(f"📁 Überwache {len(self.rules)} Ordner...")
        
        for rule in self.rules:
            print(f"  • {rule.watch_dir} ({', '.join(rule.extensions)}) → {rule.target_format.upper()}")
        
        event_handler = AutoConvertHandler(self.rules)
        self.observer = Observer()
        
        # Registriere alle Watch-Directories
        for rule in self.rules:
            if os.path.exists(rule.watch_dir):
                self.observer.schedule(event_handler, rule.watch_dir, recursive=False)
            else:
                print(f"⚠️ Ordner existiert nicht: {rule.watch_dir}")
                os.makedirs(rule.watch_dir, exist_ok=True)
                print(f"✅ Ordner erstellt: {rule.watch_dir}")
                self.observer.schedule(event_handler, rule.watch_dir, recursive=False)
        
        self.observer.start()
        
        try:
            print("\n✨ Bereit! Lege Dateien in die überwachten Ordner.")
            print("Drücke Ctrl+C zum Beenden...\n")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stoppt Überwachung"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("\n👋 Auto-Converter beendet")

if __name__ == "__main__":
    converter = AutoConverter()
    converter.start()
