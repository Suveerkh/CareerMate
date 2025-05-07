#!/bin/bash

# Exit on error
set -e

echo "Setting up CareerMate Desktop Application..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install npm (it usually comes with Node.js)"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
npm install

# Create icons
echo "Creating application icons..."
./create-icons.sh

echo "Setup complete! You can now run the application with 'npm start'"