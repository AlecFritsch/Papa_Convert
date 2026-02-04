@echo off
title Document Converter
echo.
echo Starting Document Converter...
echo.
python converter_app.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start!
    echo.
    echo Possible solutions:
    echo 1. Run install.bat first
    echo 2. Make sure Python is installed
    echo 3. Restart your terminal/shell
    echo.
    pause
)

