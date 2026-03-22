@echo off
REM ── Stop the Dictation Tool ──

set PID_FILE=%~dp0.dictation.pid

if exist "%PID_FILE%" (
    set /p PID=<"%PID_FILE%"
    taskkill /f /pid %PID% >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo Dictation tool stopped.
    ) else (
        echo Process not found (may have already exited).
    )
    del "%PID_FILE%" >nul 2>&1
) else (
    echo Dictation tool is not running (no PID file found).
    echo You can also right-click the system tray icon and choose Quit.
)
pause
