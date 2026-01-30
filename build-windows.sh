#!/bin/bash

# --- Configuration ---
APP_NAME="KoupreyTube"
APP_FILE="src/app.py"
LOGO_FILE="assets/download.png"
VERSION="1.0.8"
OUTPUT_DIR="release_windows"

# Colors for output (works in Git Bash)
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}--- Starting Windows build process for ${APP_NAME} v${VERSION} ---${NC}"

# 0. Sanity Check
if [ ! -f "$APP_FILE" ]; then
    echo -e "${RED}Error: Cannot find $APP_FILE.${NC}"
    exit 1
fi

# 1. Python Environment
echo "Installing/Updating required Windows dependencies..."
# Note: secretstorage is NOT needed on Windows, but other deps are
pip install --upgrade pyinstaller yt-dlp mutagen pillow PyQt6 PyQt6-WebEngine

# Cleanup previous builds
rm -rf build dist "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# 2. Build Windows Executable
echo -e "${GREEN}--- Building .EXE with PyInstaller ---${NC}"

# CRITICAL: On Windows, PyInstaller uses ';' as the data separator instead of ':'
pyinstaller --noconfirm \
            --onefile \
            --windowed \
            --name "$APP_NAME" \
            --collect-all PyQt6 \
            --collect-all yt_dlp \
            --add-data "assets/download.png;assets" \
            --add-data "src/player.py;." \
            --add-data "src/downloader.py;." \
            --add-data "src/ui.py;." \
            --icon "$LOGO_FILE" \
            "$APP_FILE"

# 3. Check Result
if [ -f "dist/${APP_NAME}.exe" ]; then
    mv "dist/${APP_NAME}.exe" "$OUTPUT_DIR/"
    echo -e "${GREEN}SUCCESS!${NC}"
    echo -e "Windows executable located at: ${GREEN}$OUTPUT_DIR/${APP_NAME}.exe${NC}"
else
    echo -e "${RED}ERROR: Failed to build Windows .exe${NC}"
    exit 1
fi

# Cleanup build artifacts
rm -rf build "${APP_NAME}.spec"
