@echo off
echo ========================================
echo   PIO PIO BAENA
echo   Sistema de Gestion Avicola
echo ========================================
echo.
echo Iniciando la aplicacion...
echo.

REM Verificar que Python este instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado
    echo.
    echo Por favor, ejecuta primero "instalar.bat"
    echo.
    pause
    exit /b 1
)

REM Verificar que streamlit este instalado
python -m streamlit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Streamlit no esta instalado
    echo.
    echo Por favor, ejecuta primero "instalar.bat"
    echo.
    pause
    exit /b 1
)

echo Iniciando Streamlit...
echo.
echo ========================================
echo La aplicacion se abrira en tu navegador
echo ========================================
echo.
echo Si no se abre automaticamente, copia esta URL:
echo http://localhost:8501
echo.
echo IMPORTANTE:
echo - NO CIERRES esta ventana mientras uses la aplicacion
echo - Para cerrar la aplicacion, presiona Ctrl+C aqui
echo   o simplemente cierra esta ventana
echo.
echo ========================================
echo.

REM Ejecutar Streamlit
python -m streamlit run app.py

REM Si Streamlit se cierra, mostrar mensaje
echo.
echo ========================================
echo Aplicacion cerrada
echo ========================================
echo.
pause
