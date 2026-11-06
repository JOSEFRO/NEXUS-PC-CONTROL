@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (echo Instala Python 3.10 o superior desde python.org & pause & exit /b 1)
if not exist .venv py -m venv .venv
call .venv\Scripts\activate
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
start "" http://127.0.0.1:8765
py app.py
pause
