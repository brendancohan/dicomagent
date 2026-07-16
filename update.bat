@echo off
setlocal enabledelayedexpansion
echo ===================================
echo    DICOM Agent Service Updater     
echo ===================================

set RAW_URL=https://raw.githubusercontent.com/brendancohan/dicomagent/main/VERSION

if exist "VERSION" (
    set /p LOCAL_VERSION=<VERSION
    set LOCAL_VERSION=!LOCAL_VERSION: =!
) else (
    set LOCAL_VERSION=unknown
)

echo Checking for updates online...
set REMOTE_VERSION=
for /f "delims=" %%i in ('powershell -command "try { (Invoke-WebRequest -Uri '%RAW_URL%' -UseBasicParsing -TimeoutSec 5).Content.Trim() } catch { '' }"') do set REMOTE_VERSION=%%i

if "%REMOTE_VERSION%"=="" (
    echo Warning: Could not check for updates online ^(no internet connection or blocked^).
    goto show_menu
)

if "%LOCAL_VERSION%"=="%REMOTE_VERSION%" (
    echo No updates available. You are already running version %LOCAL_VERSION%.
    set /p exit_choice="Do you want to exit? [Y/n]: "
    if /i "!exit_choice!"=="y" goto end
    if "!exit_choice!"=="" goto end
) else (
    echo An update is available! ^(Current: %LOCAL_VERSION% -^> Latest: %REMOTE_VERSION%^)
)
echo.

:show_menu
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
endlocal
pause
