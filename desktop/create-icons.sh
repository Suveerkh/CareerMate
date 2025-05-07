#!/bin/bash

# Create icons directory if it doesn't exist
mkdir -p /Users/Sakshi/PycharmProjects/CareerMate/desktop/icons

# Copy the logo to the icons directory
cp "/Users/Sakshi/PycharmProjects/CareerMate/static/images/career_mate - logo.png" /Users/Sakshi/PycharmProjects/CareerMate/desktop/icons/icon.png

echo "Icon copied successfully to desktop/icons/icon.png"
echo ""
echo "For production builds, you'll need to convert this PNG to:"
echo "- icon.icns for macOS (using iconutil or online converters)"
echo "- icon.ico for Windows (using online converters)"
echo ""
echo "For development, the PNG file is sufficient."