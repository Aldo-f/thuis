const { test, expect } = require('@playwright/test');

test('Vault creation and provider addition', async ({ page }) => {
  // Clear localStorage to start fresh
  await page.context().clearCookies();
  await page.addInitScript(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.goto('https://thuis.aldof.duckdns.org/');
  await expect(page).toHaveTitle(/Thuis/);
  
  // Click on the "Inloggen" link to go to vault page
  await page.click('text=Inloggen');
  await expect(page).toHaveURL(/.*\/vault/);
  
  // We should be on the uninitialized vault screen (create master password)
  await expect(page.locator('text=Welkom bij Thuis')).toBeVisible();
  
  // Fill in master password
  const masterPwd = 'Test1234!';
  await page.fill('input[placeholder="Minimaal 8 tekens"]', masterPwd);
  await page.fill('input[placeholder="Herhaal het wachtwoord"]', masterPwd);
  
  // Click the create vault button
  await page.click('text=Vault aanmaken');
  
  // Wait for the vault to unlock and show the provider management screen
  await expect(page.locator('text=Inloggegevens')).toBeVisible();
  await expect(page.locator('text=Ongerendeld')).not.toBeVisible(); // locked -> unlocked
  
  // Now add a provider: click "+ Nieuwe provider toevoegen"
  await page.click('text=+ Nieuwe provider toevoegen');
  
  // Should see provider selection screen
  await expect(page.locator('text=Kies een provider')).toBeVisible();
  
  // Click VRT MAX button
  await page.click('text=VRT MAX');
  
  // Now we should see the credential form for VRT MAX
  await expect(page.locator('text=E-mailadres')).toBeVisible();
  await expect(page.locator('text=Wachtwoord')).toBeVisible();
  
  // Fill in credentials (use the ones provided earlier)
  await page.fill('input[placeholder="naam@voorbeeld.com"]', 'kuxelu@ipdeer.com');
  await page.fill('input[placeholder="••••••••"]', 'Els123456');
  
  // Click Opslaan
  await page.click('text=Opslaan');
  
  // Wait for success: we should see a provider card with VRT MAX and the email masked
  await expect(page.locator('text=VRT MAX')).toBeVisible();
  await expect(page.locator('text=kuxelu@ipdeer.com')).toBeVisible(); // Actually masked, but we can check for masked pattern
  // The mask shows first 3 chars then ***: kux***@ipdeer.com
  await expect(page.locator('text=kux***@ipdeer.com')).toBeVisible();
  
  console.log('Test passed: Vault created and provider added successfully.');
});

test.run();
