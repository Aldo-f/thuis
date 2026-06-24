import {
  VrtCredentials,
  VrtCredentialsSchema,
  VrtTokens,
  VrtTokensSchema,
  VrtLoginResponseSchema,
  TokenStorage,
  TOKEN_KEYS,
} from "./types.js";

// ─── Error types ───────────────────────────────────────────

export class VrtError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = "VrtError";
  }
}

export class AuthenticationError extends VrtError {
  constructor(message: string, code = "AUTH_FAILED") {
    super(message, code);
    this.name = "AuthenticationError";
  }
}

export class InvalidCredentialsError extends AuthenticationError {
  constructor(message = "Ongeldig e-mailadres of wachtwoord") {
    super(message, "INVALID_CREDENTIALS");
    this.name = "InvalidCredentialsError";
  }
}

export class TokenAcquisitionError extends AuthenticationError {
  constructor(message = "Token-acquisitie mislukt") {
    super(message, "TOKEN_ACQUISITION_FAILED");
    this.name = "TokenAcquisitionError";
  }
}

export class TokenExpiredError extends AuthenticationError {
  constructor(message = "Sessie verlopen. Log opnieuw in.") {
    super(message, "TOKEN_EXPIRED");
    this.name = "TokenExpiredError";
  }
}

// ─── In-memory token storage ───────────────────────────────

export class InMemoryTokenStorage implements TokenStorage {
  private store = new Map<string, string>();

  async get(key: string): Promise<string | null> {
    return this.store.get(key) ?? null;
  }

  async set(key: string, value: string): Promise<void> {
    this.store.set(key, value);
  }

  async delete(key: string): Promise<void> {
    this.store.delete(key);
  }
}

// ─── VrtAuthService ────────────────────────────────────────

export interface VrtAuthServiceOptions {
  storage?: TokenStorage;
  /** Override the default base URLs for testing */
  baseUrl?: string;
  loginUrl?: string;
}

export class VrtAuthService {
  private storage: TokenStorage;
  private baseUrl: string;
  private loginBaseUrl: string;

  // Cookie jar for managing session cookies
  private cookies = new Map<string, string>();

  constructor(options: VrtAuthServiceOptions = {}) {
    this.storage = options.storage ?? new InMemoryTokenStorage();
    this.baseUrl = options.baseUrl ?? "/vrtbe";
    this.loginBaseUrl = options.loginUrl ?? "/loginvrt";
  }

  // ─── Public API ─────────────────────────────────────────

  /**
   * Full OIDC login flow:
   * 1. GET /vrtmax/sso/login → session cookies
   * 2. POST /perform_login → redirectUrl
   * 3. GET redirectUrl → extract tokens from Set-Cookie headers
   */
  async login(credentials: VrtCredentials): Promise<VrtTokens> {
    const parsed = VrtCredentialsSchema.parse(credentials);

    // Step 1: Get session cookies
    await this.fetchSessionCookies();

    // Step 2: Perform login
    const redirectUrl = await this.performLogin(parsed);

    // Step 3: Follow redirect to extract tokens
    const tokens = await this.extractTokensFromRedirect(redirectUrl);

    // Store tokens
    await this.storeTokens(tokens);
    return tokens;
  }

  /**
   * Refresh tokens using the stored refresh token.
   * Calls /vrtmax/sso/refresh which returns new Set-Cookie headers.
   */
  async refreshTokens(): Promise<VrtTokens> {
    let refreshToken = await this.storage.get(TOKEN_KEYS.REFRESH_TOKEN);
    if (!refreshToken) {
      const meta = await this.getStoredTokenMeta();
      refreshToken = meta?.refreshToken ?? null;
    }
    if (!refreshToken) {
      throw new TokenExpiredError();
    }

    // Set the refresh token cookie manually
    this.setCookie(TOKEN_KEYS.REFRESH_TOKEN, refreshToken);

    const url = `${this.baseUrl}/vrtmax/sso/refresh`;
    const response = await this.fetchWithCookies(url, { redirect: "manual" });

    if (response.status === 401) {
      await this.clearStoredTokens();
      throw new TokenExpiredError();
    }

    if (!response.ok && response.status !== 302) {
      throw new TokenExpiredError();
    }

    const tokens = this.extractTokensFromHeaders(response.headers);
    await this.storeTokens(tokens);
    return tokens;
  }

  /**
   * Get a valid access token. Auto-refreshes if within 5 minutes of expiry.
   * Throws AuthenticationError if not logged in and no valid cached tokens.
   */
  async getAccessToken(): Promise<string> {
    const meta = await this.getStoredTokenMeta();
    if (meta && !this.isTokenExpired(meta.expiresAt, 300)) {
      const stored = await this.storage.get(TOKEN_KEYS.ACCESS_TOKEN);
      if (stored) return stored;
      // Fall back to meta if separate storage missing but meta exists
      if (meta.accessToken) return meta.accessToken;
    }

    // Token expired or about to expire — try to refresh
    if (meta) {
      try {
        const refreshed = await this.refreshTokens();
        return refreshed.accessToken;
      } catch {
        // Refresh failed, fall through to error
      }
    }

    throw new AuthenticationError(
      "Niet ingelogd. Log eerst in via de instellingen.",
      "AUTH_FAILED",
    );
  }

  /**
   * Get a valid video token. Auto-refreshes if needed.
   */
  async getVideoToken(): Promise<string> {
    // Video token has same expiry as access token
    const accessToken = await this.getAccessToken();
    // Ensure video token is also refreshed by checking storage
    const videoToken = await this.storage.get(TOKEN_KEYS.VIDEO_TOKEN);
    if (videoToken) return videoToken;
    throw new AuthenticationError("Video token niet beschikbaar");
  }

  /**
   * Check if there are stored (and non-expired) tokens.
   */
  async isLoggedIn(): Promise<boolean> {
    const meta = await this.getStoredTokenMeta();
    if (!meta) return false;
    return !this.isTokenExpired(meta.expiresAt, 0);
  }

  /**
   * Clear all stored tokens.
   */
  async logout(): Promise<void> {
    await this.clearStoredTokens();
    this.cookies.clear();
  }

  // ─── Private: auth flow steps ───────────────────────────

  private async fetchSessionCookies(): Promise<void> {
    const url = `${this.baseUrl}/vrtmax/sso/login`;
    const response = await this.fetchWithCookies(url, { redirect: "manual" });

    if (response.status !== 302) {
      throw new AuthenticationError(
        `Kon sessie niet starten (status ${response.status})`,
      );
    }

    // Extract cookies from response headers
    this.extractCookiesFromHeaders(response.headers);
  }

  private async performLogin(credentials: VrtCredentials): Promise<string> {
    const xsrf = this.cookies.get("OIDCXSRF");
    if (!xsrf) {
      throw new AuthenticationError("OIDCXSRF cookie ontbreekt — geen sessie beschikbaar");
    }

    const url = `${this.loginBaseUrl}/perform_login`;
    const response = await this.fetchWithCookies(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Oidcxsrf: xsrf,
      },
      body: JSON.stringify({
        clientId: "vrtnu-site",
        loginID: credentials.email,
        password: credentials.password,
      }),
      redirect: "manual",
    });

    // /perform_login returns 403 on SUCCESS (yes, really)
    if (response.status !== 403 && response.status !== 200) {
      throw new AuthenticationError(
        `Login mislukt (status ${response.status})`,
      );
    }

    const responseBody = VrtLoginResponseSchema.parse(await response.json());

    if (responseBody.errorCode && responseBody.errorCode !== 0) {
      const msg = responseBody.errorMessage || "Onbekende fout";
      if (/invalid loginID or password/i.test(msg)) {
        throw new InvalidCredentialsError();
      }
      throw new AuthenticationError(msg);
    }

    if (!responseBody.redirectUrl) {
      throw new TokenAcquisitionError("Geen redirectUrl ontvangen na login");
    }

    return responseBody.redirectUrl;
  }

  private async extractTokensFromRedirect(redirectUrl: string): Promise<VrtTokens> {
    const response = await this.fetchWithCookies(redirectUrl, { redirect: "manual" });

    return this.extractTokensFromHeaders(response.headers);
  }

  private extractTokensFromHeaders(headers: Headers): VrtTokens {
    const setCookieHeaders = this.parseSetCookieHeaders(headers);

    const accessToken = setCookieHeaders[TOKEN_KEYS.ACCESS_TOKEN];
    const videoToken = setCookieHeaders[TOKEN_KEYS.VIDEO_TOKEN];
    const refreshToken = setCookieHeaders[TOKEN_KEYS.REFRESH_TOKEN];

    if (!accessToken || !videoToken || !refreshToken) {
      throw new TokenAcquisitionError(
        "Niet alle tokens ontvangen na authenticatie",
      );
    }

    // Decode JWT to get expiry
    let expiresAt = Math.floor(Date.now() / 1000) + 3600;
    try {
      const payload = this.decodeJwt(accessToken);
      if (payload?.exp) {
        expiresAt = Number(payload.exp) || expiresAt;
      }
    } catch {
      // If JWT decoding fails, use a reasonable default
    }

    return VrtTokensSchema.parse({
      accessToken,
      videoToken,
      refreshToken,
      expiresAt,
      acquiredAt: Math.floor(Date.now() / 1000),
    });
  }

  // ─── Private: cookie management ─────────────────────────

  private extractCookiesFromHeaders(headers: Headers): void {
    const entries = this.parseAllSetCookieHeaders(headers);
    for (const [name, value] of entries) {
      this.cookies.set(name, value);
    }
  }

  private setCookie(name: string, value: string): void {
    this.cookies.set(name, value);
  }

  private async fetchWithCookies(
    url: string,
    init: RequestInit & { redirect?: RequestRedirect } = {},
  ): Promise<Response> {
    const cookieHeader = Array.from(this.cookies.entries())
      .map(([name, value]) => `${name}=${value}`)
      .join("; ");

    const headers = new Headers(init.headers);
    if (cookieHeader) {
      headers.set("Cookie", cookieHeader);
    }

    const response = await fetch(url, {
      ...init,
      headers,
      redirect: "manual",
    });

    // Extract Set-Cookie headers from response
    this.extractCookiesFromHeaders(response.headers);

    return response;
  }

  /**
   * Parse Set-Cookie headers into name-value pairs.
   * Handles the case where multiple cookies are combined into one header value
   * (as nock does) by splitting on "," between separate cookie directives.
   */
  private parseSetCookieHeaders(headers: Headers): Record<string, string> {
    const result: Record<string, string> = {};
    for (const [name, value] of this.parseAllSetCookieHeaders(headers)) {
      result[name] = value;
    }
    return result;
  }

  /**
   * Extract all cookie name-value pairs from Set-Cookie headers,
   * handling combined headers (multiple cookies joined by ",").
   */
  private parseAllSetCookieHeaders(headers: Headers): Array<[string, string]> {
    const rawHeaders: string[] = [];
    // getSetCookie() is available in Node 20+ but nock may combine them
    const setCookieArr = headers.getSetCookie?.() ?? [];

    // Also handle the raw set-cookie header (nock workaround)
    const rawHeader = headers.get("set-cookie");
    if (rawHeader && setCookieArr.length <= 1) {
      // Try to split combined cookies
      rawHeaders.push(rawHeader);
    } else {
      rawHeaders.push(...setCookieArr);
    }

    const result: Array<[string, string]> = [];
    for (const raw of rawHeaders) {
      // Try splitting on ", " — but be careful:
      // "name=val; attr, name2=val2; attr2" — we need to split between cookies
      // We split on comma followed by a word character before =
      const parts = raw.split(/,(?=[-\w.]+=)/);
      for (const part of parts) {
        const eqIndex = part.indexOf("=");
        if (eqIndex === -1) continue;
        const name = part.slice(0, eqIndex).trim();
        const value = part.slice(eqIndex + 1).split(";")[0]?.trim();
        if (name && value) {
          result.push([name, value]);
        }
      }
    }
    return result;
  }

  // ─── Private: token storage ─────────────────────────────

  private async storeTokens(tokens: VrtTokens): Promise<void> {
    await this.storage.set(TOKEN_KEYS.ACCESS_TOKEN, tokens.accessToken);
    await this.storage.set(TOKEN_KEYS.VIDEO_TOKEN, tokens.videoToken);
    await this.storage.set(TOKEN_KEYS.REFRESH_TOKEN, tokens.refreshToken);
    await this.storage.set(TOKEN_KEYS.TOKEN_META, JSON.stringify(tokens));
  }

  private async clearStoredTokens(): Promise<void> {
    await this.storage.delete(TOKEN_KEYS.ACCESS_TOKEN);
    await this.storage.delete(TOKEN_KEYS.VIDEO_TOKEN);
    await this.storage.delete(TOKEN_KEYS.REFRESH_TOKEN);
    await this.storage.delete(TOKEN_KEYS.TOKEN_META);
  }

  private async getStoredTokenMeta(): Promise<VrtTokens | null> {
    const raw = await this.storage.get(TOKEN_KEYS.TOKEN_META);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as VrtTokens;
    } catch {
      return null;
    }
  }

  // ─── Private: JWT helpers ───────────────────────────────

  private isTokenExpired(expiresAt: number, leewaySeconds: number): boolean {
    const now = Math.floor(Date.now() / 1000);
    return now + leewaySeconds >= expiresAt;
  }

  private decodeJwt(token: string): Record<string, unknown> | null {
    try {
      const parts = token.split(".");
      if (parts.length !== 3) return null;
      const payload = parts[1]!;
      const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
      return JSON.parse(decoded);
    } catch {
      return null;
    }
  }
}
