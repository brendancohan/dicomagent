@echo off
echo ===================================
echo    DICOM Agent Service Updater     
echo ===================================
echo Please select your update method:
echo 1) Automatic Update via Git (Requires Git installed)
echo 2) Dependency Update Only (Use if you manually downloaded and extracted a new ZIP)
echo 3) Cancel
echo.
set /p choice="Enter choice [1-3]: "

if "%choice%"=="1" goto git_update
if "%choice%"=="2" goto dep_update
if "%choice%"=="3" goto end
echo Invalid choice. Exiting.
goto end

:git_update
echo.
echo Pulling latest code from Git...
git pull
if errorlevel 1 (
    echo Git pull failed. Please check your Git installation or use Option 2 after downloading manually.
    goto end
)
goto dep_update

:dep_update
echo.
echo Activating virtual environment and updating dependencies...
if not exist "venv\Scripts\activate.bat" (
    echo Warning: venv\Scripts\activate.bat not found. Are you running this from the root directory?
    goto end
)
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo ===================================
echo  Update Complete! 
echo ===================================
echo Please restart the service (close the running console window and start it again) for changes to take effect.

:end
pause
