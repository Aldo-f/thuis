import { test, expect } from '@playwright/test';
import { unlockVault, addVrtProviderCredentials, navigateToLatestThuisEpisode } from './helpers';

test.describe('Thuis Episode Discovery', () => {
  test.beforeEach(async ({ page }) => {
    // Ensure the vault is unlocked and VRT MAX credentials are added
    await page.goto('/vault');
    const masterPassword = process.env.VAULT_MASTER_PASSWORD ?? 'changeme';
    const isUnlocked = await unlockVault(page, masterPassword);
    expect(isUnlocked).toBeTruthy();

    const email = process.env.VRT_USERNAME ?? 'kuxelu@ipdeer.com';
    const password = process.env.VRT_PASSWORD ?? 'Els123456';
    const label = 'My VRT MAX Account';

    const isActive = await page.isVisible('text=VRT MAX');

    if (!isActive) {
      await addVrtProviderCredentials(page, email, password, label);
      await page.waitForSelector('text=VRT MAX', { timeout: 15000 });
    }
  });

  test('should navigate to the latest Thuis episode page', async ({ page }) => {
    await navigateToLatestThuisEpisode(page);

    // Verify that the page title or a prominent element contains "Thuis"
    await expect(page.locator('a:has-text("Thuis")').first()).toBeVisible({ timeout: 10000 });
    
    // Optionally, verify episode details like season/episode number if available
    // For this example, just checking for the main series title is sufficient.
  });
});