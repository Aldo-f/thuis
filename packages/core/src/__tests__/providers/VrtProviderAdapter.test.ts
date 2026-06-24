import { VrtProviderAdapter } from "../../providers/vrt/VrtProviderAdapter.ts";
import { LoginArgs, ProviderTokens, SearchResult, EpisodeDetail, StreamData } from "../../providers/types.js";

// Mock dependent services
class MockAuthService {
  login = jest.fn<Promise<ProviderTokens>, [any]>();
  getAccessToken = jest.fn<Promise<string | null>, []>();
}
class MockEpisodeService {
  getEpisode = jest.fn<Promise<EpisodeDetail>, [string]>();
}
class MockStreamResolver {
  resolveStream = jest.fn<Promise<{ targetUrls: { type: string; url: string }[] }>, [string]>();
}

// Mock SearchResultSchema to bypass validation
import { jest } from "@jest/globals";
jest.mock("../../types/index.js", () => ({
  SearchResultSchema: {
    parse: (data: any) => data,
  },
}));

describe("VrtProviderAdapter", () => {
  let adapter: VrtProviderAdapter;
  let mockAuth: MockAuthService;
  let mockEpisode: MockEpisodeService;
  let mockResolver: MockStreamResolver;

  beforeEach(async () => {
    adapter = new VrtProviderAdapter();
    // Bypass init and inject mocks
    mockAuth = new MockAuthService();
    mockEpisode = new MockEpisodeService();
    mockResolver = new MockStreamResolver();
    // @ts-ignore private fields
    (adapter as any).authService = mockAuth;
    // @ts-ignore private fields
    (adapter as any).episodeService = mockEpisode;
    // @ts-ignore private fields
    (adapter as any).streamResolver = mockResolver;
  });

  it("login() forwards credentials to auth service", async () => {
    const credentials: LoginArgs = { username: "user", password: "pass" };
    const expectedTokens: ProviderTokens = { accessToken: "t", refreshToken: "r" };
    mockAuth.login.mockResolvedValue(expectedTokens);

    const result = await adapter.login(credentials);
    expect(mockAuth.login).toHaveBeenCalledWith({ email: "user", password: "pass" });
    expect(result).toBe(expectedTokens);
  });

  it("login() propagates errors from auth service", async () => {
    const credentials: LoginArgs = { username: "u", password: "p" };
    mockAuth.login.mockRejectedValue(new Error("bad"));
    await expect(adapter.login(credentials)).rejects.toThrow("bad");
  });

  it("search() returns mapped search results", async () => {
    // Mock fetch globally
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ episodes: [{ id: "ep1", title: "Title 1" }] }),
    });
    // @ts-ignore replace global fetch
    global.fetch = mockFetch as any;

    const results = await adapter.search("test");
    expect(mockFetch).toHaveBeenCalled();
    expect(results).toEqual([{ id: "ep1", title: "Title 1" }]);
  });

  it("getEpisode() calls episode service", async () => {
    const url = "https://example.com/episode";
    const episode: EpisodeDetail = { id: "e", title: "E" };
    mockEpisode.getEpisode.mockResolvedValue(episode);

    const result = await adapter.getEpisode(url);
    expect(mockEpisode.getEpisode).toHaveBeenCalledWith(url);
    expect(result).toBe(episode);
  });

  it("resolveStream() selects HLS URL when present", async () => {
    const ep: EpisodeDetail = { id: "1", title: "" } as any;
    mockResolver.resolveStream.mockResolvedValue({
      targetUrls: [
        { type: "dash", url: "dash.mp4" },
        { type: "hls", url: "hls.m3u8" },
      ],
    });
    const result = await adapter.resolveStream(ep);
    expect(mockResolver.resolveStream).toHaveBeenCalled();
    expect(result).toEqual({
      drm: false,
      targetUrls: [
        { type: "hls", url: "hls.m3u8" },
      ],
    });
  });

  it("resolveStream() falls back to first URL when HLS missing", async () => {
    const ep: EpisodeDetail = { id: "1", title: "" } as any;
    mockResolver.resolveStream.mockResolvedValue({
      targetUrls: [{ type: "dash", url: "dash.mp4" }],
    });
    const result = await adapter.resolveStream(ep);
    expect(result).toEqual({ url: "dash.mp4" });
  });

  describe("login mode: api", () => {
    it("calls /api/auth/vrt-login with credentials", async () => {
      const apiAdapter = new VrtProviderAdapter({ loginMode: "api" });
      const mockTokens: ProviderTokens = { accessToken: "tok", refreshToken: "rtok" };
      const mockFetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(mockTokens),
      });
      (globalThis as any).fetch = mockFetch;

      const result = await apiAdapter.login({ username: "user", password: "pass" });
      expect(mockFetch).toHaveBeenCalledWith("/api/auth/vrt-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: "user", password: "pass" }),
      });
      expect(result).toEqual(mockTokens);
    });

    it("throws on API error response", async () => {
      const apiAdapter = new VrtProviderAdapter({ loginMode: "api" });
      const mockFetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: jest.fn().mockResolvedValue({ error: "bad" }),
      });
      (globalThis as any).fetch = mockFetch;

      await expect(apiAdapter.login({ username: "u", password: "p" })).rejects.toThrow("bad");
    });
  });
});
