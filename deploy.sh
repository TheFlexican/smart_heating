#!/bin/bash
# Deploy script for Smart Heating to HAOS

# Configuration
HA_HOST="homeassistant.local"  # Adjust to your HA IP/hostname
SOURCE_DIR="/Users/ralf/git/zone_heater_manager/custom_components/smart_heating"
DEST_DIR="/Volumes/config/custom_components/smart_heating"

echo "🚀 Deploying Smart Heating to Home Assistant OS..."

# Check if Samba share is mounted
if [ ! -d "/Volumes/config" ]; then
    echo "📁 Mounting Samba share..."
    open "smb://${HA_HOST}"
    sleep 3
fi

# Check again
if [ ! -d "/Volumes/config" ]; then
    echo "❌ Error: Could not mount Samba share"
    echo "   Make sure Samba add-on is installed and running"
    exit 1
fi

# Create custom_components directory if it doesn't exist
mkdir -p /Volumes/config/custom_components

# Copy files
echo "📦 Copying files..."
cp -r "${SOURCE_DIR}" "${DEST_DIR}"

if [ $? -eq 0 ]; then
    echo "✅ Files copied successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Go to Settings → System → Restart → Quick Reload"
    echo "2. Go to Settings → Devices & Services → Add Integration"
    echo "3. Search for 'Smart Heating'"
    echo ""
    echo "Or restart HA completely for clean start"
else
    echo "❌ Error copying files"
    exit 1
fi
