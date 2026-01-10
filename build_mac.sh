#!/bin/bash

# --- Configuration ---
APP_NAME="NunTube"
APP_FILE="src/app.py"
LOGO_FILE="assets/download.png"
VERSION="1.0.5"
OUTPUT_DIR="release_mac"

# 1. Install macOS dependencies (requires Homebrew)
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Please install it to manage dependencies."
else
    # macOS Python usually comes with Tcl/Tk, but brew can ensure it
    brew install tcl-tk 
fi

# 2. Update Python Libraries
pip install --upgrade pyinstaller customtkinter yt-dlp mutagen pygame pillow

# 3. Build .app Bundle
# macOS uses --windowed to create a .app folder
pyinstaller --noconfirm \
            --onedir \
            --windowed \
            --name "$APP_NAME" \
            --collect-all customtkinter \
            --collect-all yt_dlp \
            --add-data "$LOGO_FILE:assets" \
            --icon "$LOGO_FILE" \
            "$APP_FILE"

# 4. Create a DMG (Disk Image)
# We use 'create-dmg', a popular tool for this. Install via: brew install create-dmg
if command -v create-dmg &> /dev/null; then
    mkdir -p "$OUTPUT_DIR"
    create-dmg \
      --volname "${APP_NAME} Installer" \
      --window-pos 200 120 \
      --window-size 800 400 \
      --icon-size 100 \
      --icon "$APP_NAME.app" 200 190 \
      --hide-extension "$APP_NAME.app" \
      --app-drop-link 600 185 \
      "$OUTPUT_DIR/${APP_NAME}_${VERSION}.dmg" \
      "dist/"
else
    echo "Warning: 'create-dmg' not found. Only the .app bundle was created in /dist."
fi