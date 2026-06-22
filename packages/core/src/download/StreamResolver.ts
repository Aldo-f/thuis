import { VrtAuthService } from "../auth/VrtAuthService.js";
import {
  StreamData,
  StreamDataSchema,
  StreamError,
  DrmError,
  GeoBlockedError,
  STREAM_ERROR_CODES,
} from "./types.js";

// ─── JWT Player Info Constants ─────────────────────────────

const JWT_KEY_ID = "0-0Fp51UZykfaiCJrfTE3+oMI8zvDteYfPtR+2n1R+z8w=";
const JWT_SIGNING_KEY = "b5f500d55cb44715107249ccd8a5c0136cfb2788dbb71b90a4f142423bacaf38";

const PLAYER_INFO_TEMPLATE = {
  platform: "desktop",
  app: { type: "browser", name: "Chrome" },
  device: "undefined (undefined)",
  os: { name: "Windows", version: "10" },
  player: { name: "VRT web player", version: "5.1.1-prod-2025-02-14T08:44:16" },
};

// ─── API URLs ──────────────────────────────────────────────

const VUALTO_BASE = "https://media-services-public.vrt.be";
const TOKEN_URL = `${VUALTO_BASE}/vualto-video-aggregator-web/rest/external/v2/tokens`;

function videoUrl(streamId: string): string {
  const encoded = encodeURIComponent(streamId);
  return `${VUALTO_BASE}/vualto-video-aggregator-web/rest/external/v2/videos/${encoded}`;
}

// ─── JWT Helper ────────────────────────────────────────────

/**
 * Create a signed JWT for the player info.
 * Uses HMAC-SHA256 with the VRT player's known signing key.
 */
async function createPlayerInfoJwt(): Promise<string> {
  const header = { alg: "HS256", kid: JWT_KEY_ID };
  const payload = {
    ...PLAYER_INFO_TEMPLATE,
    exp: Math.round((Date.now() / 1000) + 900),
  };

  const base64Url = (obj: unknown): string => {
    const json = JSON.stringify(obj);
    const encoded = btoa(json);
    return encoded.replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
  };

  const headerB64 = base64Url(header);
  const payloadB64 = base64Url(payload);
  const signingInput = `${headerB64}.${payloadB64}`;

  // Sign with HMAC-SHA256 using Web Crypto API
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(JWT_SIGNING_KEY),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );

  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(signingInput),
  );

  const sigB64 = btoa(String.fromCharCode(...new Uint8Array(signature)))
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");

  return `${signingInput}.${sigB64}`;
}

// ─── StreamResolver ────────────────────────────────────────

export class StreamResolver {
  constructor(private authService: VrtAuthService) {}

  /**
   * Resolve a streamId to StreamData with HLS manifest URLs.
   *
   * 1. Gets video token from auth service
   * 2. Creates a signed playerInfo JWT
   * 3. Gets a vrtPlayerToken from the vualto API
   * 4. Fetches stream data from the vualto video API
   * 5. Parses and validates the response
   */
  async resolveStream(streamId: string): Promise<StreamData> {
    const videoToken = await this.authService.getVideoToken().catch(() => {
      throw new StreamError(
        "Video token niet beschikbaar. Log opnieuw in.",
        "NO_VIDEO_TOKEN",
      );
    });

    // Step 1: Get vrtPlayerToken
    const playerToken = await this.getPlayerToken(videoToken);

    // Step 2: Get stream data
    const streamUrl = new URL(videoUrl(streamId));
    streamUrl.searchParams.set("client", "vrtnu-web@PROD");
    streamUrl.searchParams.set("vrtPlayerToken", playerToken);

    const response = await fetch(streamUrl.toString(), {
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new StreamError(
        `Stream-verzoek mislukt (status ${response.status})`,
        "STREAM_FETCH_FAILED",
      );
    }

    const data = await response.json();

    // Check for error codes
    if (data.code) {
      this.handleStreamErrorCode(data.code);
    }

    // Check DRM
    if (data.drm) {
      throw new DrmError();
    }

    const parsed = StreamDataSchema.parse(data);
    return parsed;
  }

  private async getPlayerToken(videoToken: string): Promise<string> {
    const playerInfoJwt = await createPlayerInfoJwt();

    const response = await fetch(TOKEN_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identityToken: videoToken,
        playerInfo: playerInfoJwt,
      }),
    });

    if (!response.ok) {
      throw new StreamError(
        `Player token aanvraag mislukt (status ${response.status})`,
        "PLAYER_TOKEN_FAILED",
      );
    }

    const json = await response.json();
    const token = json.vrtPlayerToken;
    if (!token) {
      throw new StreamError(
        "Geen player token ontvangen.",
        "PLAYER_TOKEN_MISSING",
      );
    }

    return token;
  }

  private handleStreamErrorCode(code: string): void {
    switch (code) {
      case STREAM_ERROR_CODES.GEO_BLOCKED:
      case STREAM_ERROR_CODES.GEO_BLOCKED_ALT:
      case STREAM_ERROR_CODES.GEO_BLOCKED_PROXY:
      case STREAM_ERROR_CODES.EXPATS:
        throw new GeoBlockedError();
      case STREAM_ERROR_CODES.AGE_RESTRICTED:
      case STREAM_ERROR_CODES.LOGIN_REQUIRED:
        throw new StreamError(
          "Je moet ingelogd zijn om deze video te bekijken.",
          "AUTH_REQUIRED",
        );
    }
  }
}
