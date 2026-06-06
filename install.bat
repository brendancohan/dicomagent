@echo off
echo Setting up DICOM Agent Service...

:: Check if python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python could not be found. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

:: Create virtual environment
echo Creating virtual environment...
python -m venv venv

:: Activate and install requirements
echo Installing dependencies...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Installation complete!
echo To start the service, run:
echo   venv\Scripts\activate
echo   uvicorn main:app --host 0.0.0.0 --port 8000
pause
