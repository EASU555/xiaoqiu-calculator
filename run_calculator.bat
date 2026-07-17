@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON=py -3"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python 3 was not found. Install Python 3 and try again.
        pause
        exit /b 1
    )
    set "PYTHON=python"
)

%PYTHON% -c "import customtkinter; assert customtkinter.__version__ == '6.0.0'" >nul 2>nul
if errorlevel 1 (
    echo Installing CustomTkinter 6.0.0...
    %PYTHON% -m pip install --disable-pip-version-check customtkinter==6.0.0
    if errorlevel 1 (
        echo Failed to install CustomTkinter.
        pause
        exit /b 1
    )
)

%PYTHON% calculator.py
if errorlevel 1 (
    echo Calculator exited with an error.
    pause
    exit /b 1
)
