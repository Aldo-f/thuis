# Android APK Build Specification

## Goal
Produce a signed Android APK (`app-arm64-v<version>.apk`) from the existing Electron source.

## User Stories
1. Mobile users can install and launch the app, seeing the same UI as the desktop Electron client.
2. CI pipeline produces a reproducible, deterministic APK on every successful push to `main`.
3. Security audit requires the APK signed with our internal keystore (env-protected) and build logs archived.

## Acceptance Criteria
- `npm run build:electron` continues to produce desktop installers (unchanged).
- `npm run build:android` creates `dist/thuis-android-arm64-v<ver>.apk`.
- APK runs on Android 12+ (API 31) on ARM64 devices.
- APK signed with keystore via `$ANDROID_KEYSTORE_PATH` and `$ANDROID_KEYSTORE_PASS`.
- CI publishes APK to GitHub Releases (tag `v<ver>`).

## Edge Cases / Non‑Functional
- Fail fast if `ANDROID_SDK_ROOT` is missing or NDK version incompatible.
- Run lint + unit tests (`pnpm test`) before any build; abort on failures.
- Build must be reproducible: `NODE_OPTIONS=--max-old-space-size=4096` and lock PNPM lockfile.