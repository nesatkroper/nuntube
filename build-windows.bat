@echo off
set APP_NAME=KoupreyTube
set APP_FILE=src\app.py
set LOGO_FILE=assets\download.png
set OUTPUT_DIR=release_windows

echo ---------------------------------------------------
echo Building %APP_NAME% for Windows...
echo ---------------------------------------------------

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: Install/Update dependencies
echo Installing dependencies...
pip install --upgrade pyinstaller yt-dlp mutagen pillow PyQt6 PyQt6-WebEngine

:: Cleanup
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist %OUTPUT_DIR% rd /s /q %OUTPUT_DIR%
mkdir %OUTPUT_DIR%

:: Build
echo ---------------------------------------------------
echo Running PyInstaller...
echo ---------------------------------------------------
pyinstaller --noconfirm ^
            --onefile ^
            --windowed ^
            --name "%APP_NAME%" ^
            --collect-all PyQt6 ^
            --collect-all yt_dlp ^
            --add-data "assets/download.png;assets" ^
            --add-data "src/player.py;." ^
            --add-data "src/downloader.py;." ^
            --add-data "src/ui.py;." ^
            --icon "%LOGO_FILE%" ^
            "%APP_FILE%"

:: Check Result
if exist "dist\%APP_NAME%.exe" (
    move "dist\%APP_NAME%.exe" "%OUTPUT_DIR%\"
    echo ---------------------------------------------------
    echo SUCCESS! 
    echo Executable is in: %OUTPUT_DIR%\%APP_NAME%.exe
    echo ---------------------------------------------------
) else (
    echo.
    echo ERROR: Build failed.
)

:: Cleanup
if exist build rd /s /q build
if exist %APP_NAME%.spec del /q %APP_NAME%.spec

pause
