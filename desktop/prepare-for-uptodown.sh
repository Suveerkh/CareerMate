#!/bin/bash

# Create a directory for Uptodown packages
mkdir -p uptodown

# Build for all platforms
npm run package-all

# Copy the built packages to the uptodown directory
cp dist/*.dmg uptodown/ 2>/dev/null
cp dist/*.exe uptodown/ 2>/dev/null
cp dist/*.AppImage uptodown/ 2>/dev/null
cp dist/*.deb uptodown/ 2>/dev/null

# Copy the README.md file
cp README.md uptodown/

# Create a screenshots directory
mkdir -p uptodown/screenshots

echo "Packages prepared for Uptodown in the 'uptodown' directory."
echo "Please add screenshots to the 'uptodown/screenshots' directory before uploading."
echo ""
echo "Files prepared:"
ls -la uptodown/

echo ""
echo "Next steps:"
echo "1. Add screenshots to the 'uptodown/screenshots' directory"
echo "2. Register on Uptodown Developers Console: https://developers.uptodown.com/"
echo "3. Create a new app and upload the packages from the 'uptodown' directory"
echo "4. Fill in the app details using the information from README.md"#!/bin/bash

# Create a directory for Uptodown packages
mkdir -p uptodown

# Build for all platforms
npm run package-all

# Copy the built packages to the uptodown directory
cp dist/*.dmg uptodown/ 2>/dev/null
cp dist/*.exe uptodown/ 2>/dev/null
cp dist/*.AppImage uptodown/ 2>/dev/null
cp dist/*.deb uptodown/ 2>/dev/null

# Copy the README.md file
cp README.md uptodown/

# Create a screenshots directory
mkdir -p uptodown/screenshots

echo "Packages prepared for Uptodown in the 'uptodown' directory."
echo "Please add screenshots to the 'uptodown/screenshots' directory before uploading."
echo ""
echo "Files prepared:"
ls -la uptodown/

echo ""
echo "Next steps:"
echo "1. Add screenshots to the 'uptodown/screenshots' directory"
echo "2. Register on Uptodown Developers Console: https://developers.uptodown.com/"
echo "3. Create a new app and upload the packages from the 'uptodown' directory"
echo "4. Fill in the app details using the information from README.md"