# Implementation Plan: VRT MAX E2E Login and Download Tests

## Summary
Add end-to-end Playwright tests covering the full VRT MAX login flow (including SSO authentication via auth server proxy) and downloading the latest "Thuis" episode. Tests will verify the complete user journey from vault initialization to successful episode download initiation.

## Technical Context
- **Test Framework**: Playwright with TypeScript
- **Target**: Local development server with auth server proxy
- **Credentials**: Uses environment variables `VRT_USERNAME` and `VRT_PASSWORD`
- **Scope**: Full E2E flow including vault setup, provider login, episode discovery, and download initiation

## Tasks

### Wave 1 — Test Infrastructure Setup
- [x] **T1**: Create E2E test directory structure
  - Create `packages/web-app/e2e/` directory
  - Add `playwright.config.ts` configuration
  - Configure test timeout and retry settings

- [x] **T2**: Install Playwright test dependencies
  - Add `@playwright/test` to `packages/web-app/package.json`
  - Add necessary devDependencies for test execution

- [x] **T3**: Create test utility helpers
  - Login helper functions for vault operations
  - Episode discovery utilities
  - Download initiation verification

### Wave 2 — Login Flow Tests
- [x] **T4**: Test vault initialization and setup
  - Verify vault creation with master password
  - Test vault unlock flow

- [x] **T5**: Test VRT MAX provider credential addition
  - Verify credential form submission triggers auth server login
  - Confirm successful credential storage in vault

- [x] **T6**: Test VRT MAX SSO login via auth server
  - Validate auth server proxy correctly forwards to VRT MAX
  - Confirm tokens are properly returned and stored

### Wave 3 — Episode Discovery and Download Tests
- [x] **T7**: Test Thuis episode discovery
  - Verify ability to find latest Thuis episode
  - Test navigation to episode detail page

- [x] **T8**: Test download initiation for Thuis episode
  - Verify download button/link triggers download process
  - Confirm download appears in download queue
  - Validate download job starts correctly

### Wave 4 — Test Execution and Verification
- [x] **T9**: Create test execution script
  - Add npm script for running E2E tests
  - Configure test to start dev server and auth server

- [x] **T10**: Run and verify test suite
    - Execute all E2E tests
    - Confirm zero test failures
    - Verify test coverage of critical paths

## Success Criteria
- All E2E tests pass consistently
- Tests validate real VRT MAX SSO login via auth server proxy
- Download initiation for latest Thuis episode works correctly
- No test flakiness or false positives
- Tests run in reasonable time (<2 minutes for full suite)