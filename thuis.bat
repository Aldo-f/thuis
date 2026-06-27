@echo off
set SCRIPT_DIR=%~dp0
where python3 >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3 is required but not installed.
    echo Please install Python 3 from https://www.python.org/downloads/
    echo Then run this script again.
    exit /b 1
)
"%SCRIPT_DIR%src\thuis\main.py" %*
