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

echo Checking pinned dependencies...
%PYTHON% -c "import customtkinter, PyInstaller; assert customtkinter.__version__ == '6.0.0'; assert PyInstaller.__version__ == '6.20.0'" >nul 2>nul
if errorlevel 1 (
    echo Installing dependencies from requirements.txt...
    %PYTHON% -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies.
        pause
        exit /b 1
    )
)

if exist tests (
    echo Running tests...
    %PYTHON% -m unittest discover -s tests -v
    if errorlevel 1 (
        echo Tests failed. Build cancelled.
        pause
        exit /b 1
    )
)

echo Building ABCalculator.exe...
%PYTHON% -m PyInstaller --noconfirm --clean --onefile --windowed --exclude-module numpy --icon app_icon.ico --add-data "app_icon.ico;." --name ABCalculator calculator.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Build complete: dist\ABCalculator.exe
pause
