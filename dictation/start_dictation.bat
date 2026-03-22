@echo off
REM ── Dictation Tool Launcher (background) ──
REM Launches the tool with pythonw (no console window).
REM Status appears in the system tray.

REM Try common Conda locations
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
    if exist %%~P\pythonw.exe (
        start "" %%~P\pythonw.exe "%~dp0dictate.py"
        goto :done
    )
    if exist %%~P\Scripts\pythonw.exe (
        start "" %%~P\Scripts\pythonw.exe "%~dp0dictate.py"
        goto :done
    )
)

REM Fall back to system pythonw
where pythonw >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start "" pythonw "%~dp0dictate.py"
    goto :done
)

REM Last resort: use python (will show a console window)
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start "" python "%~dp0dictate.py"
    goto :done
)

echo ERROR: Could not find Python.
echo Install Python from https://www.python.org/downloads/
pause
exit /b 1

:done
echo Dictation tool started (system tray).
