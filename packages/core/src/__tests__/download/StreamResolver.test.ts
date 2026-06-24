import nock from "nock";
import { StreamResolver } from "../../download/StreamResolver.ts";
import { InMemoryTokenStorage } from "../../auth/VrtAuthService.ts";
import { VrtAuthService } from "../../auth/VrtAuthService.ts";
import { VrtTokens } from "../../auth/types";

const FAKE_VIDEO_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjAifQ.eyJleHAiOjk5OTk5OTk5OTksImlhdCI6MTcwMDAwMDAwMH0.def";
const FAKE_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjAifQ.eyJleHAiOjk5OTk5OTk5OTksImlhdCI6MTcwMDAwMDAwMH0.abc";

function createMockAuth(): VrtAuthService {
  const storage = new InMemoryTokenStorage();
  const future = Math.floor(Date.now() / 1000) + 3600;
  const tokens: VrtTokens = {
    accessToken: FAKE_ACCESS_TOKEN,
    videoToken: FAKE_VIDEO_TOKEN,
    refreshToken: "refresh",
    expiresAt: future,
    acquiredAt: Math.floor(Date.now() / 1000),
  };
  storage.set("vrtnu_token_meta", JSON.stringify(tokens));
  storage.set("vrtnu-site_profile_vt", FAKE_VIDEO_TOKEN);
  return new VrtAuthService({ storage });
}

describe("StreamResolver", () => {
  afterEach(() => {
    nock.cleanAll();
  });

  const STREAM_ID = "pbs-pub-abc123$vid-def456";

  describe("resolveStream()", () => {
    it("gets vrtPlayerToken and fetches HLS stream data", async () => {
      // Step 1: POST /v2/tokens → player token
      nock("https://media-services-public.vrt.be")
        .post("/vualto-video-aggregator-web/rest/external/v2/tokens")
        .reply(200, { vrtPlayerToken: "b1@test-player-token" });

      // Step 2: GET /v2/videos/{streamId} → stream data
      nock("https://media-services-public.vrt.be")
        .get("/vualto-video-aggregator-web/rest/external/v2/videos/pbs-pub-abc123%24vid-def456")
        .query({ client: "vrtnu-web@PROD", vrtPlayerToken: "b1@test-player-token" })
        .reply(200, {
          title: "Aflevering 105",
          duration: 1800000,
          drm: false,
          targetUrls: [
            { type: "hls", url: "https://stream.vrt.be/master.m3u8" },
          ],
        });

      const auth = createMockAuth();
      const resolver = new StreamResolver(auth);
      const stream = await resolver.resolveStream(STREAM_ID);

      expect(stream.drm).toBe(false);
      expect(stream.targetUrls).toHaveLength(1);
      expect(stream.targetUrls[0]!.type).toBe("hls");
      expect(stream.targetUrls[0]!.url).toBe("https://stream.vrt.be/master.m3u8");
      expect(stream.title).toBe("Aflevering 105");
    });

    it("throws DrmError when stream is DRM-protected", async () => {
      nock("https://media-services-public.vrt.be")
        .post("/vualto-video-aggregator-web/rest/external/v2/tokens")
        .reply(200, { vrtPlayerToken: "b1@test" });

      nock("https://media-services-public.vrt.be")
        .get(/\/vualto-video-aggregator-web\/rest\/external\/v2\/videos\//)
        .query(true)
        .reply(200, {
          drm: true,
          targetUrls: [],
        });

      const auth = createMockAuth();
      const resolver = new StreamResolver(auth);

      await expect(resolver.resolveStream(STREAM_ID)).rejects.toThrow(
        /beveiligd/i,
      );
    });

    it("throws GeoBlockedError when geo-restricted", async () => {
      nock("https://media-services-public.vrt.be")
        .post("/vualto-video-aggregator-web/rest/external/v2/tokens")
        .reply(200, { vrtPlayerToken: "b1@test" });

      nock("https://media-services-public.vrt.be")
        .get(/\/vualto-video-aggregator-web\/rest\/external\/v2\/videos\//)
        .query(true)
        .reply(200, {
          code: "CONTENT_AVAILABLE_ONLY_FOR_BE_RESIDENTS",
          targetUrls: [],
        });

      const auth = createMockAuth();
      const resolver = new StreamResolver(auth);

      await expect(resolver.resolveStream(STREAM_ID)).rejects.toThrow(
        /België/i,
      );
    });

    it("returns empty targetUrls with error code when stream fails", async () => {
      nock("https://media-services-public.vrt.be")
        .post("/vualto-video-aggregator-web/rest/external/v2/tokens")
        .reply(200, { vrtPlayerToken: "b1@test" });

      nock("https://media-services-public.vrt.be")
        .get(/\/vualto-video-aggregator-web\/rest\/external\/v2\/videos\//)
        .query(true)
        .reply(200, {
          code: "UNKNOWN_ERROR",
          targetUrls: [],
        });

      const auth = createMockAuth();
      const resolver = new StreamResolver(auth);

      const stream = await resolver.resolveStream(STREAM_ID);
      expect(stream.code).toBe("UNKNOWN_ERROR");
      expect(stream.targetUrls).toHaveLength(0);
    });

    it("throws on missing video token", async () => {
      const emptyStorage = new InMemoryTokenStorage();
      const auth = new VrtAuthService({ storage: emptyStorage });
      const resolver = new StreamResolver(auth);

      await expect(resolver.resolveStream(STREAM_ID)).rejects.toThrow(
        /video token/i,
      );
    });
  });
});
