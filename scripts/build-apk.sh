#!/bin/bash
set -e

# Build Android APK using Docker
# Usage: ./scripts/build-apk.sh

cd "$(dirname "$0")/.."

echo "Building Android APK..."
docker build -f Dockerfile.android -t thuis-android-builder .

echo "Running build..."
docker run --rm \
  -v "$(pwd):/app" \
  -e ANDROID_KEYSTORE_PATH="/tmp/keystore.jks" \
  -e ANDROID_KEYSTORE_PASS="${ANDROID_KEYSTORE_PASS:-changeit}" \
  -e ANDROID_KEY_ALIAS="${ANDROID_KEY_ALIAS:-thuis}" \
  -e ANDROID_KEY_PASS="${ANDROID_KEY_PASS:-changeit}" \
  thuis-android-builder

echo "APK build complete. Check dist/ for output."