#!/bin/bash
# publish-update.sh - Script to publish a new version of CareerMate

# Exit on error
set -e

# Check if version is provided
if [ -z "$1" ]; then
    echo "Usage: ./publish-update.sh <version>"
    echo "Example: ./publish-update.sh 1.0.1"
    exit 1
fi

NEW_VERSION=$1

# Update version in package.json
echo "Updating version to $NEW_VERSION in package.json..."
sed -i '' "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" package.json

# Commit the version change
echo "Committing version change..."
git add package.json
git commit -m "Bump version to $NEW_VERSION"

# Create a new tag
echo "Creating git tag v$NEW_VERSION..."
git tag "v$NEW_VERSION"

# Push changes and tag
echo "Pushing changes and tag to remote repository..."
git push
git push --tags

# Build and publish the app
echo "Building and publishing the app..."
npm run publish

echo "Update published successfully!"
echo "Version $NEW_VERSION is now available for users to download."