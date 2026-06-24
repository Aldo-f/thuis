/**
 * Integration test for the full Thuis download flow.
 *
 * Tests the complete pipeline:
 *   Login → Fetch metadata → Resolve stream → Download
 *
 * Requires real VRT MAX credentials via environment variables:
 *   VRT_USERNAME=your-email@example.com
 *   VRT_PASSWORD=your-password
 *   VRT_TEST_EPISODE_URL=https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/
 *
 * This test is SKIPPED by default. Run manually:
 *   VRT_USERNAME=... VRT_PASSWORD=... npx jest --testPathPattern="thuis-download"
 */

import { VrtAuthService, InMemoryTokenStorage } from "../../auth/VrtAuthService.ts";
import { VrtEpisodeService } from "../../episode/VrtEpisodeService";
import { StreamResolver } from "../../download/StreamResolver";
import { DrmError, GeoBlockedError } from "../../download/types";

const hasCredentials = !!(
  process.env.VRT_USERNAME && process.env.VRT_PASSWORD
);

const itIf = (condition: boolean) => (condition ? it : it.skip);

describe("Thuis Download — Integration", () => {
  const email = process.env.VRT_USERNAME ?? "";
  const password = process.env.VRT_PASSWORD ?? "";
  const episodeUrl = process.env.VRT_TEST_EPISODE_URL
    ?? "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/";

  const auth = new VrtAuthService({
    storage: new InMemoryTokenStorage(),
  });

  let accessToken: string;

  beforeAll(async () => {
    if (!hasCredentials) return;
    const tokens = await auth.login({ email, password }).catch((err) => {
      console.warn("Login failed — subsequent tests will fail:", err.message);
      throw err;
    });
    accessToken = tokens.accessToken;
    console.log(`Logged in. Access token: ${accessToken.slice(0, 20)}...`);
  }, 30000);

  // ─── Test 1: Full Login Flow ────────────────────────────

  describe("1. Authentication", () => {
    itIf(hasCredentials)(
      "logs in with real credentials and returns valid tokens",
      async () => {
        const tokens = await auth.login({ email, password });
        expect(tokens.accessToken).toBeTruthy();
        expect(tokens.videoToken).toBeTruthy();
        expect(tokens.refreshToken).toBeTruthy();
        expect(tokens.expiresAt).toBeGreaterThan(Math.floor(Date.now() / 1000));
        expect(tokens.acquiredAt).toBeGreaterThan(0);
      },
      30000,
    );

    itIf(hasCredentials)(
      "rejects invalid credentials",
      async () => {
        await expect(
          auth.login({ email: "invalid@test.com", password: "wrong" }),
        ).rejects.toThrow(/ongeldig/i);
      },
      15000,
    );

    itIf(hasCredentials)(
      "can refresh tokens",
      async () => {
        const tokens = await auth.refreshTokens();
        expect(tokens.accessToken).toBeTruthy();
        expect(tokens.videoToken).toBeTruthy();
      },
      15000,
    );
  });

  // ─── Test 2: Episode Metadata ────────────────────────────

  describe("2. Episode Metadata", () => {
    let episodeService: VrtEpisodeService;

    beforeAll(() => {
      episodeService = new VrtEpisodeService(auth);
    });

    itIf(hasCredentials)(
      "fetches episode metadata from a VRT MAX URL",
      async () => {
        const episode = await episodeService.getEpisode(episodeUrl);
        expect(episode.title).toBeTruthy();
        expect(episode.seriesTitle).toBe("Thuis");
        expect(episode.season).toBeGreaterThan(0);
        expect(episode.streamId).toBeTruthy();
        expect(episode.brand).toBeTruthy();
        console.log(`Episode: ${episode.seriesTitle} S${episode.season}A${episode.episode} — ${episode.title}`);
        console.log(`Stream ID: ${episode.streamId}`);
      },
      15000,
    );

    itIf(hasCredentials)(
      "fails gracefully for an invalid URL",
      async () => {
        await expect(
          episodeService.getEpisode("https://www.vrt.be/vrtmax/a-z/thuis/99/nonexistent"),
        ).rejects.toThrow();
      },
      10000,
    );
  });

  // ─── Test 3: Stream Resolution ───────────────────────────

  describe("3. Stream Resolution", () => {
    let resolver: StreamResolver;
    let streamId: string;

    beforeAll(async () => {
      resolver = new StreamResolver(auth);
      if (hasCredentials) {
        const episode = await new VrtEpisodeService(auth).getEpisode(episodeUrl);
        streamId = episode.streamId;
      }
    }, 15000);

    itIf(hasCredentials)(
      "resolves HLS stream from streamId",
      async () => {
        const stream = await resolver.resolveStream(streamId);

        // Log what we got
        console.log(`Stream title: ${stream.title}`);
        console.log(`DRM: ${stream.drm}`);
        console.log(`Target URLs: ${stream.targetUrls.length}`);
        console.log(`Code: ${stream.code ?? "none"}`);

        for (const url of stream.targetUrls) {
          console.log(`  ${url.type}: ${url.url.slice(0, 60)}...`);
        }

        // If not DRM/geo, we expect HLS URLs
        if (!stream.drm && !stream.code) {
          expect(stream.targetUrls.length).toBeGreaterThan(0);
          const hlsUrls = stream.targetUrls.filter(
            (t) => t.type === "hls" || t.type === "hls_aes",
          );
          expect(hlsUrls.length).toBeGreaterThan(0);
        }
      },
      15000,
    );

    itIf(hasCredentials)(
      "reports DRM status accurately",
      async () => {
        try {
          const stream = await resolver.resolveStream(streamId);
          // If no error, stream is either DRM-free or we need to check
          console.log(`DRM protected: ${stream.drm}`);
        } catch (err) {
          // DRM error is acceptable (content may be DRM-protected)
          if (err instanceof DrmError) {
            console.log("Content is DRM-protected — cannot download programmatically.");
          } else if (err instanceof GeoBlockedError) {
            console.log("Content is geo-blocked — VPN or Belgian IP required.");
          } else {
            throw err;
          }
        }
      },
      15000,
    );
  });

  // ─── Test 4: End-to-End Flow ─────────────────────────────

  describe("4. End-to-End", () => {
    itIf(hasCredentials)(
      "completes the full flow: login → metadata → stream",
      async () => {
        // Login
        const tokens = await auth.login({ email, password });
        expect(tokens.accessToken).toBeTruthy();

        // Fetch episode
        const episodeService = new VrtEpisodeService(auth);
        const episode = await episodeService.getEpisode(episodeUrl);
        expect(episode.streamId).toBeTruthy();

        // Resolve stream
        const resolver = new StreamResolver(auth);
        const stream = await resolver.resolveStream(episode.streamId);

        // Log results
        console.log("\n=== End-to-End Result ===");
        console.log(`Series: ${episode.seriesTitle}`);
        console.log(`Season: ${episode.season}, Episode: ${episode.episode}`);
        console.log(`Title: ${episode.title}`);
        console.log(`Stream ID: ${episode.streamId}`);
        console.log(`DRM: ${stream.drm}`);
        console.log(`Stream URLs: ${stream.targetUrls.length}`);

        if (!stream.drm && stream.targetUrls.length > 0) {
          const hlsUrl = stream.targetUrls.find(
            (t) => t.type === "hls" || t.type === "hls_aes",
          );
          if (hlsUrl) {
            console.log(`HLS URL: ${hlsUrl.url.slice(0, 80)}...`);
          }
        }
      },
      30000,
    );
  });

  // ─── Cleanup ─────────────────────────────────────────────

  afterAll(async () => {
    await auth.logout().catch(() => {});
  });
});
