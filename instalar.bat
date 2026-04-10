@echo off
echo ========================================
echo   INSTALADOR - PIO PIO BAENA
echo   Sistema de Gestion Avicola
echo ========================================
echo.

REM Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Python ya esta instalado
    python --version
    goto :install_dependencies
)

echo Python no esta instalado en este equipo
echo.
echo ========================================
echo DESCARGANDO PYTHON 3.12...
echo ========================================
echo.

REM Crear carpeta temporal
if not exist temp mkdir temp

REM Descargar Python 3.12 (instalador embebido)
echo Descargando Python 3.12.0 - esto puede tardar unos minutos...
powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile 'temp\python-installer.exe'}"

if not exist temp\python-installer.exe (
    echo.
    echo ERROR: No se pudo descargar Python
    echo.
    echo Por favor, descarga Python manualmente desde:
    echo https://www.python.org/downloads/
    echo.
    echo Despues vuelve a ejecutar este instalador.
    pause
    exit /b 1
)

echo.
echo ========================================
echo INSTALANDO PYTHON 3.12...
echo ========================================
echo.
echo IMPORTANTE: En la ventana que se abrira:
echo 1. Marca la casilla "Add Python to PATH"
echo 2. Haz clic en "Install Now"
echo 3. Espera a que termine la instalacion
echo.
pause

REM Instalar Python con opciones por defecto y agregarlo al PATH
start /wait temp\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

echo.
echo Esperando a que se complete la instalacion de Python...
timeout /t 5 /nobreak >nul

REM Verificar si Python se instalo correctamente
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python no se instalo correctamente
    echo.
    echo Cierra esta ventana y ejecuta el instalador nuevamente.
    echo Si el problema persiste, instala Python manualmente desde:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python instalado correctamente
python --version

REM Limpiar archivos temporales
if exist temp\python-installer.exe del temp\python-installer.exe
if exist temp rmdir temp

:install_dependencies
echo.
echo ========================================
echo INSTALANDO DEPENDENCIAS...
echo ========================================
echo.

REM Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip --quiet

REM Instalar dependencias
echo Instalando librerias necesarias...
echo Esto puede tardar unos minutos
echo.

python -m pip install -r requirements.txt --quiet

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Hubo un problema instalando las dependencias
    echo.
    echo Intenta ejecutar manualmente:
    echo python -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo Todas las dependencias instaladas correctamente

REM Crear acceso directo en el escritorio
echo.
echo ========================================
echo CREANDO ACCESO DIRECTO...
echo ========================================
echo.

REM Obtener ruta actual
set CURRENT_DIR=%~dp0

REM Crear script VBS para crear acceso directo
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\Pio Pio Baena.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%CURRENT_DIR%iniciar.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%CURRENT_DIR%" >> CreateShortcut.vbs
echo oLink.Description = "Sistema de Gestion Avicola - Pio Pio Baena" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript CreateShortcut.vbs //nologo
del CreateShortcut.vbs

echo Acceso directo creado en el escritorio

echo.
echo ========================================
echo INSTALACION COMPLETADA
echo ========================================
echo.
echo El sistema esta listo para usar.
echo.
echo PARA INICIAR LA APLICACION:
echo 1. Haz doble clic en el acceso directo del escritorio
echo    "Pio Pio Baena"
echo.
echo    O
echo.
echo 2. Ejecuta el archivo "iniciar.bat" de esta carpeta
echo.
echo La aplicacion se abrira automaticamente en tu navegador.
echo.
pause
