# Implementation Plan for Android APK Build

## Overview
This plan outlines the steps required to extend the existing Electron build pipeline to produce a signed Android APK. It builds upon the current Electron configuration and adds Android-specific tooling and CI integration.

## Phases
1. **Prepare Environment** - Ensure Docker container includes Android SDK/NDK
2. **Configure electron-builder** - Add Android build configuration
3. **Add build script** - Create `build:android` npm script
4. **Create Dockerfile.android** - Extend dev Docker image with Android SDK
5. **Write unit and integration tests** - Verify Android-specific code
6. **Implement GitHub Actions workflow** - Automate build, sign, and publish
7. **Local build verification** - Build and test APK on emulator

## Detailed Tasks

### Phase 1: Prepare Environment
- [ ] Add Android SDK/NDK to Dockerfile (see Dockerfile.android section)
- [ ] Ensure `gradle` dependency is available in `electron-app`

### Phase 2: Configure electron-builder
- [ ] Patch `electron-builder.yml` to add Android section (see §7 in SPEC.md)
- [ ] Verify signing configuration uses environment variables

### Phase 3: Add build script
- [ ] Add `build:android` script to `package.json` in `electron-app` package.json
- [ ] Ensure script uses `pnpm run electron-builder -p android`

### Phase 4: Dockerfile.android
- [ ] Create `Dockerfile.android` in root of `06-apps/thuis`
- [ ] Base image: `node:20-alpine`
- [ ] Install Java 17, Android SDK command-line tools, NDK 25.2.9519653, platforms (API 31)
- [ ] Set `ANDROID_SDK_ROOT` and update PATH
- [ ] Copy repo, install dependencies, set build command

### Phase 5: Tests
- [ ] Write unit test for Android signing config in `packages/electron-app/src/main/electron-android.test.ts`
- [ ] Create integration test script that launches emulator and verifies APK installation

### Phase 6: GitHub Actions
- [ ] Create `.github/workflows/android-apk.yml`
- [ ] Store keystore as Base64 secret `ANDROID_KEYSTORE_BASE64`
- [ ] Decode keystore in workflow before Docker build
- [ ] Upload APK to GitHub Releases on tag

### Phase 7: Local Verification
- [ ] Build Docker image: `docker build -f Dockerfile.android -t thuis-android-builder .`
- [ ] Run container: `docker run --rm -v $PWD:/app thuis-android-builder`
- [ ] Verify APK exists in `dist/`
- [ ] Test installation on Android emulator