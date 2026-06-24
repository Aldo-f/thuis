import React from 'react';
import { test, expect } from '@playwright/experimental-ct-react';
import SeriesPage from '../../pages/SeriesPage';
import { useSeries } from '../../components/hooks/useSeries';

// Mock the series hook
jest.mock('../../components/hooks/useSeries', () => ({
  useSeries: jest.fn(),
}));

const mockSeries = [
  { id: 's1', title: 'Series One', thumbnail: '/thumb1.jpg' },
  { id: 's2', title: 'Series Two', thumbnail: '/thumb2.jpg' },
];

test.describe('SeriesPage component', () => {
  test.beforeEach(() => {
    // @ts-ignore
    useSeries.mockReturnValue({ series: mockSeries, loading: false, error: null });
  });

  test('renders series grid with titles', async ({ mount }) => {
    const component = await mount(<SeriesPage />);
    await expect(component.locator('text=Series One')).toBeVisible();
    await expect(component.locator('text=Series Two')).toBeVisible();
    // Verify grid items count matches mock data
    await expect(component.locator('[data-test-id="series-item"]').first()).toHaveCount(mockSeries.length);
  });

  test('triggers bulk download when button clicked', async ({ mount }) => {
    const bulkMock = jest.fn();
    // @ts-ignore
    useSeries.mockReturnValue({ series: mockSeries, loading: false, error: null, bulkDownload: bulkMock });
    const component = await mount(<SeriesPage />);
    const bulkBtn = component.locator('[data-test-id="bulk-download-btn"]');
    await bulkBtn.click();
    expect(bulkMock).toHaveBeenCalled();
  });
});
