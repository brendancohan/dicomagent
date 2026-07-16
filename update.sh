#!/bin/bash

echo "==================================="
echo "   DICOM Agent Service Updater     "
echo "==================================="
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
