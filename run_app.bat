@echo off
echo Starting Legal Notebook Application...
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else if exist "env\Scripts\activate.bat" (
    echo Activating virtual environment...
    call env\Scripts\activate.bat
) else (
    echo Warning: No virtual environment found. Running with system Python...
    echo Expected locations: venv, .venv, or env
    echo.
)

REM Change to the script directory
cd /d "%~dp0"

REM Run the application
echo Running UI application...
python ui\app.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
