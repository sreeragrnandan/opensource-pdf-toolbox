@echo off
cd /d "%~dp0"
python pdf_tool_main.py
if errorlevel 1 (
    echo.
    echo Error running app. Make sure Python is installed.
    pause
)
