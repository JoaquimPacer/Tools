@echo off
REM ── Dictation Tool Installer ──
REM 1. Installs Python dependencies
REM 2. Registers auto-start via Task Scheduler

echo.
echo ============================================
echo   Dictation Tool v2 - Setup
echo ============================================
echo.

REM ── Find Python ──
set PYTHON_CMD=
set PYTHONW_CMD=

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
        set PYTHON_CMD=python
        if exist %%~P\pythonw.exe (
            set "PYTHONW_CMD=%%~P\pythonw.exe"
        ) else if exist %%~P\Scripts\pythonw.exe (
            set "PYTHONW_CMD=%%~P\Scripts\pythonw.exe"
        )
        goto :install_deps
    )
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    for /f "delims=" %%i in ('where pythonw 2^>nul') do set "PYTHONW_CMD=%%i"
    goto :install_deps
)

echo ERROR: Could not find Python or Conda.
echo Install Python from https://www.python.org/downloads/
pause
exit /b 1

:install_deps
echo [1/3] Installing dependencies...
pip install -r "%~dp0requirements.txt"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: pip install failed. Check the output above.
    pause
    exit /b 1
)

echo.
echo [2/3] Removing old startup entry (if any)...
set VBS_FILE=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Dictation.vbs
if exist "%VBS_FILE%" del "%VBS_FILE%"
schtasks /delete /tn "DictationTool" /f >nul 2>&1

echo.
echo [3/3] Adding to Task Scheduler (runs on login)...

REM Determine which pythonw to use
if "%PYTHONW_CMD%"=="" (
    echo WARNING: pythonw.exe not found. Using python.exe (console will be visible).
    set "LAUNCH_CMD=%PYTHON_CMD% \"%~dp0dictate.py\""
) else (
    set "LAUNCH_CMD=\"%PYTHONW_CMD%\" \"%~dp0dictate.py\""
)

schtasks /create /tn "DictationTool" /tr "%LAUNCH_CMD%" /sc onlogon /rl limited /f >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Could not create scheduled task.
    echo You can start manually with start_dictation.bat
) else (
    echo Scheduled task created.
)

echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo   - Dependencies installed
echo   - Auto-starts on login (Task Scheduler)
echo   - To start now: double-click start_dictation.bat
echo   - To stop: right-click system tray icon ^> Quit
echo   - To uninstall: double-click uninstall.bat
echo.
echo   First run will download the Whisper model (~1.5 GB).
echo   This only happens once.
echo.
pause
