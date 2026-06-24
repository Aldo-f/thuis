import { ProviderAdapter } from '../ProviderAdapter.js';
import { LoginArgs, ProviderTokens, SearchResult, EpisodeDetail } from '../types.js';
import { StreamData } from '../../download/types.js';

export class ProviderNotSupportedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ProviderNotSupportedError';
  }
}

export class PlaytvProviderAdapter implements ProviderAdapter {
  readonly name = 'playtv';
  readonly id = 'playtv';
  readonly displayName = 'Play.TV';
  readonly supportsSearch = false;
  readonly supportsAuth = false;

  async init(): Promise<void> {
    // No-op: provider is not yet supported.
  }

  async dispose(): Promise<void> {
    // No-op: provider is not yet supported.
  }

  async login(_credentials: LoginArgs): Promise<ProviderTokens> {
    throw new ProviderNotSupportedError('Play.TV wordt nog niet ondersteund');
  }

  async search(_query: string): Promise<SearchResult[]> {
    throw new ProviderNotSupportedError('Play.TV wordt nog niet ondersteund');
  }

  async getEpisode(_url: string): Promise<EpisodeDetail> {
    throw new ProviderNotSupportedError('Play.TV wordt nog niet ondersteund');
  }

  async resolveStream(_episode: EpisodeDetail): Promise<StreamData> {
    throw new ProviderNotSupportedError('Play.TV wordt nog niet ondersteund');
  }
}