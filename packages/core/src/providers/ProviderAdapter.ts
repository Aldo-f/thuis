import { LoginArgs, ProviderTokens, SearchResult, EpisodeDetail } from './types.js';
import { StreamData } from '../download/types.js';

export interface ProviderAdapter {
  readonly name: string;
  readonly id: string;
  readonly displayName: string;
  readonly supportsSearch: boolean;
  readonly supportsAuth: boolean;
  init(): Promise<void>;
  dispose(): Promise<void>;
  login(credentials: LoginArgs): Promise<ProviderTokens>;
  search(query: string): Promise<SearchResult[]>;
  getEpisode(url: string): Promise<EpisodeDetail>;
  resolveStream(episode: EpisodeDetail): Promise<StreamData>;
}