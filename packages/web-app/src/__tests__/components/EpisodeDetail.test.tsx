import React from 'react';
import { test, expect } from '@playwright/experimental-ct-react';
import EpisodeDetail from '../../pages/EpisodeDetail';
import { useEpisode } from '../../components/hooks/useEpisode';

// Mock the hook
jest.mock('../../components/hooks/useEpisode', () => ({
  useEpisode: jest.fn(),
}));

const mockEpisode = {
  title: 'Test Episode',
  description: 'Lorem ipsum',
  videoUrl: 'https://example.com/video.m3u8',
};

test.describe('EpisodeDetail component', () => {
  test.beforeEach(() => {
    // @ts-ignore
    useEpisode.mockReturnValue({ episode: mockEpisode, loading: false, error: null });
  });

  test('renders episode metadata and player', async ({ mount }) => {
    const component = await mount(<EpisodeDetail episodeId="123" />);
    await expect(component.locator('text=Test Episode')).toBeVisible();
    await expect(component.locator('video')).toBeVisible();
    // Verify that the video src is set correctly
    await expect(component.locator('video')).toHaveAttribute('src', mockEpisode.videoUrl);
  });
});
