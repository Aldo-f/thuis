import { ProviderAdapter } from '../ProviderAdapter.js';
import { VrtAuthService } from '../../auth/VrtAuthService.js';
import { VrtEpisodeService } from '../../episode/VrtEpisodeService.js';
import { StreamResolver } from '../../download/StreamResolver.js';
import { LoginArgs, ProviderTokens, SearchResult, EpisodeDetail, StreamData } from '../types.js';
import { SEARCH_EPISODES_QUERY } from '../../graphql/queries.js';
import { SearchResultSchema, Episode } from '../../types/index.js';
import { z } from 'zod';

export interface VrtProviderAdapterOptions {
  loginMode?: 'direct' | 'api';
  apiUrl?: string;
}

export class VrtProviderAdapter implements ProviderAdapter {
  readonly name = 'vrt';
  readonly id = 'vrt';
  readonly displayName = 'VRT MAX';
  readonly supportsSearch = true;
  readonly supportsAuth = true;

  private authService!: VrtAuthService;
  private episodeService!: VrtEpisodeService;
  private streamResolver!: StreamResolver;
  private loginMode: 'direct' | 'api';
  private apiUrl: string;

  constructor(options?: VrtProviderAdapterOptions) {
    this.loginMode = options?.loginMode ?? 'direct';
    this.apiUrl = options?.apiUrl ?? '/api/auth/vrt-login';
  }

  async init(): Promise<void> {
    this.authService = new VrtAuthService();
    this.episodeService = new VrtEpisodeService(this.authService);
    this.streamResolver = new StreamResolver(this.authService);
    // Services do not have an init method; nothing to do.
  }

  async dispose(): Promise<void> {
    // Services do not have a dispose method; nothing to do.
  }

  async login(credentials: LoginArgs): Promise<ProviderTokens> {
    if (this.loginMode === 'api') {
      const response = await globalThis.fetch(this.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: credentials.username, password: credentials.password }),
      });
      if (!response.ok) {
        const body = (await response.json()) as { error?: string };
        throw new Error(body.error ?? 'Login request failed');
      }
      return response.json() as Promise<ProviderTokens>;
    }
    const authCredentials: { email: string; password: string } = {
      email: credentials.username,
      password: credentials.password,
    };
    return this.authService.login(authCredentials);
  }

  async search(query: string): Promise<SearchResult[]> {
    const baseUrl = 'https://www.vrt.be/vrtnu-api/graphql/v1';
    const token = await this.authService.getAccessToken().catch(() => null);
    const variables = {
      componentId: btoa(JSON.stringify({ q: query })),
      lazyItemCount: 10,
    };

    const response = await fetch(baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        query: SEARCH_EPISODES_QUERY,
        variables,
      }),
    });

    if (!response.ok) {
      throw new Error(`Search request failed with status ${response.status}`);
    }

    const json = await response.json();

    if (json.errors && json.errors.length) {
      throw new Error(`GraphQL errors: ${json.errors.map((e: { message: string }) => e.message).join(', ')}`);
    }

    if (!json.data) {
      throw new Error('No data returned from GraphQL API');
    }

    // Validate against Zod schema
    const parsed = SearchResultSchema.parse(json.data);
    // Map to the SearchResult[] expected by ProviderAdapter
    return parsed.episodes.map((episode: Episode) => ({
      id: episode.id,
      title: episode.title,
    }));
  }

  async getEpisode(url: string): Promise<EpisodeDetail> {
    return this.episodeService.getEpisode(url);
  }

  async resolveStream(episode: EpisodeDetail): Promise<StreamData> {
    // Delegates to StreamResolver and returns the full StreamData object.
    // The caller can inspect drm, targetUrls, etc.
    return this.streamResolver.resolveStream(episode.videoId);
  }
}
