#!/bin/bash
set -e

# Check arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <path-to-app-bundle> <version>"
    echo "Example: $0 dist/WhackEd4.app 1.3.2"
    exit 1
fi

APP_BUNDLE="$1"
VERSION="$2"
DMG_NAME="WhackEd4-${VERSION}.dmg"
VOLUME_NAME="WhackEd4"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKDROP="$SCRIPT_DIR/dmg-backdrop.png"

# Verify app bundle exists
if [ ! -d "$APP_BUNDLE" ]; then
    echo "Error: App bundle not found at $APP_BUNDLE"
    exit 1
fi

# Verify backdrop exists
if [ ! -f "$BACKDROP" ]; then
    echo "Error: Backdrop image not found at $BACKDROP"
    exit 1
fi

# Create temporary directory for DMG contents
TMP_DMG_DIR=$(mktemp -d)
echo "Creating DMG contents in $TMP_DMG_DIR"

# Copy app bundle to temp directory
echo "Copying app bundle..."
cp -R "$APP_BUNDLE" "$TMP_DMG_DIR/"

# Create Applications symlink
echo "Creating Applications symlink..."
ln -s /Applications "$TMP_DMG_DIR/Applications"

# Create temporary DMG
TMP_DMG=$(mktemp).dmg
echo "Creating temporary DMG..."
hdiutil create -volname "$VOLUME_NAME" -srcfolder "$TMP_DMG_DIR" -ov -format UDRW "$TMP_DMG"

# Mount the temporary DMG
echo "Mounting DMG..."
MOUNT_DIR=$(hdiutil attach -readwrite -noverify -noautoopen "$TMP_DMG" | grep Volumes | awk '{print $3}')

# Wait for mount
sleep 2

# Copy backdrop image to DMG
echo "Setting up backdrop..."
mkdir -p "$MOUNT_DIR/.background"
cp "$BACKDROP" "$MOUNT_DIR/.background/backdrop.png"

# Set up DMG appearance with AppleScript
echo "Configuring DMG appearance..."
osascript <<EOF
tell application "Finder"
    tell disk "$VOLUME_NAME"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {100, 100, 605, 500}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 128
        set background picture of viewOptions to file ".background:backdrop.png"

        -- Position app icon on the left
        set position of item "$(basename "$APP_BUNDLE")" of container window to {50, 160}

        -- Position Applications symlink on the right
        set position of item "Applications" of container window to {370, 160}

        update without registering applications
        delay 2
        close
    end tell
end tell
EOF

# Sync and unmount
echo "Finalizing DMG..."
sync
hdiutil detach "$MOUNT_DIR"

# Convert to compressed read-only DMG
echo "Compressing DMG..."
rm -f "$DMG_NAME"
hdiutil convert "$TMP_DMG" -format UDZO -imagekey zlib-level=9 -o "$DMG_NAME"

# Clean up
echo "Cleaning up..."
rm -f "$TMP_DMG"
rm -rf "$TMP_DMG_DIR"

echo "DMG created successfully: $DMG_NAME"