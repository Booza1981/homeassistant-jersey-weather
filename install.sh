#!/bin/bash

# Jersey Weather Integration Installer for Home Assistant

echo "Jersey Weather Integration Installer"
echo "===================================="

# Check if Home Assistant config directory is provided
if [ -z "$1" ]; then
  echo "Please provide the path to your Home Assistant config directory."
  echo "Usage: ./install.sh /path/to/homeassistant/config"
  exit 1
fi

HA_CONFIG_DIR="$1"
CUSTOM_COMPONENTS_DIR="$HA_CONFIG_DIR/custom_components"
TARGET_DIR="$CUSTOM_COMPONENTS_DIR/jersey_weather"

# Check if config directory exists
if [ ! -d "$HA_CONFIG_DIR" ]; then
  echo "Error: The provided directory does not exist."
  exit 1
fi

# Create custom_components directory if it doesn't exist
if [ ! -d "$CUSTOM_COMPONENTS_DIR" ]; then
  echo "Creating custom_components directory..."
  mkdir -p "$CUSTOM_COMPONENTS_DIR"
fi

# Remove existing installation if it exists
if [ -d "$TARGET_DIR" ]; then
  echo "Removing existing installation..."
  rm -rf "$TARGET_DIR"
fi

# Create target directory
mkdir -p "$TARGET_DIR"

# Copy files
echo "Installing Jersey Weather integration..."
cp -r ./custom_components/jersey_weather/* "$TARGET_DIR/"

# Set permissions
chmod -R 755 "$TARGET_DIR"

echo "Installation complete!"
echo "Please restart Home Assistant to complete the installation."
echo "After restarting, add the integration through the UI by going to:"
echo "Configuration -> Integrations -> Add Integration -> Jersey Weather"
