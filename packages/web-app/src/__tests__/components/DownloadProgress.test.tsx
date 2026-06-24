import React from 'react';
import { test, expect } from '@playwright/experimental-ct-react';
import DownloadProgress from '../../components/DownloadProgress';
import { useDownload } from '../../components/hooks/useDownload';

// Mock the download hook
jest.mock('../../components/hooks/useDownload', () => ({
  useDownload: jest.fn(),
}));

const mockState = {
  progress: 45,
  total: 100,
  status: 'downloading',
};

test.describe('DownloadProgress component', () => {
  test.beforeEach(() => {
    // @ts-ignore
    useDownload.mockReturnValue({ download: mockState, loading: false, error: null });
  });

  test('renders progress bar with correct percentage', async ({ mount }) => {
    const component = await mount(<DownloadProgress />);
    await expect(component.locator('[data-test-id="progress-percentage"]').first()).toHaveText('45%');
    // Verify bar width style reflects progress (implementation‑specific attribute)
    await expect(component.locator('[data-test-id="progress-bar"]').first()).toHaveAttribute('style', /width:\s*45%/i);
  });

  test('shows completed state when progress reaches 100', async ({ mount }) => {
    // @ts-ignore
    useDownload.mockReturnValue({ download: { ...mockState, progress: 100, status: 'completed' }, loading: false, error: null });
    const component = await mount(<DownloadProgress />);
    await expect(component.locator('text=Completed')).toBeVisible();
  });
});
