#!/bin/bash

# Check if both arguments are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Error: Code signing identity and app path required!"
    echo ""
    echo "Usage: $0 \"Developer ID Application: Your Name (TEAM_ID)\" \"/path/to/app.app\""
    echo ""
    echo "Example: $0 \"Developer ID Application: John Smith (ABC123DEF4)\" \"dist/WhackEd4.app\""
    echo ""
    echo "To find your signing identity:"
    echo "  security find-identity -v -p codesigning"
    echo ""
    echo "To get a Developer ID certificate:"
    echo "  1. Join Apple Developer Program (https://developer.apple.com/programs/)"
    echo "  2. Create a Developer ID Application certificate in your Apple Developer account"
    echo "  3. Download and install the certificate in Keychain Access"
    echo ""
    exit 1
fi

IDENTITY="$1"
APP="$2"
ENTITLEMENTS="$(dirname "$0")/entitlements.plist"

echo "Signing nested binaries..."

# Sign all .so files (Python extensions)
find "$APP" -name "*.so" -exec codesign --force --timestamp \
    --options runtime \
    --entitlements "$ENTITLEMENTS" \
    --sign "$IDENTITY" {} \;

# Sign all .dylib files (dynamic libraries)
find "$APP" -name "*.dylib" -exec codesign --force --timestamp \
    --options runtime \
    --entitlements "$ENTITLEMENTS" \
    --sign "$IDENTITY" {} \;

# Sign Python executable
find "$APP/Contents/MacOS" -type f -perm +111 -exec codesign --force --timestamp \
    --options runtime \
    --entitlements "$ENTITLEMENTS" \
    --sign "$IDENTITY" {} \;

# Sign any frameworks (wxPython frameworks)
find "$APP/Contents/Frameworks" -name "*.framework" -exec codesign --force --timestamp \
    --options runtime \
    --entitlements "$ENTITLEMENTS" \
    --sign "$IDENTITY" {} \;

echo "Signing main app bundle..."
codesign --force --timestamp \
    --options runtime \
    --entitlements "$ENTITLEMENTS" \
    --sign "$IDENTITY" \
    "$APP"

echo "Verifying signature..."
codesign --verify --deep --strict --verbose=2 "$APP"
spctl --assess --verbose=4 --type execute "$APP"

echo "Done!"
