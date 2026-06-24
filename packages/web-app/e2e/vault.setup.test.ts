import { test, expect } from '@playwright/test';
import { unlockVault, lockVault } from './helpers';

test.describe('Vault initialization and setup', () => {
  test('should initialize vault if not already initialized', async ({ page }) => {
    // Go to the vault page
    await page.goto('/vault');

    // Check if we are on the initialization screen
    const initializeScreen = await page.isVisible('text=Welkom bij Thuis');
    if (initializeScreen) {
      // Fill in master password and confirmation
      const masterPassword = process.env.VAULT_MASTER_PASSWORD ?? 'changeme';
      await page.fill('input[placeholder="Minimaal 8 tekens"]', masterPassword);
      await page.fill('input[placeholder="Herhaal het wachtwoord"]', masterPassword);
      await page.click('button:has-text("Vault aanmaken")');

      // Wait for the vault to be unlocked (e.g., provider list visible)
      await page.waitForSelector('text=Inloggegevens', { timeout: 10000 });
    } else {
      // If already initialized, we just need to unlock
      const masterPassword = process.env.VAULT_MASTER_PASSWORD ?? 'changeme';
      const isUnlocked = await unlockVault(page, masterPassword);
      expect(isUnlocked).toBeTruthy();
    }
  });

  test('should unlock vault with correct master password', async ({ page }) => {
    // Go to the vault page
    await page.goto('/vault');

    // Unlock the vault
    const masterPassword = process.env.VAULT_MASTER_PASSWORD ?? 'changeme';
    const isUnlocked = await unlockVault(page, masterPassword);
    expect(isUnlocked).toBeTruthy();
  });

test('should not unlock vault with incorrect master password', async ({ page }) => {
    await page.goto('/vault');
    const masterPassword = process.env.VAULT_MASTER_PASSWORD ?? 'changeme';
    // Ensure we are unlocked (if not, initialize and unlock)
    await unlockVault(page, masterPassword);
    // Now lock the vault
    await page.click('button:has-text("Vergrendelen")');
    await page.waitForSelector('text=Vault ontgrendelen', { timeout: 5000 });

    // Now try to unlock with wrong password
    await page.fill('input[placeholder="Hoofdwachtwoord"]', 'wrongpassword');
    await page.click('button:has-text("Ontgrendelen")');
    await page.waitForSelector('div.bg-red-50', { timeout: 5000 });
  });
});