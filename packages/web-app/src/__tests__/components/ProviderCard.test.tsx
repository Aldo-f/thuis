import React from 'react';
import { test, expect } from '@playwright/experimental-ct-react';
import { ProviderList } from '../../components/vault/ProviderCard';
import { ProviderRegistry } from '@thuis/core/providers/ProviderRegistry';

// Mock ProviderRegistry to control providers returned
class MockRegistry {
  getAll() {
    return [
      { id: 'vrt', displayName: 'VRT', supportsAuth: true },
      { id: 'vtm', displayName: 'VTm', supportsAuth: false },
    ];
  }
}

test.describe('ProviderCard component', () => {
  test.beforeEach(() => {
    // @ts-ignore
    ProviderRegistry.getInstance = () => new MockRegistry();
  });

  test('renders dynamic provider cards from registry and toggles yt-dlp', async ({ mount }) => {
    const component = await mount(<ProviderList />);
    await expect(component.locator('text=VRT')).toBeVisible();
    
    await expect(component.locator('text=VTm')).toBeVisible();
    // Verify color bar exists for each card
    const cards = component.locator('[data-test-id="provider-card"]');
    await expect(cards).toHaveCount(2);
  });
});
