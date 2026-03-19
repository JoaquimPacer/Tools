@echo off
REM ── Dictation Tool Installer ──
REM 1. Installs Python dependencies
REM 2. Adds the tool to Windows startup (runs on login)

echo.
echo ============================================
echo   Dictation Tool - One-Time Setup
echo ============================================
echo.

REM ── Find Python ──
set PYTHON_FOUND=0

for %%P in (
    "%USERPROFILE%\anaconda3"
    "%USERPROFILE%\miniconda3"
    "%USERPROFILE%\Anaconda3"
    "%USERPROFILE%\Miniconda3"
    "%LOCALAPPDATA%\anaconda3"
    "%LOCALAPPDATA%\miniconda3"
    "C:\ProgramData\anaconda3"
    "C:\ProgramData\miniconda3"
) do (
    if exist %%~P\Scripts\activate.bat (
        call %%~P\Scripts\activate.bat %%~P
        set PYTHON_FOUND=1
        goto :install_deps
    )
)

python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_FOUND=1
    goto :install_deps
)

echo ERROR: Could not find Python or Conda.
echo Install Python from https://www.python.org/downloads/
pause
exit /b 1

:install_deps
echo [1/2] Installing dependencies...
pip install -r "%~dp0requirements.txt"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: pip install failed. Check the output above.
    pause
    exit /b 1
)

echo.
echo [2/2] Adding to Windows startup...

REM Create a VBS wrapper in the Windows Startup folder.
REM This runs the .bat minimized so a console doesn't pop up in your face.
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set VBS_FILE=%STARTUP_DIR%\Dictation.vbs
set BAT_PATH=%~dp0start_dictation.bat

echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_FILE%"
echo WshShell.Run chr(34) ^& "%BAT_PATH%" ^& chr(34), 7, False >> "%VBS_FILE%"
echo Set WshShell = Nothing >> "%VBS_FILE%"

echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo   - Dependencies installed
echo   - Will auto-start on login (minimized)
echo   - To start now: double-click start_dictation.bat
echo   - To stop auto-start: delete %VBS_FILE%
echo.
pause
