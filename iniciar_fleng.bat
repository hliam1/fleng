@echo off
title Fleng
cd /d "%~dp0"

echo.
echo   Iniciando Fleng...
echo.

if not exist "venv\" (
    echo   Primera vez: preparando el entorno. Esto tarda un momento.
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo   [ERROR] No se encontro Python.
        echo   Instalalo desde https://www.python.org/downloads/
        echo   y marca la casilla "Add Python to PATH".
        echo.
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

if not exist ".env" (
    echo.
    echo   [!] No existe el archivo .env
    echo   Copiando la plantilla...
    copy .env.example .env >nul
    echo.
    echo   Abre el archivo .env y pega tus claves de API.
    echo   Despues vuelve a ejecutar este archivo.
    echo.
    notepad .env
    pause
    exit /b 1
)

python app.py
pause
