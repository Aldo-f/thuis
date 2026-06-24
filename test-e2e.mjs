import { chromium } from 'playwright-core';

(async () => {
  const browser = await chromium.launch({
    executablePath: '/usr/bin/chromium',
    headless: true,
    args: ['--no-sandbox', '--disable-gpu']
  });
  const context = await browser.newContext();
  // Clear state
  await context.addInitScript(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  const page = await context.newPage();
  
  try {
    await page.goto('https://thuis.aldof.duckdns.org/', { waitUntil: 'networkidle' });
    let title = await page.title();
    console.log('Page title:', title);
    if (!title.includes('Thuis')) {
      throw new Error('Unexpected title');
    }
    
    // Navigate to vault page
    await page.click('text=Inloggen');
    await page.waitForURL(/.*\/vault/);
    
    // We should be on the uninitialized vault screen (create master password)
    await page.waitForSelector('text=Welkom bij Thuis');
    
    // Fill in master password
    const masterPwd = 'Test1234!';
    await page.fill('input[placeholder="Minimaal 8 tekens"]', masterPwd);
    await page.fill('input[placeholder="Herhaal het wachtwoord"]', masterPwd);
    
    // Click the create vault button
    await page.click('text=Vault aanmaken');
    
    // Wait for the vault to unlock and show the provider management screen
    await page.waitForSelector('text=Inloggegevens');
    const lockedText = await page.locator('text=Ongerendeld').count();
    if (lockedText > 0) {
      throw new Error('Vault should be unlocked after creation');
    }
    
    // Now add a provider: click "+ Nieuwe provider toevoegen"
    await page.click('text=+ Nieuwe provider toevoegen');
    
    // Should see provider selection screen
    await page.waitForSelector('text=Kies een provider');
    
    // Click VRT MAX button
    await page.click('text=VRT MAX');
    
    // Now we should see the credential form for VRT MAX
    await page.waitForSelector('text=E-mailadres');
    await page.waitForSelector('text=Wachtwoord');
    
    // Fill in credentials (use the ones provided earlier)
    await page.fill('input[placeholder="naam@voorbeeld.com"]', 'kuxelu@ipdeer.com');
    await page.fill('input[placeholder="••••••••"]', 'Els123456');
    
    // Click Opslaan
    await page.click('text=Opslaan');
    
    // Wait for success: we should see a provider card with VRT MAX and the email masked
    await page.waitForSelector('text=VRT MAX');
    const emailLocator = await page.locator('text=kux***@ipdeer.com');
    await emailLocator.waitFor();
    
    console.log('Test passed: Vault created and provider added successfully.');
  } catch (e) {
    console.error('Test failed:', e.message);
    // Optionally take a screenshot for debugging
    await page.screenshot({ path: '/tmp/test-failure.png' });
    console.log('Screenshot saved to /tmp/test-failure.png');
  } finally {
    await browser.close();
  }
})();
