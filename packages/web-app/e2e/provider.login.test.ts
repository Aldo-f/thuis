import { test, expect } from '@playwright/test';
import { unlockVault } from './helpers';

test.describe('VRT MAX provider credential addition', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the auth server endpoint
    await page.route('**/api/auth/vrt-login', async (route) => {
      const request = route.request();
      if (request.method() === 'POST') {
        const body = JSON.parse(request.postData() || '{}');
        if (body.email === 'invalid@example.com') {
          await route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Onbekende fout bij inloggen' }),
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              accessToken: 'mock-access-token',
              refreshToken: 'mock-refresh-token',
              expiresAt: Date.now() + 3600000,
            }),
          });
        }
      } else {
        await route.continue();
      }
    });
    // Ensure we are on the vault page and unlocked
    await page.goto('/vault');
    const masterPassword = process.env.VAULT_MASTER_PASSWORD ?? 'changeme';
    const isUnlocked = await unlockVault(page, masterPassword);
    expect(isUnlocked).toBeTruthy();
  });

  test('should add VRT MAX credentials and trigger login via auth server', async ({ page }) => {
    // Click on "Add provider" button
    await page.click('button:has-text("Nieuwe provider toevoegen")');

    // Select VRT MAX provider (assuming it's listed)
    await page.click('text=VRT MAX');

    // Fill in the credentials
    const email = process.env.VRT_USERNAME ?? 'kuxelu@ipdeer.com';
    const password = process.env.VRT_PASSWORD ?? 'Els123456';
    const label = 'My VRT MAX Account';

    await page.fill('input[placeholder="naam@voorbeeld.com"]', email);
    await page.fill('input[placeholder="••••••••"]', password);
    await page.fill('input[placeholder="Bijv. Mijn VRT-account"]', label);

    // Check the verification box (optional)
    await page.locator('label').filter({ hasText: 'Verifieer nu' }).locator('input').check();

    // Submit the submit button
    await page.click('button:has-text("Opslaan")');

    // Wait for the provider card to appear
    await page.waitForSelector('text=VRT MAX', { timeout: 15000 });

// Wait for the provider card to show as configured badge
    await page.waitForSelector('text=Geconfigureerd', { timeout: 10000 });
  });

  test('should show error message for invalid credentials', async ({ page }) => {
    // Click on "Add provider" button
    await page.click('button:has-text("Nieuwe provider toevoegen")');

    // Select VRT MAX provider
    await page.click('text=VRT MAX');

    // Fill in invalid credentials
    const email = 'invalid@example.com';
    const password = 'wrongpassword';
    const label = 'Invalid Account';

    await page.fill('input[placeholder="naam@voorbeeld.com"]', email);
    await page.fill('input[placeholder="••••••••"]', password);
    await page.fill('input[placeholder="Bijv. Mijn VRT-account"]', label);

    // Submit the form
    await page.click('button:has-text("Opslaan")');

    // Wait for error message
    await page.waitForSelector('text=Onbekende fout bij inloggen', { timeout: 10000 });
  });
});