#!/bin/bash
# build.sh - Build script for Render deployment

# Exit on error
set -e

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories if they don't exist
mkdir -p flask_session
mkdir -p static/reports

# Set permissions
chmod -R 755 .

echo "Build completed successfully!"