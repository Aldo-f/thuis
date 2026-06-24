---
id: search-service
title: Search Service
sidebar_position: 5
---

# Search Service

The **SearchService** is the central orchestrator that aggregates search results from all registered `ProviderAdapter`s. It provides a uniform API to the UI layer, handling provider selection, error aggregation, and result normalisation.

## Core API

```ts
/**
 * Initialise the service with a list of adapters.
 */
init(adapters: ProviderAdapter[]): Promise<void>;

/**
 * Perform a search across every enabled provider.
 * @param query Free‑text query entered by the user.
 * @returns An array of {@link SearchResult} objects, merged from all providers.
 */
searchAll(query: string): Promise<SearchResult[]>;

/**
 * Search a specific provider.
 * @param providerId Identifier of the provider (e.g. "vrt-max").
 * @param query Search term.
 */
searchProvider(providerId: string, query: string): Promise<SearchResult[]>;
```

## How It Works

1. **Adapter registration** – each concrete `ProviderAdapter` calls `SearchService.register(adapter)` during its module initialisation. The service stores the adapter instance in an internal map keyed by the provider ID.
2. **Parallel execution** – `searchAll` fires `adapter.search(query)` for every registered adapter concurrently using `Promise.allSettled`.
3. **Result normalisation** – each adapter returns its own `SearchResult` type. The service maps these into the shared `SearchResult` interface defined in `packages/core/src/providers/types.ts`.
4. **Error handling** – if an individual provider fails, its error is captured and attached to the final result set under a `providerErrors` field. The UI can display per‑provider warnings without breaking the entire search.

```ts
interface AggregatedSearchResult {
  results: SearchResult[];
  providerErrors: Record<string, string>; // providerId → error message
}
```

## Example Usage (React Hook)

```tsx
import { useEffect, useState } from "react";
import { SearchService } from "@/core/services/SearchService";

export function useSearch(query: string) {
  const [data, setData] = useState<AggregatedSearchResult>({
    results: [],
    providerErrors: {},
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!query) return;
    setLoading(true);
    SearchService.searchAll(query)
      .then(res => setData(res))
      .finally(() => setLoading(false));
  }, [query]);

  return { data, loading };
}
```

## Error Handling Strategy

- **Network failures** – captured and stored in `providerErrors`. The UI can show a non‑intrusive toast.
- **Authentication errors** – if a provider reports missing or expired credentials, the service triggers a `vault.lock()` and surfaces a *“login required”* message for that provider.
- **Partial successes** – `searchAll` returns the successful results along with any errors, never aborting the whole operation.

## When to Extend

Add new behaviour when a provider introduces a fundamentally different result shape (e.g., live‑stream calendars). Create a transformation function in the adapter so the service continues to return the canonical `SearchResult`.

---

*For a deeper dive, see the implementation in `packages/core/src/services/SearchService.ts`.*
