import nock from "nock";
import { VrtAuthService } from "../../auth/VrtAuthService.ts";
import { InMemoryTokenStorage } from "../../auth/VrtAuthService";
import { VrtTokens } from "../../auth/types";

// ─── Fixtures ──────────────────────────────────────────────

const VALID_CREDENTIALS = { email: "user@example.com", password: "correct-password" };
const INVALID_CREDENTIALS = { email: "user@example.com", password: "wrong-password" };

const FAKE_SESSION = "session_abc123";
const FAKE_OIDCXSRF = "xsrf_xyz789";
const FAKE_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjAifQ.eyJleHAiOjk5OTk5OTk5OTksImlhdCI6MTcwMDAwMDAwMH0.abc";
const FAKE_VIDEO_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjAifQ.eyJleHAiOjk5OTk5OTk5OTksImlhdCI6MTcwMDAwMDAwMH0.def";
const FAKE_REFRESH_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjAifQ.eyJleHAiOjk5OTk5OTk5OTksImlhdCI6MTcwMDAwMDAwMH0.ghi";

const EXPIRED_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjAifQ.eyJleHAiOjEwMDAwMCwiaWF0IjoxMDAwMDB9.xyz";

function makeSetCookieHeader( cookies: Record<string, string>, domain = ".login.vrt.be"): string[] {
  return Object.entries(cookies).map(([name, value]) =>
    `${name}=${value}; Domain=${domain}; Path=/; HttpOnly; SameSite=Lax`,
  );
}

// ─── Helpers ───────────────────────────────────────────────

function createService(): VrtAuthService {
  const storage = new InMemoryTokenStorage();
  return new VrtAuthService({ storage });
}

// ───────────────────────────────────────────────────────────

describe("VrtAuthService", () => {
  afterEach(() => {
    nock.cleanAll();
  });

  describe("login()", () => {
    // ── Happy path ─────────────────────────────────────────
    it("performs full OIDC login flow and returns tokens", async () => {
      // Step 1: GET /vrtmax/sso/login → session cookies
      nock("https://www.vrt.be")
        .get("/vrtmax/sso/login")
        .reply(302, "", {
          Location: "https://login.vrt.be/authorize?state=abc",
          "Set-Cookie": makeSetCookieHeader({ SESSION: FAKE_SESSION, OIDCXSRF: FAKE_OIDCXSRF }),
        });

      // Step 2: POST /perform_login → redirect URL
      nock("https://login.vrt.be")
        .post("/perform_login", (body) => {
          return body.clientId === "vrtnu-site"
            && body.loginID === VALID_CREDENTIALS.email
            && body.password === VALID_CREDENTIALS.password;
        })
        .reply(403, {
          redirectUrl: "https://www.vrt.be/vrtmax/sso/callback?code=auth_code&state=abc",
          errorCode: 0,
        });

      // Step 3: GET /callback → tokens in cookies
      nock("https://www.vrt.be")
        .get("/vrtmax/sso/callback")
        .query(true)
        .reply(302, "", {
          Location: "https://www.vrt.be/vrtmax/",
          "Set-Cookie": [
            `vrtnu-site_profile_at=${FAKE_ACCESS_TOKEN}; Domain=.www.vrt.be; Path=/; HttpOnly`,
            `vrtnu-site_profile_vt=${FAKE_VIDEO_TOKEN}; Domain=.www.vrt.be; Path=/; HttpOnly`,
            `vrtnu-site_profile_rt=${FAKE_REFRESH_TOKEN}; Domain=.www.vrt.be; Path=/vrtmax/sso; HttpOnly`,
          ],
        });

      const service = createService();
      const tokens = await service.login(VALID_CREDENTIALS);

      expect(tokens.accessToken).toBe(FAKE_ACCESS_TOKEN);
      expect(tokens.videoToken).toBe(FAKE_VIDEO_TOKEN);
      expect(tokens.refreshToken).toBe(FAKE_REFRESH_TOKEN);
      expect(tokens.expiresAt).toBeGreaterThan(0);
      expect(tokens.acquiredAt).toBeGreaterThan(0);
    });

    // ── Wrong credentials ──────────────────────────────────
    it("throws InvalidCredentialsError on wrong password", async () => {
      nock("https://www.vrt.be")
        .get("/vrtmax/sso/login")
        .reply(302, "", {
          Location: "https://login.vrt.be/authorize?state=abc",
          "Set-Cookie": makeSetCookieHeader({ SESSION: FAKE_SESSION, OIDCXSRF: FAKE_OIDCXSRF }),
        });

      nock("https://login.vrt.be")
        .post("/perform_login")
        .reply(403, {
          errorCode: "invalid loginID or password",
          errorMessage: "invalid loginID or password",
        });

      const service = createService();
      await expect(service.login(INVALID_CREDENTIALS)).rejects.toThrow(
        /ongeldig/i,
      );
    });

    // ── Missing cookies after auth ──────────────────────────
    it("throws TokenAcquisitionError when redirect does not set expected tokens", async () => {
      nock("https://www.vrt.be")
        .get("/vrtmax/sso/login")
        .reply(302, "", {
          Location: "https://login.vrt.be/authorize?state=abc",
          "Set-Cookie": makeSetCookieHeader({ SESSION: FAKE_SESSION, OIDCXSRF: FAKE_OIDCXSRF }),
        });

      nock("https://login.vrt.be")
        .post("/perform_login")
        .reply(403, {
          redirectUrl: "https://www.vrt.be/vrtmax/sso/callback?code=abc&state=abc",
          errorCode: 0,
        });

      // Callback sets NO cookies (simulates auth failure)
      nock("https://www.vrt.be")
        .get("/vrtmax/sso/callback")
        .query(true)
        .reply(302, "", { Location: "https://www.vrt.be/vrtmax/" });

      const service = createService();
      await expect(service.login(VALID_CREDENTIALS)).rejects.toThrow(
        /token.*ontvangen/i,
      );
    });

    // ── Network failure ─────────────────────────────────────
    it("throws on network failure during /sso/login", async () => {
      nock("https://www.vrt.be")
        .get("/vrtmax/sso/login")
        .replyWithError("ECONNREFUSED");

      const service = createService();
      await expect(service.login(VALID_CREDENTIALS)).rejects.toThrow();
    });
  });

  describe("refreshTokens()", () => {
    it("sends refresh request with stored refresh token", async () => {
      nock("https://www.vrt.be")
        .get("/vrtmax/sso/refresh")
        .reply(200, "", {
          "Set-Cookie": [
            `vrtnu-site_profile_at=${FAKE_ACCESS_TOKEN}; Domain=.www.vrt.be; Path=/; HttpOnly`,
            `vrtnu-site_profile_vt=${FAKE_VIDEO_TOKEN}; Domain=.www.vrt.be; Path=/; HttpOnly`,
            `vrtnu-site_profile_rt=${FAKE_REFRESH_TOKEN}; Domain=.www.vrt.be; Path=/vrtmax/sso; HttpOnly`,
          ],
        });

      const service = createService();
      // Manually set a refresh token to simulate stored session
      // We do this by calling a method that stores it, or accessing storage directly
      const storage = new InMemoryTokenStorage();
      await storage.set("vrtnu-site_profile_rt", FAKE_REFRESH_TOKEN);
      const svc = new VrtAuthService({ storage });

      const tokens = await svc.refreshTokens();
      expect(tokens.accessToken).toBe(FAKE_ACCESS_TOKEN);
      expect(tokens.videoToken).toBe(FAKE_VIDEO_TOKEN);
    });

    it("throws TokenExpiredError on 401 response", async () => {
      nock("https://www.vrt.be")
        .get("/vrtmax/sso/refresh")
        .reply(401, "Unauthorized");

      const storage = new InMemoryTokenStorage();
      await storage.set("vrtnu-site_profile_rt", "expired-refresh-token");
      const svc = new VrtAuthService({ storage });

      await expect(svc.refreshTokens()).rejects.toThrow(/sessie verlopen/i);
    });
  });

  describe("getAccessToken()", () => {
    it("returns cached token if not expired", async () => {
      // Store a non-expired token directly
      const storage = new InMemoryTokenStorage();
      const future = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
      const tokens: VrtTokens = {
        accessToken: FAKE_ACCESS_TOKEN,
        videoToken: FAKE_VIDEO_TOKEN,
        refreshToken: FAKE_REFRESH_TOKEN,
        expiresAt: future,
        acquiredAt: Math.floor(Date.now() / 1000),
      };
      await storage.set("vrtnu_token_meta", JSON.stringify(tokens));

      const svc = new VrtAuthService({ storage });
      const token = await svc.getAccessToken();
      expect(token).toBe(FAKE_ACCESS_TOKEN);
    });

    it("auto-refreshes if within 5 minutes of expiry", async () => {
      // Token expires in 2 minutes — should trigger refresh
      const soon = Math.floor(Date.now() / 1000) + 120;
      const storage = new InMemoryTokenStorage();
      const tokens: VrtTokens = {
        accessToken: FAKE_ACCESS_TOKEN,
        videoToken: FAKE_VIDEO_TOKEN,
        refreshToken: FAKE_REFRESH_TOKEN,
        expiresAt: soon,
        acquiredAt: Math.floor(Date.now() / 1000),
      };
      await storage.set("vrtnu_token_meta", JSON.stringify(tokens));

      // Mock refresh endpoint
      nock("https://www.vrt.be")
        .get("/vrtmax/sso/refresh")
        .reply(200, "", {
          "Set-Cookie": [
            `vrtnu-site_profile_at=${FAKE_ACCESS_TOKEN}; Domain=.www.vrt.be; Path=/; HttpOnly`,
            `vrtnu-site_profile_vt=${FAKE_VIDEO_TOKEN}; Domain=.www.vrt.be; Path=/; HttpOnly`,
            `vrtnu-site_profile_rt=${FAKE_REFRESH_TOKEN}; Domain=.www.vrt.be; Path=/vrtmax/sso; HttpOnly`,
          ],
        });

      const svc = new VrtAuthService({ storage });
      const token = await svc.getAccessToken();
      expect(token).toBe(FAKE_ACCESS_TOKEN);
    });

    it("throws AuthenticationError if not logged in", async () => {
      const storage = new InMemoryTokenStorage();
      const svc = new VrtAuthService({ storage });

      await expect(svc.getAccessToken()).rejects.toThrow(/niet ingelogd/i);
    });
  });

  describe("isLoggedIn()", () => {
    it("returns true if valid tokens exist", async () => {
      const storage = new InMemoryTokenStorage();
      const future = Math.floor(Date.now() / 1000) + 3600;
      await storage.set("vrtnu_token_meta", JSON.stringify({
        accessToken: FAKE_ACCESS_TOKEN,
        videoToken: FAKE_VIDEO_TOKEN,
        refreshToken: FAKE_REFRESH_TOKEN,
        expiresAt: future,
        acquiredAt: Math.floor(Date.now() / 1000),
      } satisfies VrtTokens));

      const svc = new VrtAuthService({ storage });
      expect(await svc.isLoggedIn()).toBe(true);
    });

    it("returns false if tokens expired", async () => {
      const storage = new InMemoryTokenStorage();
      const past = Math.floor(Date.now() / 1000) - 3600;
      await storage.set("vrtnu_token_meta", JSON.stringify({
        accessToken: FAKE_ACCESS_TOKEN,
        videoToken: FAKE_VIDEO_TOKEN,
        refreshToken: FAKE_REFRESH_TOKEN,
        expiresAt: past,
        acquiredAt: past - 3600,
      } satisfies VrtTokens));

      const svc = new VrtAuthService({ storage });
      expect(await svc.isLoggedIn()).toBe(false);
    });

    it("returns false if never logged in", async () => {
      const svc = createService();
      expect(await svc.isLoggedIn()).toBe(false);
    });
  });

  describe("logout()", () => {
    it("clears all stored tokens", async () => {
      const storage = new InMemoryTokenStorage();
      await storage.set("vrtnu-site_profile_at", FAKE_ACCESS_TOKEN);
      await storage.set("vrtnu-site_profile_vt", FAKE_VIDEO_TOKEN);
      await storage.set("vrtnu-site_profile_rt", FAKE_REFRESH_TOKEN);
      await storage.set("vrtnu_token_meta", JSON.stringify({}));

      const svc = new VrtAuthService({ storage });
      await svc.logout();

      expect(await storage.get("vrtnu-site_profile_at")).toBeNull();
      expect(await storage.get("vrtnu-site_profile_vt")).toBeNull();
      expect(await storage.get("vrtnu-site_profile_rt")).toBeNull();
      expect(await storage.get("vrtnu_token_meta")).toBeNull();
    });
  });
});
