---
id: api-reference
title: API Reference
sidebar_position: 6
---

# API Reference

This section lists the public TypeScript types and utilities exported by Thuis that are relevant for extension developers.

## Provider Types (`packages/core/src/providers/types.ts`)

```ts
/** Basic info about a media episode */
export interface Episode {
  id: string;
  title: string;
  season: number;
  episode: number;
  airDate: string; // ISO 8601
  thumbnail: string;
}

/** Result of a provider search */
export interface SearchResult {
  providerId: string;
  episodes: Episode[];
}

/** Credentials required to talk to a provider */
export interface ProviderCredentials {
  username?: string;
  password?: string;
  apiKey?: string;
  token?: string;
}

/** Contract that each media provider must implement */
export interface ProviderAdapter {
  init(vault: CredentialVault): Promise<void>;
  login(): Promise<void>;
  search(query: string): Promise<SearchResult[]>;
  getStreamUrl(id: string): Promise<string>;
}
```

## Vault Utilities (`packages/core/src/vault/`)

```ts
/** Initialise the vault – prompts for the master password if needed. */
init(): Promise<void>;

/** Store credentials for a provider. */
saveCredentials(providerId: string, credentials: ProviderCredentials): Promise<void>;

/** Retrieve stored credentials (or `null`). */
getCredentials(providerId: string): Promise<ProviderCredentials | null>;

/** Remove credentials for a provider. */
removeCredentials(providerId: string): Promise<void>;

/** Change the master password – re‑encrypts everything. */
changeMasterPassword(oldPwd: string, newPwd: string): Promise<void>;
```

## Search Service (`packages/core/src/services/SearchService.ts`)

```ts
/** Initialise the service with a list of adapters. */
init(adapters: ProviderAdapter[]): Promise<void>;

/** Search across all enabled providers. */
searchAll(query: string): Promise<AggregatedSearchResult>;

/** Search a specific provider. */
searchProvider(providerId: string, query: string): Promise<SearchResult[]>;
```

---

For a full list of exported symbols, see the generated TypeDoc output in the `website/build` folder after running `pnpm run docs:build`.
