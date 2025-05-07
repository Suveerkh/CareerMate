#!/bin/bash
# package.sh - Script to package CareerMate desktop app for Mac and Windows

# Exit on error
set -e

# Create icons directory if it doesn't exist
mkdir -p icons

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed. Please install Node.js and try again."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is required but not installed. Please install npm and try again."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
npm install

# Package for macOS
echo "Packaging for macOS..."
npm run package-mac

# Package for Windows
echo "Packaging for Windows..."
npm run package-win

echo "Packaging complete! Check the release-builds directory for the packaged applications."