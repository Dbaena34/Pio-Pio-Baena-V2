@echo off
title Pio Pio Baena

echo ========================================
echo      PIO PIO BAENA
echo ========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo ERROR:
    echo El entorno virtual no existe.
    echo.
    echo Ejecute instalar.bat primero.
    echo.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

REM ── AUTO-ACTUALIZACION ──────────────────────────────────────────────────────
python updater.py
echo ────────────────────────────────────────
echo.

REM ── INICIO DE LA APLICACION ─────────────────────────────────────────────────
echo Iniciando aplicacion...
echo.

python app.py

echo.
echo ========================================
echo Aplicacion finalizada
echo ========================================
echo.

pause
