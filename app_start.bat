@echo off
TITLE Critical Hits

cd /d "%~dp0"
python app_start.py

if %errorlevel% neq 0 (
    echo.
    echo [!] Application crashed with Error %errorlevel%
    echo.
)

pause