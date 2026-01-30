#!/bin/bash

# --- Configuration ---
# --- Configuration ---
APP_NAME="kouprey"
APP_FILE="src/app.py"
LOGO_FILE="assets/download.png" # Make sure this file exists!
VERSION="1.0.8"
MAINTAINER="Kouprey Tube"
OUTPUT_DIR="release"
DEB_ROOT="${APP_NAME}_deb"
DEB_PACKAGE_NAME="${APP_NAME}_${VERSION}_amd64.deb"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}--- Starting build process for ${APP_NAME} v${VERSION} ---${NC}"

# 0. Sanity Check
if [ ! -f "$APP_FILE" ]; then
    echo -e "${RED}Error: Cannot find $APP_FILE. Are you in the root folder?${NC}"
    exit 1
fi

if [ ! -f "$LOGO_FILE" ]; then
    echo -e "${RED}Error: Cannot find icon at $LOGO_FILE.${NC}"
    exit 1
fi

# 1. Dependency Check
echo "Checking system dependencies..."
# Removed python3-tk check as we are using PyQt6 and bundling it

# 2. Python Environment
echo "Updating Python libraries..."
pip install --upgrade pyinstaller yt-dlp mutagen pillow PyQt6 PyQt6-WebEngine

# Cleanup previous builds
rm -rf build dist "$DEB_ROOT" "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# 3. Build Linux Executable
echo -e "${GREEN}--- Building Binary with PyInstaller ---${NC}"

# Note: separator for add-data is ':' on Linux
pyinstaller --noconfirm \
            --onefile \
            --windowed \
            --name "$APP_NAME" \
            --collect-all PyQt6 \
            --collect-all yt_dlp \
            --add-data "$LOGO_FILE:assets" \
            --icon "$LOGO_FILE" \
            "$APP_FILE"

if [ ! -f "dist/${APP_NAME}" ]; then
    echo -e "${RED}ERROR: PyInstaller failed to create the binary.${NC}"
    exit 1
fi

# 4. Create Debian Structure
echo -e "${GREEN}--- Creating Debian Package ---${NC}"
mkdir -p "$DEB_ROOT/usr/bin"
mkdir -p "$DEB_ROOT/DEBIAN"
mkdir -p "$DEB_ROOT/usr/share/applications"
mkdir -p "$DEB_ROOT/usr/share/pixmaps"

# Copy Binary
cp "dist/${APP_NAME}" "$DEB_ROOT/usr/bin/"
chmod 755 "$DEB_ROOT/usr/bin/$APP_NAME"

# Copy Icon (Standard Linux path /usr/share/pixmaps/appname.png)
cp "$LOGO_FILE" "$DEB_ROOT/usr/share/pixmaps/$APP_NAME.png"

# 5. Create Desktop Entry
# Note: Icon=kouprey works because we placed kouprey.png in /usr/share/pixmaps
cat > "$DEB_ROOT/usr/share/applications/$APP_NAME.desktop" <<EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=Kouprey Tube
Comment=YouTube Channel and Playlist Downloader
Exec=/usr/bin/$APP_NAME
Icon=$APP_NAME
Terminal=false
StartupWMClass=$APP_NAME
Categories=Utility;Network;AudioVideo;
EOL

# 6. Create Control File
INST_SIZE=$(du -s "$DEB_ROOT" | awk '{print $1}')

cat > "$DEB_ROOT/DEBIAN/control" <<EOL
Package: $APP_NAME
Version: $VERSION
Architecture: amd64
Maintainer: $MAINTAINER
Installed-Size: $INST_SIZE
Priority: optional
Section: utils
Description: Kouprey Tube Downloader
 A simple GUI downloader for YouTube Channels and Playlists.
 Depends: python3
EOL

# 7. Post-Install Script
cat > "$DEB_ROOT/DEBIAN/postinst" <<EOL
#!/bin/bash
update-desktop-database /usr/share/applications
EOL
chmod 755 "$DEB_ROOT/DEBIAN/postinst"

# 8. Build .deb
dpkg-deb --build --root-owner-group "$DEB_ROOT"

if [ $? -eq 0 ]; then
    mv "${DEB_ROOT}.deb" "$OUTPUT_DIR/$DEB_PACKAGE_NAME"
    echo -e "${GREEN}SUCCESS!${NC}"
    echo -e "Installer located at: ${GREEN}$OUTPUT_DIR/$DEB_PACKAGE_NAME${NC}"
else
    echo -e "${RED}ERROR: Failed to build .deb${NC}"
    exit 1
fi

sudo rm -rf /build /dist /kouprey_deb