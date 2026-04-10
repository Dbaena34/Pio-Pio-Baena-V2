@echo off
echo ========================================
echo   BACKUP - PIO PIO BAENA
echo   Copia de Seguridad de Datos
echo ========================================
echo.

REM Crear carpeta de backups si no existe
if not exist backups mkdir backups

REM Obtener fecha y hora actual
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set year=%datetime:~0,4%
set month=%datetime:~4,2%
set day=%datetime:~6,2%
set hour=%datetime:~8,2%
set minute=%datetime:~10,2%
set second=%datetime:~12,2%

set timestamp=%year%%month%%day%_%hour%%minute%%second%

REM Verificar que existe la base de datos
if not exist data\granja.db (
    echo ERROR: No se encontro la base de datos
    echo.
    echo Verifica que el archivo data\granja.db existe
    pause
    exit /b 1
)

REM Copiar base de datos
echo Creando backup de la base de datos...
copy data\granja.db backups\granja_backup_%timestamp%.db >nul

if %errorlevel% equ 0 (
    echo.
    echo Backup creado exitosamente
    echo.
    echo Archivo: backups\granja_backup_%timestamp%.db
    echo Fecha: %day%/%month%/%year% - %hour%:%minute%:%second%
    echo.
    
    REM Contar backups
    set count=0
    for %%f in (backups\*.db) do set /a count+=1
    echo Total de backups: %count%
    echo.
    
    REM Advertencia si hay muchos backups
    if %count% gtr 10 (
        echo AVISO: Tienes mas de 10 backups
        echo Considera eliminar los mas antiguos para ahorrar espacio
        echo.
    )
) else (
    echo.
    echo ERROR: No se pudo crear el backup
    pause
    exit /b 1
)

echo ========================================
echo RECOMENDACIONES:
echo ========================================
echo.
echo 1. Crea backups regularmente al menos 1 vez por semana
echo 2. Guarda los backups en otro lugar seguro:
echo    - USB
echo    - OneDrive/Google Drive
echo    - Otro disco duro
echo.
echo 3. Para restaurar un backup:
echo    - Cierra la aplicacion
echo    - Renombra data\granja.db a data\granja_old.db
echo    - Copia el backup a data\granja.db
echo    - Inicia la aplicacion
echo.

pause
