@echo off
setlocal
if /i "%~1"=="/elevated" goto elevated
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -ArgumentList '/elevated' -Verb RunAs"
exit /b

:elevated
cd /d "%~dp0"
call "%~dp0INICIAR.bat"
