@echo off
cd /d "%~dp0"
if not exist "data" mkdir data

echo ========================================================
echo        B I E N V E N I D O   A   L A  SAMMY_API 2.1 
echo                 EXTRACCION BAJO DEMANDA
echo ========================================================
echo.
echo Ingresa las fechas a consultar en formato YYYY-MM-DD
echo (Recuerda que el rango maximo por consulta es de 1 mes).
echo.

set /p FECHA_INICIO="Fecha inicio (ej. 2026-10-01): "
set /p FECHA_FIN="Fecha fin    (ej. 2026-10-23): "

if "%FECHA_INICIO%"=="" (
    echo [!] No ingresaste fecha de inicio. Cancelando.
    pause
    exit /b
)

if "%FECHA_FIN%"=="" (
    echo [!] No ingresaste fecha de fin. Cancelando.
    pause
    exit /b
)

echo.
echo [*] Descargando registros del %FECHA_INICIO% al %FECHA_FIN%...

docker run --rm --env-file .env -e MANUAL_FROM=%FECHA_INICIO% -e MANUAL_TO=%FECHA_FIN% -v "%cd%\data:/app/data" zoom-exporter python export_call_history_csv.py

echo.
echo [✓] Proceso finalizado. Revisa el CSV en la carpeta 'data'.
pause