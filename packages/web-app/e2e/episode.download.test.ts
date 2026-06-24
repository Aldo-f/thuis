import { test, expect } from '@playwright/test';
import { unlockVault, addVrtProviderCredentials, navigateToLatestThuisEpisode, initiateAndVerifyDownload } from './helpers';

test.describe('Thuis Episode Download Initiation', () => {
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

    // Navigate to the latest Thuis episode
    await navigateToLatestThuisEpisode(page);
  });

  test('should initiate and verify download for Thuis episode', async ({ page }) => {
    const downloadStarted = await initiateAndVerifyDownload(page);
    expect(downloadStarted).toBeTruthy();
  });
});