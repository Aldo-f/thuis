---
id: provider-adapter
title: Provider Adapter
sidebar_position: 3
---

# Provider Adapter

The **ProviderAdapter** interface defines how Thuis communicates with a media provider (e.g., VRT MAX, VTM GO, Play.TV). A concrete adapter implements the methods required to authenticate, search for episodes, and retrieve streaming URLs.

## Interface

```ts
export interface ProviderAdapter {
  /**
   * Initialise the adapter with the shared credential vault.
   */
  init(vault: CredentialVault): Promise<void>;

  /**
   * Perform any provider‑specific login. May prompt the user for credentials that are then stored in the vault.
   */
  login(): Promise<void>;

  /**
   * Search the provider catalog.
   * @param query Free‑text query (title, season, etc.)
   * @returns A list of {@link SearchResult} objects.
   */
  search(query: string): Promise<SearchResult[]>;

  /**
   * Resolve a single episode into a playable HLS URL.
   * @param id Provider‑specific episode identifier.
   */
  getStreamUrl(id: string): Promise<string>;
}
```

## Implementing a New Provider

1. **Create a class** that implements `ProviderAdapter`.
2. **Inject the vault** in the `init` method to read/write credentials.
3. **Implement `login`** – call the provider’s authentication endpoint and store the resulting token using `vault.save()`.
4. **Implement `search`** – map the provider’s search response to the generic `SearchResult` shape.
5. **Implement `getStreamUrl`** – transform the provider‑specific playback URL into a plain HLS URL that the player can consume.
6. **Register the adapter** in `packages/core/src/providers/index.ts` so the `SearchService` can discover it.

## Example Skeleton

```ts
import { ProviderAdapter, SearchResult } from "../types";
import { CredentialVault } from "../../vault/CredentialVault";

export class VrtMaxAdapter implements ProviderAdapter {
  private vault!: CredentialVault;

  async init(vault: CredentialVault) {
    this.vault = vault;
  }

  async login() {
    const creds = await this.vault.getCredentials("vrt-max");
    // Perform login request …
    // await this.vault.saveToken("vrt-max", token);
  }

  async search(query: string): Promise<SearchResult[]> {
    // Call VRT MAX search API and map results
    return [];
  }

  async getStreamUrl(id: string): Promise<string> {
    // Resolve playback URL
    return "https://.../playlist.m3u8";
  }
}
```

Refer to the existing `VrtMaxAdapter` in `packages/core/src/providers/vrtMax.ts` for a real implementation.

## When to Extend

Add a new adapter whenever a fresh service is added to the platform. The rest of the application (search UI, download manager) does not need to change because they work against the generic `ProviderAdapter` contract.
