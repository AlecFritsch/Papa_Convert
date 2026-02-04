@echo off
echo ========================================
echo Universal Document Converter - Installation
echo ========================================
echo.

echo [1/5] Pruefe Python...
python --version
if errorlevel 1 (
    echo FEHLER: Python nicht gefunden!
    echo Bitte Python von https://www.python.org installieren
    pause
    exit /b 1
)
echo.

echo [2/5] Installiere Python-Pakete...
pip install -r requirements.txt
if errorlevel 1 (
    echo FEHLER: Installation fehlgeschlagen!
    pause
    exit /b 1
)
echo.

echo [3/5] Installiere LibreOffice...
winget install --id TheDocumentFoundation.LibreOffice -e --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
    echo WARNUNG: LibreOffice Installation fehlgeschlagen oder bereits installiert
    echo.
)

echo [4/5] Installiere Pandoc...
winget install --id JohnMacFarlane.Pandoc -e --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
    echo WARNUNG: Pandoc Installation fehlgeschlagen oder bereits installiert
    echo.
)

echo [5/5] Pruefe Installation...
echo.
echo Python-Pakete:
pip show PyQt6 >nul 2>&1 && echo [OK] PyQt6 installiert || echo [FEHLT] PyQt6
pip show Pillow >nul 2>&1 && echo [OK] Pillow installiert || echo [FEHLT] Pillow
pip show watchdog >nul 2>&1 && echo [OK] Watchdog installiert || echo [FEHLT] Watchdog
echo.
echo Externe Tools:
if exist "C:\Program Files\LibreOffice\program\soffice.exe" (echo [OK] LibreOffice installiert) else if exist "C:\Program Files (x86)\LibreOffice\program\soffice.exe" (echo [OK] LibreOffice installiert) else (echo [FEHLT] LibreOffice)
where pandoc >nul 2>&1 && echo [OK] Pandoc installiert || echo [WARNUNG] Pandoc - Shell neu starten!
echo.

echo ========================================
echo Installation abgeschlossen!
echo ========================================
echo.
echo WICHTIG: Bitte Shell/Terminal neu starten damit Pandoc funktioniert!
echo.
echo Starte die App mit: python converter_app.py
echo Oder doppelklick auf: start.bat
echo.
pause
