@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
cd /d "%ROOT_DIR%"

REM Carrega variaveis de .env se existir
if exist "%ROOT_DIR%\.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%ROOT_DIR%\.env") do (
        set "LINE=%%A"
        if not "!LINE!"=="" if not "!LINE:~0,1!"=="#" (
            set "%%A=%%B"
        )
    )
)

if "%API_HOST%"=="" set "API_HOST=127.0.0.1"
if "%API_PORT%"=="" set "API_PORT=8000"
if "%MOSQUITTO_PORT%"=="" set "MOSQUITTO_PORT=1883"
if "%DB_PATH%"=="" set "DB_PATH=%ROOT_DIR%\db\banco_de_dados.db"
if "%USE_VENV%"=="" set "USE_VENV=1"

REM 1. Seleciona ou cria ambiente Python
set "PYTHON_BIN="
if exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON_BIN=%ROOT_DIR%\.venv\Scripts\python.exe"
) else if "%USE_VENV%"=="1" (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Erro: Python 3.10+ nao encontrado no PATH.
        pause
        exit /b 1
    )
    echo Criando ambiente virtual em .venv...
    python -m venv "%ROOT_DIR%\.venv"
    if errorlevel 1 (
        echo Erro ao criar ambiente virtual .venv.
        pause
        exit /b 1
    )
    set "PYTHON_BIN=%ROOT_DIR%\.venv\Scripts\python.exe"
    echo Instalando dependencias de requirements.txt...
    "!PYTHON_BIN!" -m pip install --upgrade pip
    "!PYTHON_BIN!" -m pip install -r "%ROOT_DIR%\requirements.txt"
    if errorlevel 1 (
        echo Erro ao instalar dependencias.
        pause
        exit /b 1
    )
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Erro: Python nao encontrado no PATH.
        pause
        exit /b 1
    )
    set "PYTHON_BIN=python"
)

REM 2. Inicia o Mosquitto em janela separada
set "MOSQ_DIR=%ROOT_DIR%\mosquitto"
echo Iniciando Mosquitto na porta %MOSQUITTO_PORT%...
if exist "%MOSQ_DIR%\mosquitto.exe" (
    start "Broker MQTT - Mosquitto" /D "%MOSQ_DIR%" "%MOSQ_DIR%\mosquitto.exe" -c mosquitto.conf -p %MOSQUITTO_PORT% -v
) else (
    where mosquitto >nul 2>&1
    if errorlevel 1 (
        echo Erro: Mosquitto nao encontrado nem em %MOSQ_DIR%\mosquitto.exe nem no PATH.
        pause
        exit /b 1
    )
    start "Broker MQTT - Mosquitto" /D "%MOSQ_DIR%" mosquitto -c mosquitto.conf -p %MOSQUITTO_PORT% -v
)

timeout /t 1 /nobreak >nul

REM 3. Inicia o FastAPI
echo Iniciando FastAPI em http://%API_HOST%:%API_PORT%/docs ...
echo Pressione Ctrl+C para encerrar o FastAPI.
"%PYTHON_BIN%" -m uvicorn backend.app.main:app --app-dir "%ROOT_DIR%" --host %API_HOST% --port %API_PORT%

echo.
echo Encerrando Mosquitto...
taskkill /FI "WINDOWTITLE eq Broker MQTT - Mosquitto*" /T /F >nul 2>&1
pause
