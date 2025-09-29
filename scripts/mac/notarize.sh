#!/bin/bash

# Check if all required arguments are provided
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
    echo "Error: App path, Apple ID, team ID, and app-specific password required!"
    echo ""
    echo "Usage: $0 \"/path/to/app.app\" \"your-apple-id@example.com\" \"TEAM_ID\" \"app-specific-password\""
    echo ""
    echo "Example: $0 \"dist/WhackEd4.app\" \"john@example.com\" \"ABC123DEF4\" \"abcd-efgh-ijkl-mnop\""
    echo ""
    echo "To get required credentials:"
    echo "  1. Apple ID: Your Apple Developer account email"
    echo "  2. Team ID: Found in Apple Developer account > Membership details"
    echo "  3. App-specific password: Generate at appleid.apple.com > Sign-In and Security > App-Specific Passwords"
    echo ""
    echo "IMPORTANT: Never commit credentials to git. Use environment variables or secure storage."
    echo ""
    exit 1
fi

APP_PATH="$1"
APPLE_ID="$2"
TEAM_ID="$3"
APP_PASSWORD="$4"

# Extract app name for the zip file
APP_NAME=$(basename "$APP_PATH" .app)
ZIP_FILE="${APP_NAME}.zip"

echo "Creating zip archive for notarization..."
ditto -c -k --keepParent "$APP_PATH" "$ZIP_FILE"

if [ $? -ne 0 ]; then
    echo "Error: Failed to create zip archive"
    exit 1
fi

echo "Submitting for notarization..."
NOTARIZE_OUTPUT=$(xcrun notarytool submit "$ZIP_FILE" \
    --apple-id "$APPLE_ID" \
    --team-id "$TEAM_ID" \
    --password "$APP_PASSWORD" \
    --wait)

echo "$NOTARIZE_OUTPUT"

# Extract submission ID from output
SUBMISSION_ID=$(echo "$NOTARIZE_OUTPUT" | grep "id:" | head -1 | awk '{print $2}')

if echo "$NOTARIZE_OUTPUT" | grep -q "status: Accepted"; then
    echo "Notarization successful!"

    echo "Stapling notarization to app..."
    xcrun stapler staple "$APP_PATH"

    if [ $? -eq 0 ]; then
        echo "Stapling successful!"
        echo "Verifying notarization..."
        spctl --assess --verbose=4 --type execute "$APP_PATH"
    else
        echo "Warning: Stapling failed"
    fi

else
    echo "Notarization failed!"
    if [ ! -z "$SUBMISSION_ID" ]; then
        echo "Getting detailed log for submission $SUBMISSION_ID..."
        xcrun notarytool log "$SUBMISSION_ID" \
            --apple-id "$APPLE_ID" \
            --team-id "$TEAM_ID" \
            --password "$APP_PASSWORD"
    fi
    exit 1
fi

# Clean up zip file
echo "Cleaning up..."
rm -f "$ZIP_FILE"

echo "Done! Your app is now notarized and ready for distribution."