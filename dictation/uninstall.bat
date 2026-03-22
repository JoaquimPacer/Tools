@echo off
REM ── Remove Dictation Tool ──

echo Stopping dictation tool...
set PID_FILE=%~dp0.dictation.pid
if exist "%PID_FILE%" (
    set /p PID=<"%PID_FILE%"
    taskkill /f /pid %PID% >nul 2>&1
    del "%PID_FILE%" >nul 2>&1
)

echo Removing scheduled task...
schtasks /delete /tn "DictationTool" /f >nul 2>&1

echo Removing old startup entry (if any)...
set VBS_FILE=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Dictation.vbs
if exist "%VBS_FILE%" del "%VBS_FILE%"

echo.
echo Dictation tool removed from auto-start.
echo (Python packages and models were not removed.)
echo.
pause
