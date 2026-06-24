import { ProviderAdapter } from '../ProviderAdapter.js';
import { LoginArgs, ProviderTokens, SearchResult, EpisodeDetail } from '../types.js';
import { StreamData } from '../../download/types.js';

export class ProviderNotSupportedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ProviderNotSupportedError';
  }
}

export class VtmgoProviderAdapter implements ProviderAdapter {
  readonly name = 'vtmgo';
  readonly id = 'vtmgo';
  readonly displayName = 'VTM GO';
  readonly supportsSearch = false;
  readonly supportsAuth = false;

  async init(): Promise<void> {
    // No-op: provider is not yet supported.
  }

  async dispose(): Promise<void> {
    // No-op: provider is not yet supported.
  }

  async login(_credentials: LoginArgs): Promise<ProviderTokens> {
    throw new ProviderNotSupportedError('VTM GO wordt nog niet ondersteund');
  }

  async search(_query: string): Promise<SearchResult[]> {
    throw new ProviderNotSupportedError('VTM GO wordt nog niet ondersteund');
  }

  async getEpisode(_url: string): Promise<EpisodeDetail> {
    throw new ProviderNotSupportedError('VTM GO wordt nog niet ondersteund');
  }

  async resolveStream(_episode: EpisodeDetail): Promise<StreamData> {
    throw new ProviderNotSupportedError('VTM GO wordt nog niet ondersteund');
  }
}
