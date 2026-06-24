import { ProviderRegistry } from "../../providers/ProviderRegistry.ts";
import { ProviderAdapter } from "../../providers/ProviderAdapter.ts";
import { LoginArgs, ProviderTokens, SearchResult, EpisodeDetail, StreamData } from "../../providers/types.ts";

// Mock provider for testing
class DummyProvider implements ProviderAdapter {
  readonly name = "dummy";
  readonly id = "dummy-id";
  readonly displayName = "Dummy";
  readonly supportsSearch = false;
  readonly supportsAuth = false;
  async init(): Promise<void> {
    // dummy implementation
  }
  async dispose(): Promise<void> {
    // dummy implementation
  }
  async login(credentials: LoginArgs): Promise<ProviderTokens> {
    return { accessToken: "token", refreshToken: "refresh" } as ProviderTokens;
  }
  async search(query: string): Promise<SearchResult[]> {
    return [] as SearchResult[];
  }
  async getEpisode(url: string): Promise<EpisodeDetail> {
    return { id: "episode-id", title: "Episode" } as EpisodeDetail;
  }
  async resolveStream(episode: EpisodeDetail): Promise<StreamData> {
    return { url: "https://example.com/stream" } as StreamData;
  }
}

describe("ProviderRegistry", () => {
  it("should register, retrieve, list, and dispose providers", async () => {
    const registry = ProviderRegistry.getInstance();
    const provider = new DummyProvider();
    await registry.register(provider);
    expect(registry.get("dummy")).toBe(provider);
    expect(registry.getAll()).toContain(provider);
    await registry.dispose();
    expect(registry.getAll()).toHaveLength(0);
  });
});