import React from 'react';
import { test, expect } from '@playwright/experimental-ct-react';
import DownloadQueuePage from '../../pages/DownloadQueuePage';

test.describe('DownloadQueuePage component', () => {
  test('shows empty state message when no downloads', async ({ mount }) => {
    const component = await mount(<DownloadQueuePage />);
    await expect(component.locator('text=Geen downloads in de wachtrij')).toBeVisible();
  });
});
