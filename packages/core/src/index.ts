// @thuis/core — Shared business logic, API clients, and state management

export * from "./types/index.js";
export * from "./vault/Vault.js";

// Auth
export {
  VrtAuthService,
  VrtError,
  AuthenticationError,
  InvalidCredentialsError,
  TokenAcquisitionError,
  TokenExpiredError,
  InMemoryTokenStorage,
} from "./auth/VrtAuthService.js";
export type { VrtAuthServiceOptions } from "./auth/VrtAuthService.js";

export {
  VrtCredentialsSchema,
  VrtTokensSchema,
  VrtLoginResponseSchema,
  VrtPlayerTokenResponseSchema,
  TOKEN_KEYS,
} from "./auth/types.js";
export type {
  VrtCredentials,
  VrtTokens,
  VrtLoginResponse,
  VrtPlayerTokenResponse,
  TokenStorage,
} from "./auth/types.js";

// Episode
export {
  VrtEpisodeService,
  EpisodeUnavailableError,
} from "./episode/VrtEpisodeService.js";

// GraphQL
export { VIDEO_PAGE_QUERY, SEARCH_EPISODES_QUERY, EPISODE_BY_URL_QUERY } from "./graphql/queries.js";
export {
  VideoPageSchema,
  VideoPageEpisodeSchema,
  VideoPagePlayerSchema,
  extractStreamId,
} from "./graphql/types.js";
export type { VideoPageResponse } from "./graphql/types.js";
export { createClient } from "./graphql/client.js";
export type { GraphQLClient } from "./graphql/client.js";

// Download
export {
  StreamResolver,
} from "./download/StreamResolver.js";
export {
  StreamDataSchema,
  TargetUrlSchema,
  SubtitleUrlSchema,
  STREAM_ERROR_CODES,
  StreamError,
  DrmError,
  GeoBlockedError,
} from "./download/types.js";
export type {
  StreamData,
  TargetUrl,
  SubtitleUrl,
} from "./download/types.js";

export { parseVrtUrl, VrtUrlError } from "./url-resolver.js";
export type { VrtUrlComponents } from "./url-resolver.js";

export { ProviderRegistry } from "./providers/ProviderRegistry.js";
export type { ProviderAdapter } from "./providers/ProviderAdapter.js";
export { initializeProviders } from "./provider-setup.js";
