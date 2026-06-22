# Tasks for Android APK Build (TDD Workflow)

## Overview
These tasks implement the Android APK build pipeline. Each step follows a test‑driven approach.

| Task | Command | Description |
|------|---------|-------------|
| **T001** | `pnpm install` | Ensure PNPM and all dependencies are installed in tree. |
| **T002** | `pnpm add -D electron-builder@latest` | Add latest electron‑builder to devDependencies. |
| **T003** | `npm run build:android` | Build Android APK locally; verify error messages for missing env vars. |
| **T004** | `docker build -f Dockerfile.android -t thuis-android-builder .` | Ensure Dockerfile.android builds without errors. |
| **T005** | `docker run --rm -v $PWD:/app thuis-android-builder` | Run container and create `dist/thuis-android-arm64-*.apk`. |
| **T006** | `./scripts/integration-test.sh` | Launch Android emulator, install APK, verify launch on API 31. |
| **T007** | `pnpm test` | Run unit tests for Android signing config; ensure zero failures. |
| **T008** | `git tag v${GITHUB_RUN_NUMBER}` | Tag commit; push tag to trigger GitHub Release upload. |
| **T009** | Verify APK in GitHub Release | Confirm APK appears in Release assets under tag name. |

**Notes**  
- Each task must pass before moving to the next.  
- All commands assume the project root is `~/docker-stack/06-apps/thuis`.  
- Use `pnpm run build:android` instead of `pnpm run build` to invoke the Android build script.  
- `integration-test.sh` expects Android SDK platform‑tools to be available in container PATH.