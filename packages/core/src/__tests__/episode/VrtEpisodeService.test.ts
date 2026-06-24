import nock from "nock";
import { VrtEpisodeService } from "../../episode/VrtEpisodeService.ts";
import { InMemoryTokenStorage } from "../../auth/VrtAuthService.ts";
import { VrtAuthService } from "../../auth/VrtAuthService.ts";
import { VrtTokens } from "../../auth/types";

// ─── Fixtures ──────────────────────────────────────────────

const FAKE_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjAifQ.eyJleHAiOjk5OTk5OTk5OTksImlhdCI6MTcwMDAwMDAwMH0.abc";
const FAKE_VIDEO_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjAifQ.eyJleHAiOjk5OTk5OTk5OTksImlhdCI6MTcwMDAwMDAwMH0.def";
const FAKE_REFRESH_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjAifQ.eyJleHAiOjk5OTk5OTk5OTksImlhdCI6MTcwMDAwMDAwMH0.ghi";

const EPISODE_URL = "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/";

const MOCK_GRAPHQL_RESPONSE = {
  data: {
    page: {
      episode: {
        id: "1740392401937",
        title: "Aflevering 105",
        name: "Thuis - Seizoen 31 - Aflevering 105",
        description: "Marie stelt een nieuwe collega voor aan het team.",
        durationRaw: "PT30M",
        episodeNumberRaw: 105,
        onTimeRaw: "2025-03-03T20:00:00+01:00",
        ageRaw: "ALL",
        program: { title: "Thuis" },
        season: { id: "1739450401467", titleRaw: "31" },
        brand: "een",
      },
      ldjson: null,
      player: {
        image: { templateUrl: "https://images.vrt.be/thumb.jpg" },
        modes: [{ streamId: "pbs-pub-abc123$vid-def456" }],
      },
    },
  },
};

// ─── Helpers ───────────────────────────────────────────────

function createMockAuthService(tokens?: Partial<VrtTokens>): VrtAuthService {
  const storage = new InMemoryTokenStorage();
  const future = Math.floor(Date.now() / 1000) + 3600;
  const defaultTokens: VrtTokens = {
    accessToken: FAKE_ACCESS_TOKEN,
    videoToken: FAKE_VIDEO_TOKEN,
    refreshToken: FAKE_REFRESH_TOKEN,
    expiresAt: future,
    acquiredAt: Math.floor(Date.now() / 1000),
    ...tokens,
  };
  storage.set("vrtnu_token_meta", JSON.stringify(defaultTokens));
  storage.set("vrtnu-site_profile_at", FAKE_ACCESS_TOKEN);
  storage.set("vrtnu-site_profile_vt", FAKE_VIDEO_TOKEN);
  return new VrtAuthService({ storage });
}

// ───────────────────────────────────────────────────────────

describe("VrtEpisodeService", () => {
  afterEach(() => {
    nock.cleanAll();
  });

  describe("getEpisode()", () => {
    it("sends VideoPage GraphQL query and returns parsed episode detail", async () => {
      nock("https://www.vrt.be")
        .post("/vrtnu-api/graphql/v1", (body: any) => {
          return body.operationName === "VideoPage"
            && body.variables.pageId === "/vrtmax/a-z/thuis/31/thuis-s31a6105/";
        })
        .reply(200, MOCK_GRAPHQL_RESPONSE, {
          "Content-Type": "application/json",
        });

      const auth = createMockAuthService();
      const service = new VrtEpisodeService(auth);
      const episode = await service.getEpisode(EPISODE_URL);

      expect(episode.title).toBe("Aflevering 105");
      expect(episode.seriesTitle).toBe("Thuis");
      expect(episode.season).toBe(31);
      expect(episode.episode).toBe(105);
      expect(episode.description).toBe("Marie stelt een nieuwe collega voor aan het team.");
      expect(episode.streamId).toBe("pbs-pub-abc123$vid-def456");
      expect(episode.brand).toBe("een");
      expect(episode.durationSeconds).toBe(1800);
    });

    it("uses public endpoint when no auth token available", async () => {
      nock("https://www.vrt.be")
        .post("/vrtnu-api/graphql/public/v1")
        .reply(200, MOCK_GRAPHQL_RESPONSE, {
          "Content-Type": "application/json",
        });

      // Auth service with no tokens
      const auth = new VrtAuthService({ storage: new InMemoryTokenStorage() });
      const service = new VrtEpisodeService(auth);
      const episode = await service.getEpisode(EPISODE_URL);

      expect(episode.title).toBe("Aflevering 105");
    });

    it("retries with refreshed token on 401", async () => {
      // First call returns 401
      nock("https://www.vrt.be")
        .post("/vrtnu-api/graphql/v1")
        .reply(401, "Unauthorized");

      // Refresh endpoint
      nock("https://www.vrt.be")
        .get("/vrtmax/sso/refresh")
        .reply(200, "", {
          "Set-Cookie": [
            `vrtnu-site_profile_at=${FAKE_ACCESS_TOKEN}; Domain=.www.vrt.be; Path=/; HttpOnly`,
            `vrtnu-site_profile_vt=${FAKE_VIDEO_TOKEN}; Domain=.www.vrt.be; Path=/; HttpOnly`,
            `vrtnu-site_profile_rt=${FAKE_REFRESH_TOKEN}; Domain=.www.vrt.be; Path=/vrtmax/sso; HttpOnly`,
          ],
        });

      // Second call after refresh succeeds
      nock("https://www.vrt.be")
        .post("/vrtnu-api/graphql/v1")
        .reply(200, MOCK_GRAPHQL_RESPONSE, {
          "Content-Type": "application/json",
        });

      const auth = createMockAuthService();
      const service = new VrtEpisodeService(auth);
      const episode = await service.getEpisode(EPISODE_URL);

      expect(episode.title).toBe("Aflevering 105");
      expect(episode.streamId).toBe("pbs-pub-abc123$vid-def456");
    });

    it("throws EpisodeUnavailableError when no streamId in response", async () => {
      const noStreamResponse = {
        data: {
          page: {
            episode: { title: "Test", program: { title: "Test" }, season: { titleRaw: "1" } },
            player: { modes: [] },
          },
        },
      };

      nock("https://www.vrt.be")
        .post("/vrtnu-api/graphql/v1")
        .reply(200, noStreamResponse, { "Content-Type": "application/json" });

      const auth = createMockAuthService();
      const service = new VrtEpisodeService(auth);

      await expect(service.getEpisode(EPISODE_URL)).rejects.toThrow(
        /stream id/i,
      );
    });

    it("throws EpisodeUnavailableError when GraphQL returns errors", async () => {
      nock("https://www.vrt.be")
        .post("/vrtnu-api/graphql/v1")
        .reply(200, {
          errors: [{ message: "Page not found" }],
        });

      const auth = createMockAuthService();
      const service = new VrtEpisodeService(auth);

      await expect(service.getEpisode(EPISODE_URL)).rejects.toThrow(
        /GraphQL-fout/i,
      );
    });
  });
});
