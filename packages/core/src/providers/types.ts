export type { StreamData } from '../download/types.js';
export type { EpisodeDetail } from '../types/episode.js';

export interface LoginArgs {
  username: string;
  password: string;
}

export interface ProviderTokens {
  accessToken: string;
  refreshToken?: string;
}

export interface SearchResult {
  id: string;
  title: string;
  // Add other common properties as needed
}