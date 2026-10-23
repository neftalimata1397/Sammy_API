@echo off
cd /d "%~dp0"

echo [*] Construyendo / Verificando imagen de Docker...
docker build -t zoom-exporter .

echo [*] Ejecutando extraccion...
docker run --rm --env-file .env -v "%cd%\data:/app/data" zoom-exporter

echo [✓] Proceso terminado. Revisa la carpeta data.
pause