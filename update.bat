@echo off
setlocal enabledelayedexpansion
pushd "%~dp0"
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
echo 2) Manual ZIP Update (Download, extract, and provide path)
echo 3) Cancel
echo.
set /p choice="Enter choice [1-3]: "

if "%choice%"=="1" goto git_update
if "%choice%"=="2" goto manual_update
if "%choice%"=="3" goto end
echo Invalid choice. Exiting.
goto end

:git_update
echo.
git --version >nul 2>&1
if errorlevel 1 (
    echo Git not found. Cannot update via Git. Please use Option 2.
    goto end
)
if not exist ".git\" (
    echo Not a git repository. Cannot update via Git. Please use Option 2.
    goto end
)

:: Store hash of current requirements
certutil -hashfile requirements.txt MD5 | find /i /v "certutil" | find /i /v "hash" > req_hash_before.txt
set /p REQ_BEFORE=<req_hash_before.txt
del req_hash_before.txt

echo Pulling latest code from Git...
git pull
if errorlevel 1 (
    echo Git pull failed. Please check your Git installation or use Option 2.
    goto end
)

certutil -hashfile requirements.txt MD5 | find /i /v "certutil" | find /i /v "hash" > req_hash_after.txt
set /p REQ_AFTER=<req_hash_after.txt
del req_hash_after.txt

if not "!REQ_BEFORE!"=="!REQ_AFTER!" (
    set REQ_CHANGED=1
) else (
    set REQ_CHANGED=0
)
goto finish_update

:manual_update
echo.
echo If you haven't already, please download the latest .zip from:
echo https://github.com/brendancohan/dicomagent/archive/refs/heads/main.zip
echo Extract the .zip file somewhere on your computer.
echo.
set /p extracted_path="Enter the full path to the extracted directory (or press Enter to cancel): "

if "!extracted_path!"=="" (
    echo Update cancelled.
    goto end
)

if not exist "!extracted_path!\" (
    echo Error: Directory does not exist.
    goto end
)

fc requirements.txt "!extracted_path!\requirements.txt" >nul 2>&1
if errorlevel 1 (
    set REQ_CHANGED=1
) else (
    set REQ_CHANGED=0
)

echo Copying new files from !extracted_path!...
xcopy "!extracted_path!\*" .\ /E /Y /C /Q
if errorlevel 1 (
    echo Error copying files. Please check permissions and try again.
    goto end
)
goto finish_update

:finish_update
echo.
echo ===================================
echo  Update Complete! 
echo ===================================
if "!REQ_CHANGED!"=="1" (
    echo WARNING: The project dependencies have changed in this update.
    echo You MUST run install.bat on the host machine to update your Python environment.
    echo.
)
echo Please restart the service (close the running console window and start it again) for changes to take effect.

:end
popd
endlocal
pause
