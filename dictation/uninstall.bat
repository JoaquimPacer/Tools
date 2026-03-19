@echo off
REM ── Remove Dictation Tool from Windows Startup ──

set VBS_FILE=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Dictation.vbs

if exist "%VBS_FILE%" (
    del "%VBS_FILE%"
    echo Dictation tool removed from Windows startup.
) else (
    echo Dictation tool was not in Windows startup.
)
echo.
pause
