import { ProviderRegistry } from "@thuis/core";
import type { ProviderAdapter, SearchResult } from "@thuis/core";

export class SearchService {
    async search(query: string): Promise<(SearchResult & { provider: string })[]> {
    // Get all registered adapters
    const adapters = ProviderRegistry.getInstance().getAll() as ProviderAdapter[];

    // Filter those that announce search support. The concrete ProviderAdapter
    // type defines the boolean `supportsSearch` and a `search` method returning
    // `Promise<SearchResult[]>`.
    const searchable = adapters.filter((adapter) => (adapter as ProviderAdapter).supportsSearch);

    // Execute all searches in parallel whilst capturing failures.
    const promises = searchable.map((adapter) =>
      adapter.search(query).then(
        (results: SearchResult[]) => ({ status: "fulfilled" as const, results, provider: adapter.id }),
        (error: unknown) => ({ status: "rejected" as const, error, provider: adapter.id })
      )
    );

    const settled = await Promise.all(promises);

    // Merge successful results, discarding rejected ones.
    const aggregated: (SearchResult & { provider: string })[] = [];
    for (const entry of settled) {
      if (entry.status === "fulfilled") {
        for (const r of entry.results) {
          aggregated.push({ ...r, provider: entry.provider });
        }
      }
      // Errors are silently ignored – a real implementation could log them.
    }

    return aggregated;
  }
}
