import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox, 
                             QListWidget, QProgressBar, QMessageBox, QFileDialog,
                             QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from converter_engine import DocumentConverter, ConversionError

class ConversionWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, files, output_format, output_dir, options=None):
        super().__init__()
        self.files = files
        self.output_format = output_format
        self.output_dir = output_dir
        self.options = options or {}
        self.converter = DocumentConverter()
    
    def run(self):
        results = []
        total = len(self.files)
        
        for i, file_path in enumerate(self.files):
            try:
                self.progress.emit(int((i / total) * 100), f"Converting: {Path(file_path).name}")
                output_file = self.converter.convert(
                    file_path, 
                    self.output_format, 
                    self.output_dir,
                    self.options
                )
                results.append((file_path, output_file, True))
            except ConversionError as e:
                results.append((file_path, str(e), False))
            except Exception as e:
                results.append((file_path, f"Error: {str(e)}", False))
        
        self.progress.emit(100, "Done!")
        self.finished.emit(results)

class DropZone(QListWidget):
    files_dropped = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.placeholder_text = "Drop files here or click to browse"
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e5e5;
                border-radius: 8px;
                background-color: white;
                padding: 24px;
                font-size: 13px;
                color: #a3a3a3;
            }
            QListWidget:hover {
                border-color: #d4d4d4;
            }
            QListWidget::item {
                padding: 10px 14px;
                border: none;
                border-bottom: 1px solid #f5f5f5;
                color: #171717;
                background-color: transparent;
                border-radius: 0px;
                margin: 0px;
                font-size: 13px;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
            QListWidget::item:hover {
                background-color: #fafafa;
            }
            QListWidget::item:selected {
                background-color: #f5f5f5;
                color: #000000;
            }
        """)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            from PyQt6.QtGui import QPainter
            from PyQt6.QtCore import Qt
            painter = QPainter(self.viewport())
            painter.setPen(self.palette().color(self.foregroundRole()))
            painter.setFont(self.font())
            painter.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, self.placeholder_text)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_files(files)
        event.acceptProposedAction()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select Files", "",
                "All Files (*.*)"
            )
            if files:
                self.add_files(files)
    
    def add_files(self, files):
        for file in files:
            if os.path.isfile(file):
                self.addItem(Path(file).name)
        
        self.files_dropped.emit(files)

class ConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.files = []
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Converter")
        self.setMinimumSize(700, 550)
        self.resize(800, 650)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QWidget {
                font-family: -apple-system, system-ui, 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #000000;
                color: white;
                border: none;
                padding: 11px 22px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #262626;
            }
            QPushButton:pressed {
                background-color: #0a0a0a;
            }
            QPushButton:disabled {
                background-color: #e5e5e5;
                color: #a3a3a3;
            }
            QComboBox {
                padding: 9px 12px;
                border: 1px solid #e5e5e5;
                border-radius: 6px;
                background-color: white;
                color: #171717;
                font-size: 13px;
                min-width: 130px;
            }
            QComboBox:hover {
                border-color: #d4d4d4;
            }
            QComboBox:focus {
                border-color: #a3a3a3;
            }
            QComboBox::drop-down {
                border: none;
                width: 28px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #737373;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #e5e5e5;
                border-radius: 6px;
                padding: 4px;
                selection-background-color: #fafafa;
                selection-color: #000000;
                color: #171717;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 9px 12px;
                border-radius: 4px;
                min-height: 18px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f5f5f5;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #fafafa;
                font-weight: 500;
            }
            QLabel {
                color: #171717;
            }
            QCheckBox {
                spacing: 8px;
                color: #525252;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1.5px solid #d4d4d4;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #a3a3a3;
            }
            QCheckBox::indicator:checked {
                background-color: #000000;
                border-color: #000000;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTggMkw0IDZMMiA0IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)
        
        # Header
        title = QLabel("Converter")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #000000;")
        main_layout.addWidget(title)
        
        # Drop Zone
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self.on_files_added)
        main_layout.addWidget(self.drop_zone, 1)
        
        # Format Row
        format_row = QWidget()
        format_layout = QHBoxLayout(format_row)
        format_layout.setContentsMargins(0, 0, 0, 0)
        format_layout.setSpacing(12)
        
        format_label = QLabel("Convert to")
        format_label.setStyleSheet("font-size: 13px; color: #525252;")
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "PDF", "DOCX", "PPTX", "HTML", "Markdown",
            "ODT", "ODS", "ODP", "ODG", "XLSX", "XLS",
            "TXT", "RTF", "EPUB", "JPG", "PNG", "GIF",
            "HEIC", "SVG"
        ])
        
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        
        main_layout.addWidget(format_row)
        
        # Options Row
        options_row = QWidget()
        options_layout = QHBoxLayout(options_row)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(20)
        
        self.preserve_layout_cb = QCheckBox("Preserve layout")
        self.preserve_layout_cb.setChecked(True)
        
        self.ocr_cb = QCheckBox("OCR")
        
        quality_label = QLabel("Quality")
        quality_label.setStyleSheet("font-size: 13px; color: #525252;")
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Fast", "Balanced", "Best"])
        self.quality_combo.setCurrentIndex(1)
        
        options_layout.addWidget(self.preserve_layout_cb)
        options_layout.addWidget(self.ocr_cb)
        options_layout.addWidget(quality_label)
        options_layout.addWidget(self.quality_combo)
        options_layout.addStretch()
        
        main_layout.addWidget(options_row)
        
        # Output Row
        output_row = QWidget()
        output_layout = QHBoxLayout(output_row)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(12)
        
        output_label = QLabel("Save to")
        output_label.setStyleSheet("font-size: 13px; color: #525252;")
        
        self.output_path = QLabel(str(Path.home() / "Documents" / "Converted"))
        self.output_path.setStyleSheet("""
            color: #737373;
            font-size: 12px;
            padding: 8px 12px;
            background-color: #fafafa;
            border: 1px solid #e5e5e5;
            border-radius: 6px;
        """)
        
        output_btn = QPushButton("Browse")
        output_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #171717;
                border: 1px solid #e5e5e5;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #fafafa;
                border-color: #d4d4d4;
            }
        """)
        output_btn.clicked.connect(self.select_output_dir)
        
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path, 1)
        output_layout.addWidget(output_btn)
        
        main_layout.addWidget(output_row)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #f5f5f5;
                height: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #000000;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #737373; font-size: 12px;")
        main_layout.addWidget(self.status_label)
        
        # Buttons
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #171717;
                border: 1px solid #e5e5e5;
            }
            QPushButton:hover {
                background-color: #fafafa;
                border-color: #d4d4d4;
            }
        """)
        clear_btn.clicked.connect(self.clear_files)
        
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setEnabled(False)
        self.convert_btn.clicked.connect(self.start_conversion)
        
        button_layout.addStretch()
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(self.convert_btn)
        
        main_layout.addWidget(button_row)
    
    def on_files_added(self, files):
        self.files.extend(files)
        self.convert_btn.setEnabled(len(self.files) > 0)
    
    def clear_files(self):
        self.files.clear()
        self.drop_zone.clear()
        self.convert_btn.setEnabled(False)
    
    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if dir_path:
            self.output_path.setText(dir_path)
    
    def start_conversion(self):
        if not self.files:
            return
        
        output_format = self.format_combo.currentText().lower()
        output_dir = self.output_path.text()
        
        quality_map = {"Fast": 1, "Balanced": 2, "Best": 3}
        options = {
            'preserve_layout': self.preserve_layout_cb.isChecked(),
            'ocr': self.ocr_cb.isChecked(),
            'quality': quality_map.get(self.quality_combo.currentText(), 2)
        }
        
        self.convert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = ConversionWorker(self.files, output_format, output_dir, options)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.error.connect(self.conversion_error)
        self.worker.start()
    
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def conversion_finished(self, results):
        self.progress_bar.setVisible(False)
        self.convert_btn.setEnabled(True)
        
        success_count = sum(1 for _, _, success in results if success)
        total_count = len(results)
        
        if success_count == total_count:
            QMessageBox.information(self, "Success", f"Converted {success_count} file(s)")
            os.startfile(self.output_path.text())
        else:
            failed = [Path(f).name for f, _, s in results if not s]
            QMessageBox.warning(self, "Partial Success", f"Converted {success_count}/{total_count}\n\nFailed:\n" + "\n".join(failed))
        
        self.clear_files()
    
    def conversion_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.convert_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Conversion failed:\n{error_msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConverterApp()
    window.show()
    sys.exit(app.exec())
