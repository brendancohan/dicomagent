#!/bin/bash

echo "==================================="
echo "   DICOM Agent Service Updater     "
echo "==================================="

RAW_URL="https://raw.githubusercontent.com/brendancohan/dicomagent/main/VERSION"

if [ -f "VERSION" ]; then
    LOCAL_VERSION=$(cat VERSION | tr -d '[:space:]')
else
    LOCAL_VERSION="unknown"
fi

echo "Checking for updates online..."
if command -v curl &> /dev/null; then
    REMOTE_VERSION=$(curl -s -f "$RAW_URL" | tr -d '[:space:]')
elif command -v wget &> /dev/null; then
    REMOTE_VERSION=$(wget -qO- "$RAW_URL" | tr -d '[:space:]')
else
    REMOTE_VERSION=""
fi

if [ -z "$REMOTE_VERSION" ]; then
    echo "Warning: Could not check for updates online (no curl or wget found, or no internet connection)."
elif [ "$LOCAL_VERSION" = "$REMOTE_VERSION" ]; then
    echo "No updates available. You are already running version $LOCAL_VERSION."
    read -p "Do you want to exit? [Y/n]: " exit_choice
    if [[ -z "$exit_choice" || "$exit_choice" =~ ^[Yy]$ ]]; then
        echo "Exiting."
        exit 0
    fi
else
    echo "An update is available! (Current: $LOCAL_VERSION -> Latest: $REMOTE_VERSION)"
fi
echo ""

echo "Please select your update method:"
echo "1) Automatic Update via Git (Requires Git installed)"
echo "2) Dependency Update Only (Use if you manually downloaded and extracted a new ZIP)"
echo "3) Cancel"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "Pulling latest code from Git..."
        git pull
        if [ $? -ne 0 ]; then
            echo "Git pull failed. Please check your Git installation or use Option 2 after downloading manually."
            exit 1
        fi
        ;;
    2)
        echo ""
        echo "Skipping Git pull. Assuming new files have already been manually extracted over the old ones."
        ;;
    3)
        echo ""
        echo "Update cancelled."
        exit 0
        ;;
    *)
        echo ""
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "Activating virtual environment and updating dependencies..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Warning: venv/bin/activate not found. Are you running this from the root directory?"
    exit 1
fi

echo ""
echo "==================================="
echo " Update Complete! "
echo "==================================="
echo "Please restart the service for the changes to take effect."
