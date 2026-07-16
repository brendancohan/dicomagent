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
echo "2) Manual ZIP Update (Download, extract, and provide path)"
echo "3) Cancel"
echo ""
read -p "Enter choice [1-3]: " choice

REQ_CHANGED=0

case $choice in
    1)
        echo ""
        if command -v md5sum &> /dev/null; then
            REQ_BEFORE=$(md5sum requirements.txt 2>/dev/null | awk '{print $1}')
        else
            REQ_BEFORE=$(md5 -q requirements.txt 2>/dev/null)
        fi
        
        echo "Pulling latest code from Git..."
        git pull
        if [ $? -ne 0 ]; then
            echo "Git pull failed. Please check your Git installation or use Option 2."
            exit 1
        fi
        
        if command -v md5sum &> /dev/null; then
            REQ_AFTER=$(md5sum requirements.txt 2>/dev/null | awk '{print $1}')
        else
            REQ_AFTER=$(md5 -q requirements.txt 2>/dev/null)
        fi
        
        if [ "$REQ_BEFORE" != "$REQ_AFTER" ]; then
            REQ_CHANGED=1
        fi
        ;;
    2)
        echo ""
        echo "If you haven't already, please download the latest .zip from:"
        echo "https://github.com/brendancohan/dicomagent/archive/refs/heads/main.zip"
        echo "Extract the .zip file somewhere on your computer."
        echo ""
        read -p "Enter the full path to the extracted directory (or press Enter to cancel): " extracted_path
        
        if [ -z "$extracted_path" ]; then
            echo "Update cancelled."
            exit 0
        fi
        
        if [ ! -d "$extracted_path" ]; then
            echo "Error: Directory does not exist."
            exit 1
        fi
        
        cmp -s requirements.txt "$extracted_path/requirements.txt"
        if [ $? -ne 0 ]; then
            REQ_CHANGED=1
        fi
        
        echo "Copying new files from $extracted_path..."
        cp -R "$extracted_path"/* ./
        
        if [ $? -ne 0 ]; then
            echo "Error copying files. Please check permissions and try again."
            exit 1
        fi
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
echo "==================================="
echo " Update Complete! "
echo "==================================="
if [ $REQ_CHANGED -eq 1 ]; then
    echo "WARNING: The project dependencies have changed in this update."
    echo "You MUST run ./install.sh on the host machine to update your Python environment."
    echo ""
fi
echo "Please restart the service for the changes to take effect."
