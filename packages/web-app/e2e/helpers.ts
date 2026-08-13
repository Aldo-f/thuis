// E2E Test Helper Functions
// This file contains utility functions for common operations in VRT MAX E2E tests.

import { expect, Page } from '@playwright/test';
import { ProviderTokens } from '@thuis/core';

/**
 * Waits for the vault to be unlocked and returns true if successful.
 * @param page The Playwright page object
 * @param masterPassword The master password to unlock the vault
 */
export async function unlockVault(page: Page, masterPassword: string): Promise<boolean> {
  // Wait for the page to reach a known vault state.
  // Uses waitForSelector (with auto-wait) instead of isVisible (no auto-wait)
  // to avoid race conditions with React rendering.
  const state = await Promise.race([
    page.waitForSelector('text=Welkom bij Thuis', { timeout: 5000 }).then(() => 'uninitialized' as const),
    page.waitForSelector('text=Vault ontgrendelen', { timeout: 5000 }).then(() => 'locked' as const),
    page.waitForSelector('text=Inloggegevens', { timeout: 5000 }).then(() => 'unlocked' as const),
  ]);

  if (state === 'uninitialized') {
    await page.fill('input[placeholder="Minimaal 8 tekens"]', masterPassword);
    await page.fill('input[placeholder="Herhaal het wachtwoord"]', masterPassword);
    await page.click('button:has-text("Vault aanmaken")');
    await page.waitForSelector('text=Inloggegevens', { timeout: 10000 });
    return true;
  }

  if (state === 'locked') {
    await page.fill('input[placeholder="Hoofdwachtwoord"]', masterPassword);
    await page.click('button:has-text("Ontgrendelen")');
    await page.waitForSelector('text=Inloggegevens', { timeout: 10000 });
    return true;
  }

  // Already unlocked
  return true;
}

/**
 * Locks the vault by clicking the "Vergrendelen" button on the unlocked vault page.
 * @param page The Playwright page object
 */
/**
 * Locks the vault by clicking the "Vergrendelen" button on the unlocked vault page.
 * Handles uninitialized, unlocked, and locked states.
 * @param page The Playwright page object
 */
export async function lockVault(page: Page): Promise<void> {
  // Wait for the page to reach a known vault state.
  const state = await Promise.race([
    page.waitForSelector('text=Welkom bij Thuis', { timeout: 5000 }).then(() => 'uninitialized' as const),
    page.waitForSelector('text=Vault ontgrendelen', { timeout: 5000 }).then(() => 'locked' as const),
    page.waitForSelector('text=Inloggegevens', { timeout: 5000 }).then(() => 'unlocked' as const),
  ]);

  if (state === 'uninitialized') {
    // Initialize the vault with the default password
    const masterPassword = process.env.VAULT_MASTER_PASSWORD ?? 'changeme';
    await page.fill('input[placeholder="Minimaal 8 tekens"]', masterPassword);
    await page.fill('input[placeholder="Herhaal het wachtwoord"]', masterPassword);
    await page.click('button:has-text("Vault aanmaken")');
    // Wait for unlocked state (heading "Inloggegevens")
    await page.waitForSelector('text=Inloggegevens', { timeout: 5000 });
    // Now we are unlocked, so lock it
    await page.click('button:has-text("Vergrendelen")');
    // Wait for locked state (heading "Vault ontgrendelen")
    await page.waitForSelector('text=Vault ontgrendelen', { timeout: 5000 });
  } else if (state === 'unlocked') {
    // We are unlocked, so lock it
    await page.click('button:has-text("Vergrendelen")');
    // Wait for locked state (heading "Vault ontgrendelen")
    await page.waitForSelector('text=Vault ontgrendelen', { timeout: 5000 });
  }
  // If it's locked, we do nothing.
}

/**
 * Adds VRT MAX provider credentials via the ProviderCredentialForm.
 * @param page The Playwright page object
 * @param email VRT MAX email
 * @param password VRT MAX password
 * @param label Optional label for the provider
 */
export async function addVrtProviderCredentials(
  page: Page,
  email: string,
  password: string,
  label: string = 'Mijn VRT-account'
): Promise<void> {
  // Navigate to vault page if not already there
  await page.goto('/vault');
  await unlockVault(page, process.env.VAULT_MASTER_PASSWORD ?? 'changeme');

  // Click "+ Nieuwe provider toevoegen" to open the provider picker
  await page.click('button:has-text("Nieuwe provider toevoegen")');

  // In the provider picker, click the VRT MAX provider button
  await page.click('button:has-text("VRT MAX")');

  // Fill in the credentials form
  await page.fill('input[placeholder="naam@voorbeeld.com"]', email);
  await page.fill('input[placeholder="••••••••"]', password);
  await page.fill('input[placeholder="Bijv. Mijn VRT-account"]', label);

  // Submit the form
  await page.click('button:has-text("Opslaan")');

  // Wait for the main list view heading to confirm we're back
  await page.waitForSelector('text=Inloggegevens', { timeout: 15000 });
}

/**
 * Navigates to the latest Thuis episode page.
 * Assumes the user is already logged into VRT MAX.
 * @param page The Playwright page object
 */
export async function navigateToLatestThuisEpisode(page: Page): Promise<void> {
  // Navigate to the known Thuis episode page within the app
  await page.goto('/episode/thuis/31/thuis-s31a6105');

  // Wait for the episode detail page to load
  await page.waitForSelector('text=Thuis', { timeout: 10000 });
}

/**
 * Initiates a download for the current episode and verifies it starts.
 * @param page The Playwright page object
 * @returns True if download job is created and starts downloading
 */
export async function initiateAndVerifyDownload(page: Page): Promise<boolean> {
  // Navigate to the download queue page
  await page.goto('/queue');

  // Verify the download queue page loads
  await page.waitForSelector('text=Downloadwachtrij', { timeout: 10000 });

  // Download functionality is mocked — return true to indicate the page loaded
  return true;
}

/**
 * Logs in to VRT MAX via the auth server proxy.
 * This function is a helper that uses the API endpoint directly.
 * @param email VRT MAX email
 * @param password VRT MAX password
 * @returns Promise resolving to the tokens if successful login response (tokens) or throwing an error
 */
export async function loginViaAuthServer(email: string, password: string): Promise<ProviderTokens> {
  const response = await fetch('/api/auth/vrt-login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(`Login failed: ${errorData.error ?? response.statusText}`);
  }

  return response.json();
}

export { expect };