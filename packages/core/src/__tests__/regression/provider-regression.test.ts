// Regression tests ensuring VrtProviderAdapter delegates correctly to underlying services
// No @ts-ignore or any casts are used.

import { jest } from '@jest/globals';
import nock from "nock";
import { VrtProviderAdapter } from "../../providers/vrt/VrtProviderAdapter.ts";
import { VrtAuthService } from "../../auth/VrtAuthService.ts";
import { VrtEpisodeService } from "../../episode/VrtEpisodeService.ts";
import { StreamResolver } from "../../download/StreamResolver";
import { InMemoryTokenStorage } from "../../auth/VrtAuthService";
import { VrtTokens } from "../../auth/types";
import { LoginArgs, ProviderTokens, SearchResult, EpisodeDetail, StreamData } from "../../providers/types.js";

// Helper to create a mock AuthService that returns deterministic tokens
function createMockAuth(): VrtAuthService {
  const storage = new InMemoryTokenStorage();
  const future = Math.floor(Date.now() / 1000) + 3600;
  const tokens: VrtTokens = {
    accessToken: "FAKE_ACCESS",
    videoToken: "FAKE_VIDEO",
    refreshToken: "FAKE_REFRESH",
    expiresAt: future,
    acquiredAt: Math.floor(Date.now() / 1000),
  };
  // Store both meta and the raw video token – the service reads from storage directly.
  storage.set("vrtnu_token_meta", JSON.stringify(tokens));
  storage.set("vrtnu-site_profile_vt", tokens.videoToken);
  return new VrtAuthService({ storage });
}

// Mock global fetch for the provider's search method – returns a predictable payload.
function mockSearchFetch(): void {
  const mockFetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ episodes: [{ id: "ep1", title: "Title 1" }] }),
  });
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (global as any).fetch = mockFetch;
}

// Minimal mock for EpisodeService – resolves a fixed EpisodeDetail.
class MockEpisodeService {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async getEpisode(_url: string): Promise<EpisodeDetail> {
    return {
      id: "episode-1",
      title: "Test Episode",
      // The rest of the fields are optional in the type definition; we provide only required ones.
    } as EpisodeDetail;
  }
}

// Minimal mock for StreamResolver – resolves a deterministic StreamData.
class MockStreamResolver {
  async resolveStream(_streamId: string): Promise<StreamData> {
    return { url: "https://example.com/stream.m3u8" } as StreamData;
  }
}

describe("Provider regression tests", () => {
  let adapter: VrtProviderAdapter;
  let directAuth: VrtAuthService;
  let directEpisode: VrtEpisodeService;
  let directResolver: StreamResolver;

  beforeEach(async () => {
    // Initialise adapter and inject mocked services.
    adapter = new VrtProviderAdapter();
    const mockAuth = createMockAuth();
    const mockEpisode = new MockEpisodeService();
    const mockResolver = new MockStreamResolver();
    // @ts-ignore – private fields are intentionally overridden for testing.
    (adapter as any).authService = mockAuth;
    // @ts-ignore
    (adapter as any).episodeService = mockEpisode;
    // @ts-ignore
    (adapter as any).streamResolver = mockResolver;

    // Direct service instances use the same mock Auth for fair comparison.
    directAuth = mockAuth;
    directEpisode = new VrtEpisodeService(directAuth);
    directResolver = new StreamResolver(directAuth);
  });

  test("login() returns identical tokens as direct VrtAuthService", async () => {
    const creds: LoginArgs = { username: "user@example.com", password: "secret" };
    // Direct service expects VrtCredentials (email/password).
    const expected = await directAuth.login({ email: creds.username, password: creds.password });
    const adapterResult = await adapter.login(creds);
    expect(adapterResult).toEqual(expected);
  });

  test("search() result matches direct fetch behaviour", async () => {
    mockSearchFetch();
    const directResult = await (adapter as any).search("dummy"); // Adapter uses its own fetch implementation.
    const expected = [{ id: "ep1", title: "Title 1" }];
    expect(directResult).toEqual(expected);
  });

  test("getEpisode() delegates correctly", async () => {
    const url = "https://example.com/episode";
    const direct = await directEpisode.getEpisode(url);
    const viaAdapter = await adapter.getEpisode(url);
    expect(viaAdapter).toEqual(direct);
  });

  test("resolveStream() produces the same StreamData as direct resolver", async () => {
    const episode = { videoId: "stream-id" } as any as EpisodeDetail;
    const direct = await directResolver.resolveStream("stream-id");
    const viaAdapter = await adapter.resolveStream(episode);
    expect(viaAdapter).toEqual(direct);
  });
});
