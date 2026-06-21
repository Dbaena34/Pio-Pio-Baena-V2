@echo off
title Instalador - Pio Pio Baena

echo ========================================
echo   INSTALADOR - PIO PIO BAENA
echo ========================================
echo.

REM Verificar Python

python -V >nul 2>&1

if errorlevel 1 (
    echo.
    echo ERROR: Python no esta instalado.
    echo.
    echo Instale Python primero y vuelva a ejecutar.
    echo.
    pause
    exit /b 1
)

echo Python encontrado:
python -V

echo.
echo ========================================
echo CREANDO ENTORNO VIRTUAL
echo ========================================
echo.

if exist .venv (
    echo El entorno virtual ya existe.
) else (
    python -m venv .venv

    if errorlevel 1 (
        echo.
        echo ERROR creando entorno virtual.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo INSTALANDO DEPENDENCIAS
echo ========================================
echo.

call .venv\Scripts\activate.bat

python -m pip install --upgrade pip

python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR instalando dependencias.
    pause
    exit /b 1
)

echo.
echo Dependencias instaladas correctamente.

echo.
echo ========================================
echo CREANDO ACCESO DIRECTO
echo ========================================
echo.

set CURRENT_DIR=%~dp0

echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\Pio Pio Baena.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%CURRENT_DIR%iniciar.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%CURRENT_DIR%" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript CreateShortcut.vbs //nologo
del CreateShortcut.vbs

echo.
echo ========================================
echo INSTALACION COMPLETADA
echo ========================================
echo.
echo Ya puede ejecutar iniciar.bat
echo.
pause