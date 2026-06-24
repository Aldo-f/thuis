import { test, expect } from '@playwright/test';
import { addVrtProviderCredentials, unlockVault } from './helpers';

test.describe('VRT MAX SSO Login via Auth Server', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the auth server endpoint
    await page.route('**/api/auth/vrt-login', async (route) => {
      const request = route.request();
      if (request.method() === 'POST') {
        const body = JSON.parse(route.request().postData() || '{}');
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
    // Ensure the vault is unlocked before each test
    await page.goto('/vault');
    const masterPassword = process.env.VAULT_MASTER_PASSWORD ?? 'changeme';
    const isUnlocked = await unlockVault(page, masterPassword);
    expect(isUnlocked).toBeTruthy();
  });

  test('should successfully log in to VRT MAX via auth server and store tokens', async ({ page }) => {
    // Add VRT MAX credentials, which triggers login via the auth server
    const email = process.env.VRT_USERNAME ?? 'kuxelu@ipdeer.com';
    const password = process.env.VRT_PASSWORD ?? 'Els123456';
    const label = 'My VRT MAX Account';

    await addVrtProviderCredentials(page, email, password, label);

    // Verify that the VRT MAX provider card shows as configured badge, indicating successful login and token storage
    await page.waitForSelector('text=Geconfigureerd', { timeout: 10000 });
  });

  test('should handle failed login attempts gracefully', async ({ page }) => {
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

    // Wait for error message from the UI (which originates from the auth server)
    await page.waitForSelector('text=Onbekende fout bij inloggen', { timeout: 10000 });
    expect(await page.isVisible('text=Onbekende fout bij inloggen')).toBeTruthy();
  });
});