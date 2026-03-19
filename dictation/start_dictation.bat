@echo off
REM ── Dictation Tool Launcher ──
REM Auto-detects Anaconda, Miniconda, or plain Python.

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
    if exist %%~P\Scripts\activate.bat (
        call %%~P\Scripts\activate.bat %%~P
        goto :run
    )
)

REM Fall back to system Python
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :run

echo ERROR: Could not find Python or Conda.
echo Install Python from https://www.python.org/downloads/
pause
exit /b 1

:run
cd /d "%~dp0"
python "%~dp0dictate.py"
if %ERRORLEVEL% NEQ 0 pause
