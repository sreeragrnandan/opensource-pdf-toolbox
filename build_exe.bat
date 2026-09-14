@echo off
title OpenSource PDF Toolbox ? Build Script
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   OpenSource PDF Toolbox ? EXE Builder
echo ============================================================
echo.

cd /d "%~dp0"

:: ?? Check Python ????????????????????????????????????????????
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ and add it to PATH.
    pause
    exit /b 1
)

:: ?? Install / upgrade dependencies ??????????????????????????
echo [1/3] Checking dependencies...
pip install pikepdf Pillow tkinterdnd2 PyMuPDF --quiet --upgrade
if errorlevel 1 (
    echo [WARN] Some packages may have failed to upgrade. Continuing...
)

:: ?? Build with PyInstaller (output directly to project root) ?
echo.
echo [2/3] Building executable (this may take a few minutes)...
python -m PyInstaller PDF_Toolbox.spec --clean --noconfirm --distpath "%~dp0"

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. See output above for details.
    pause
    exit /b 1
)

:: ?? Desktop shortcut ?????????????????????????????????????????
echo.
echo [3/3] Build succeeded!
echo       Output: %~dp0OpenSource PDF Toolbox.exe
echo.
set /p SHORTCUT=Would you like to add a shortcut to your Desktop? (Y/N): 
if /i "!SHORTCUT!"=="Y" (
    echo Creating Desktop shortcut...
    powershell -NoProfile -Command ^
        " = New-Object -ComObject WScript.Shell; ^
          = .CreateShortcut([Environment]::GetFolderPath('Desktop') + '\OpenSource PDF Toolbox.lnk'); ^
         .TargetPath = '%~dp0OpenSource PDF Toolbox.exe'; ^
         .WorkingDirectory = '%~dp0'; ^
         .IconLocation = '%~dp0assets\icon.ico'; ^
         .Description = 'OpenSource PDF Toolbox ? Compress, Merge & Rearrange PDFs'; ^
         .Save()"
    echo Done! Shortcut added to Desktop.
) else (
    echo Skipping Desktop shortcut.
)

echo.
echo ============================================================
echo   All done! The app is ready at:
echo   %~dp0OpenSource PDF Toolbox.exe
echo ============================================================
echo.
pause
