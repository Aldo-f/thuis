# VRT MAX Download — Technical Analysis

> Analysis date: 2026-06-22
> Sources: yt-dlp vrt.py (master), Kodi plugin.video.vrt.nu, Aldo-f/thuis (Python v3), existing @thuis/core codebase

---

## Table of Contents

1. [The Goal](#1-the-goal)
2. [Architecture Overview](#2-architecture-overview)
3. [VRT MAX Authentication Flow (Detailed)](#3-vrt-max-authentication-flow-detailed)
4. [Episode Metadata Flow](#4-episode-metadata-flow)
5. [Stream URL & Download Flow](#5-stream-url--download-flow)
6. [Required HTTP APIs Summary](#6-required-http-apis-summary)
7. [JWT Player Token](#7-jwt-player-token)
8. [Error Conditions](#8-error-conditions)
9. [TDD Test Strategy](#9-tdd-test-strategy)
10. [Implementation Plan](#10-implementation-plan)
11. [Existing Codebase Integration](#11-existing-codebase-integration)

---

## 1. The Goal

Create a TDD test (and then implementation) in `@thuis/core` that:

1. Logs into VRT MAX using email + password
2. Fetches the latest episode metadata from the Thuis series (season 31)
3. Resolves the HLS stream URL
4. Downloads the episode via FFmpeg

The entry URL: `https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/`

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Test / Client                      │
├─────────────────────────────────────────────────────┤
│  1. VrtAuthService          │   2. VrtEpisodeService │
│     - login()               │     - getEpisode()     │
│     - getAccessToken()      │     - resolveStream()  │
│     - getVideoToken()       │                        │
│     - refreshTokens()       │                        │
├─────────────────────────────┴───────────────────────┤
│  3. StreamDownloader                                 │
│     - downloadHlsStream()                            │
│     - uses FFmpeg process                            │
└─────────────────────────────────────────────────────┘
         │                           │
         ▼                           ▼
┌──────────────────┐    ┌──────────────────────────┐
│  login.vrt.be    │    │  vrtnu-api.graphql/v1    │
│  perform_login   │    │  media-services-public   │
│  sso/login       │    │  vualto-video-aggregator │
│  sso/refresh     │    │                          │
└──────────────────┘    └──────────────────────────┘
```

---

## 3. VRT MAX Authentication Flow (Detailed)

### 3.1 Flow Diagram

```
  Client                    VRT SSO                     VRT Login            VRT Redirect
    │                          │                          │                     │
    │── GET /vrtmax/sso/login ──│                          │                     │
    │◄── Set-Cookie: SESSION ───│                          │                     │
    │◄── Set-Cookie: OIDCXSRF ──│                          │                     │
    │                          │                          │                     │
    │── POST /perform_login ────│─────────────────────────►│                     │
    │   Headers:               │                          │                     │
    │     Content-Type: json   │                          │                     │
    │     Oidcxsrf: <value>    │                          │                     │
    │   Body: {                │                          │                     │
    │     clientId: vrtnu-site,│                          │                     │
    │     loginID: <email>,    │                          │                     │
    │     password: <pass>     │                          │                     │
    │   }                      │                          │                     │
    │◄── 403 (expected) ───────│──────────────────────────│                     │
    │   { redirectUrl: "..." } │                          │                     │
    │                          │                          │                     │
    │── GET <redirectUrl> ─────│──────────────────────────│────────────────────►│
    │◄── Set-Cookie: ──────────│──────────────────────────│────────────────────│
    │   vrtnu-site_profile_at  │                          │                     │
    │   vrtnu-site_profile_vt  │                          │                     │
    │   vrtnu-site_profile_rt  │                          │                     │
    │                          │                          │                     │
```

### 3.2 Step-by-Step

#### Step A: Get Session Cookies

```
GET https://www.vrt.be/vrtmax/sso/login
```

No specific headers needed (standard browser headers suffice).

**Response**: Redirect (302) to login.vrt.be authorize page, with `Set-Cookie` headers:
- `SESSION` (domain: .login.vrt.be)
- `OIDCXSRF` (domain: .login.vrt.be)

> **Note**: The Kodi add-on uses `https://www.vrt.be/vrtnu/sso/login?scope=openid,mid` instead. Both seem to work.

#### Step B: Perform Login

```
POST https://login.vrt.be/perform_login
Headers:
  Content-Type: application/json
  Oidcxsrf: <OIDCXSRF cookie value>
Body:
  {
    "clientId": "vrtnu-site",
    "loginID": "<email>",
    "password": "<password>"
  }
```

**Response**: HTTP 403 (this is expected by yt-dlp, not an error!)
```json
{
  "redirectUrl": "https://www.vrt.be/vrtmax/sso/callback?code=...&state=...",
  "errorCode": 0
}
```

On failure:
```json
{
  "errorCode": "some_code",
  "errorMessage": "invalid loginID or password"
}
```

#### Step C: Get Tokens via Redirect

```
GET <redirectUrl from Step B>
Follow redirects (or handle manually).
```

**Response**: Sets cookies:
| Cookie Name | Domain | Path | Purpose |
|---|---|---|---|
| `vrtnu-site_profile_at` | `.www.vrt.be` | `/` | Access token (JWT) |
| `vrtnu-site_profile_vt` | `.www.vrt.be` | `/` | Video token (JWT) |
| `vrtnu-site_profile_rt` | `.www.vrt.be` | `/vrtmax/sso` | Refresh token (JWT) |

All three are JWT tokens. The access token (`_at`) is used in GraphQL API Authorization header.

#### Step D: Refresh Tokens

```
GET https://www.vrt.be/vrtmax/sso/refresh
Cookie: vrtnu-site_profile_rt=<refresh_token>
```

Response sets new `_at`, `_vt`, `_rt` cookies.
Returns HTTP 401 if refresh token is expired — then you must re-login.

#### Step E: Token Check

JWT tokens have an `exp` claim. yt-dlp checks:
```
token_exp = jwt_decode(token)['exp']
if token_exp - time.time() < 300:  # 5 min buffer
    # needs refresh
```

---

## 4. Episode Metadata Flow

### 4.1 GraphQL Query

```
POST https://www.vrt.be/vrtnu-api/graphql/v1
Headers:
  Authorization: Bearer <access_token>
  Content-Type: application/json
  x-vrt-client-name: WEB
  x-vrt-client-version: 1.5.9
  x-vrt-zone: default
Body:
{
  "operationName": "VideoPage",
  "query": "query VideoPage($pageId: ID!) {
    page(id: $pageId) {
      ... on EpisodePage {
        episode {
          ageRaw description durationRaw episodeNumberRaw id name onTimeRaw
          program { title }
          season { id titleRaw }
          title brand
        }
        ldjson
        player {
          image { templateUrl }
          modes { streamId }
        }
      }
    }
  }",
  "variables": {
    "pageId": "/vrtmax/a-z/thuis/31/thuis-s31a6105/"
  }
}
```

**Note**: If no access token is available, use the public endpoint:
```
POST https://www.vrt.be/vrtnu-api/graphql/public/v1
```
(omit `Authorization` header, but still include `x-vrt-client-*` headers)

### 4.2 Key Data from Response

```json
{
  "data": {
    "page": {
      "episode": {
        "id": "1740392401937",
        "title": "Aflevering 105",
        "name": "Thuis - Seizoen 31 - Aflevering 105",
        "description": "...",
        "durationRaw": "PT30M",
        "episodeNumberRaw": 105,
        "onTimeRaw": "2025-03-03T20:00:00+01:00",
        "ageRaw": "ALL",
        "program": { "title": "Thuis" },
        "season": { "id": "1739450401467", "titleRaw": "31" },
        "brand": "een"
      },
      "player": {
        "image": { "templateUrl": "..." },
        "modes": [
          { "streamId": "pbs-pub-...$vid-..." }
        ]
      }
    }
  }
}
```

`streamId` is the critical value — it's the video asset identifier used to fetch the actual stream.

---

## 5. Stream URL & Download Flow

### 5.1 Get vrtPlayerToken (needed for stream access)

```
POST https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v2/tokens
Headers:
  Content-Type: application/json
Body:
{
  "identityToken": "<video_token (vrtnu-site_profile_vt)>",
  "playerInfo": "<JWT signed player info>"
}
```

**Response**:
```json
{
  "vrtPlayerToken": "b1@3a1b2c3d..."
}
```

### 5.2 Get Stream Data

```
GET https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v2/videos/<video_id>?client=vrtnu-web@PROD&vrtPlayerToken=<player_token>
```

This URL redirects to:
```
https://media-services-public.vrt.be/media-aggregator/v2/media-items/<publication_id>$<video_id>?client=vrtnu-web@PROD&vrtPlayerToken=<player_token>
```

**Response** (success):
```json
{
  "title": "Aflevering 105",
  "duration": 1800000,
  "posterImageUrl": "...",
  "targetUrls": [
    {
      "type": "hls",
      "url": "https://...master.m3u8?..."
    },
    {
      "type": "hls_aes",
      "url": "https://...master.m3u8?...
    }
  ],
  "drm": false
}
```

**Error codes** from streaming API:

| Code | Meaning |
|---|---|
| `CONTENT_AVAILABLE_ONLY_FOR_BE_RESIDENTS` | Geo-blocked |
| `CONTENT_AVAILABLE_ONLY_IN_BE` | Geo-blocked |
| `CONTENT_UNAVAILABLE_VIA_PROXY` | VPN/proxy detected |
| `CONTENT_IS_AGE_RESTRICTED` | Age-restricted, login required |
| `CONTENT_REQUIRES_AUTHENTICATION` | Login required |
| `CONTENT_AVAILABLE_ONLY_FOR_BE_RESIDENTS_AND_EXPATS` | Geo + login |

### 5.3 Download HLS Stream

Use FFmpeg to download:
```bash
ffmpeg -i "<hls_url>" \
  -headers "User-Agent: <ua>\r\nReferer: https://www.vrt.be/\r\nCookie: <cookies>\r\n" \
  -c copy -y output.mp4
```

---

## 6. Required HTTP APIs Summary

| # | Method | URL | Purpose | Auth |
|---|---|---|---|---|
| 1 | GET | `https://www.vrt.be/vrtmax/sso/login` | Get session cookies (SESSION, OIDCXSRF) | None |
| 2 | POST | `https://login.vrt.be/perform_login` | Login with email + password | OIDCXSRF header |
| 3 | GET | `<redirectUrl from #2>` | Exchange auth code for tokens | Session cookies |
| 4 | GET | `https://www.vrt.be/vrtmax/sso/refresh` | Refresh tokens | `_rt` cookie |
| 5 | POST | `https://www.vrt.be/vrtnu-api/graphql/v1` | Fetch episode metadata | Bearer `_at` |
| 6 | POST | `https://...vualto-video-aggregator-web/.../tokens` | Get vrtPlayerToken | `_vt` in body |
| 7 | GET | `https://...vualto-video-aggregator-web/.../videos/{id}` | Get stream info | `vrtPlayerToken` |

---

## 7. JWT Player Token

The player token request needs a JWT-signed `playerInfo`. The signing key can be extracted from VRT's player scripts (yt-dlp uses a known key).

### Current known values (from yt-dlp source — may change):

```typescript
const JWT_KEY_ID = '0-0Fp51UZykfaiCJrfTE3+oMI8zvDteYfPtR+2n1R+z8w=';
const JWT_SIGNING_KEY = 'b5f500d55cb44715107249ccd8a5c0136cfb2788dbb71b90a4f142423bacaf38'; // dev key

const PLAYER_INFO = {
  platform: 'desktop',
  app: { type: 'browser', name: 'Chrome' },
  device: 'undefined (undefined)',
  os: { name: 'Windows', version: '10' },
  player: { name: 'VRT web player', version: '5.1.1-prod-2025-02-14T08:44:16' },
};
```

### JWT Construction

1. Header: `{ alg: 'HS256', kid: <keyId> }`
2. Payload: `{ exp: <now+900>, ...PLAYER_INFO }`
3. Sign with HMAC-SHA256 using the signing key

The JWT is passed as the `playerInfo` field in the vrtPlayerToken request.

---

## 8. Error Conditions

### Login Errors
| Error | Cause | Handling |
|---|---|---|
| `errorCode` != 0 in login response | Wrong credentials | Raise `AuthenticationError` |
| `errorMessage: "invalid loginID or password"` | Wrong email/pw | Raise `InvalidCredentialsError` |
| HTTP 403 without expected JSON | API change / block | Raise `LoginFailedError` |
| OIDCXSRF cookie missing | Browser/session issue | Retry Step A |

### Token Errors
| Condition | Cause | Handling |
|---|---|---|
| `_at` cookie missing after auth | Auth flow failed | Raise `TokenAcquisitionError` |
| `_vt` cookie missing after auth | Auth flow failed | Raise `TokenAcquisitionError` |
| `_rt` cookie missing after auth | Auth flow failed | Raise `TokenAcquisitionError` |
| JWT `exp` claim < now | Token expired | Refresh automatically |
| Refresh returns 401 | Session expired | Re-login |

### GraphQL Errors
| Condition | Cause | Handling |
|---|---|---|
| HTTP 401 | Token expired | Refresh, retry |
| HTTP 400 (missing x-vrt-client-name header) | Missing required header | Add header |
| No `player.modes[0].streamId` | Episode not available / geo-blocked | Raise `EpisodeUnavailableError` |

### Stream Errors
| Error Code | Handling |
|---|---|
| `CONTENT_REQUIRES_AUTHENTICATION` | `raise_login_required()` |
| `CONTENT_AVAILABLE_ONLY_FOR_BE_RESIDENTS` | `raise_geo_restricted()` |
| `CONTENT_IS_AGE_RESTRICTED` | `raise_login_required()` |
| `drm: true` | `report_drm()` — cannot download DRM content |
| HTTP 404 on stream fetch | Invalid or expired player token |

---

## 9. TDD Test Strategy

### 9.1 Test Layers

Three test layers, tested independently:

#### Layer 1: VrtAuthService (login + token management)

| Test | What It Verifies |
|---|---|
| `login() - gets session cookies` | Calls GET /vrtmax/sso/login, stores SESSION + OIDCXSRF |
| `login() - performs credential login` | POST to /perform_login with correct headers + body |
| `login() - handles wrong credentials` | errorCode != 0 → throws `InvalidCredentialsError` |
| `login() - extracts tokens from redirect` | Parses Set-Cookie for _at, _vt, _rt |
| `login() - missing token raises error` | Partial Set-Cookie → throws `TokenAcquisitionError` |
| `refreshTokens() - refreshes via _rt cookie` | GET /sso/refresh with _rt cookie |
| `refreshTokens() - expired refresh re-logs in` | 401 → calls login() |
| `getAccessToken() - caches and reuses` | Second call doesn't re-auth |
| `getAccessToken() - expired token refreshes` | JWT exp < now+300 → calls refresh |
| `isTokenExpired()` | Correctly checks JWT exp claim |

#### Layer 2: VrtEpisodeService (metadata)

| Test | What It Verifies |
|---|---|
| `getEpisode(url) - queries GraphQL` | POST /graphql/v1 with correct query body |
| `getEpisode(url) - parses response` | Returns typed EpisodeDetail object |
| `getEpisode(url) - uses public endpoint if no token` | POST /graphql/public/v1 without Authorization |
| `getEpisode(url) - 401 triggers refresh` | Calls VrtAuthService.refreshTokens(), retries |
| `getEpisode(url) - extracts streamId` | From player.modes[0].streamId |
| `resolveStream(streamId) - gets player token` | POST /vualto/.../tokens with playerInfo JWT |
| `resolveStream(streamId) - gets HLS URL` | GET /vualto/.../videos/{id}, extracts hls targetUrl |
| `resolveStream(streamId) - drm detection` | drm=true → throws `DrmError` |
| `resolveStream(streamId) - geo error` | code=CONTENT_... → throws `GeoBlockedError` |

#### Layer 3: Integration Test (requires credentials + network)

| Test | What It Verifies |
|---|---|
| `full flow - login + get latest thuis episode` | End-to-end: login → metadata → stream URL |
| `download with ffmpeg` | Downloads at least first bytes of HLS stream |

### 9.2 Mocking Strategy

For unit tests, use `nock` (or similar) to mock HTTP:

```typescript
import nock from 'nock';

// Mock login flow
nock('https://www.vrt.be')
  .get('/vrtmax/sso/login')
  .reply(302, '', {
    'Set-Cookie': [
      'SESSION=abc123; Domain=.login.vrt.be; Path=/; HttpOnly',
      'OIDCXSRF=xyz789; Domain=.login.vrt.be; Path=/; HttpOnly',
    ],
    Location: 'https://login.vrt.be/authorize?...'
  });

nock('https://login.vrt.be')
  .post('/perform_login', body => body.loginID === 'test@example.com')
  .reply(403, {
    redirectUrl: 'https://www.vrt.be/vrtmax/sso/callback?code=abc&state=def',
    errorCode: 0
  });

nock('https://www.vrt.be')
  .get('/vrtmax/sso/callback')
  .query(true)
  .reply(302, '', {
    'Set-Cookie': [
      'vrtnu-site_profile_at=eyJhbG...; Domain=.www.vrt.be; Path=/',
      'vrtnu-site_profile_vt=eyJ2a...; Domain=.www.vrt.be; Path=/',
      'vrtnu-site_profile_rt=eyJyZ...; Domain=.www.vrt.be; Path=/vrtmax/sso',
    ],
    Location: 'https://www.vrt.be/vrtmax/'
  });
```

For integration tests, use real credentials (from environment variables).

### 9.3 Test File Structure

```
packages/core/src/
  __tests__/
    auth/
      VrtAuthService.test.ts     # Unit tests for auth
    episode/
      VrtEpisodeService.test.ts  # Unit tests for episode fetching
    download/
      StreamResolver.test.ts     # Unit tests for stream resolution
    integration/
      thuis-download.test.ts     # Integration test (real calls)
  auth/
    VrtAuthService.ts            # Auth implementation
    types.ts                     # Auth types
  episode/
    VrtEpisodeService.ts         # Episode metadata implementation
    types.ts                     # Episode response types
  download/
    StreamResolver.ts            # Stream URL resolution
    Downloader.ts                # FFmpeg download
    types.ts                     # Stream types
```

---

## 10. Implementation Plan

### Phase A: Types & Interfaces (Zod schemas)

Define Zod schemas for:
- `VrtCredentials` (email, password)
- `VrtTokens` (accessToken, videoToken, refreshToken, expiresAt)
- `VrtLoginResponse` (redirectUrl, errorCode, errorMessage)
- `VrtEpisodeGraphQlResponse` (full GraphQL response shape)
- `VrtStreamData` (targetUrls, drm, code, title, duration)
- `VrtPlayerTokenResponse` (vrtPlayerToken)
- `VrtJwtPlayerInfo` (for player token JWT signing)

### Phase B: VrtAuthService

Class `VrtAuthService`:
```typescript
class VrtAuthService {
  constructor(private httpClient: HttpClient) {}
  
  async login(credentials: VrtCredentials): Promise<VrtTokens>
  async refreshTokens(): Promise<VrtTokens>
  async getAccessToken(): Promise<string>  // auto-refreshes if needed
  async getVideoToken(): Promise<string>   // auto-refreshes if needed
  
  private async fetchSessionCookies(): Promise<void>
  private async performLogin(credentials: VrtCredentials): Promise<string>
  private async extractTokensFromRedirect(redirectUrl: string): Promise<VrtTokens>
  private isTokenExpired(token: string): boolean
  private decodeJwt(token: string): any
}
```

### Phase C: VrtEpisodeService

Class `VrtEpisodeService`:
```typescript
class VrtEpisodeService {
  constructor(
    private authService: VrtAuthService,
    private httpClient: HttpClient
  ) {}
  
  async getEpisode(url: string): Promise<EpisodeDetail>
  async resolveStream(streamId: string): Promise<StreamData>
  
  private async graphQlQuery(query: string, variables: object): Promise<any>
  private async getVrtPlayerToken(videoToken: string): Promise<string>
  private async fetchStreamData(videoId: string, playerToken: string): Promise<StreamData>
}
```

### Phase D: StreamDownloader

Class `StreamDownloader`:
```typescript
class StreamDownloader {
  async downloadHls(hlsUrl: string, outputPath: string, options?: DownloadOptions): Promise<DownloadResult>
  
  private async spawnFfmpeg(...): Promise<void>
  private parseProgress(line: string): ProgressInfo | null
}
```

### Phase E: The TDD Test

```typescript
// packages/core/src/__tests__/integration/thuis-download.test.ts
describe('Thuis Download - Integration', () => {
  const credentials = {
    email: process.env.VRT_USERNAME!,
    password: process.env.VRT_PASSWORD!,
  };
  const episodeUrl = 'https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/';
  
  beforeAll(() => {
    if (!credentials.email || !credentials.password) {
      throw new Error('VRT_USERNAME and VRT_PASSWORD env vars required');
    }
  });

  it('logs in, fetches the latest thuis episode, resolves HLS URL, and downloads it', async () => {
    // 1. Login
    const auth = new VrtAuthService(new HttpClient());
    const tokens = await auth.login(credentials);
    expect(tokens.accessToken).toBeDefined();
    expect(tokens.videoToken).toBeDefined();
    
    // 2. Fetch episode metadata
    const episodeService = new VrtEpisodeService(auth, new HttpClient());
    const episode = await episodeService.getEpisode(episodeUrl);
    expect(episode.title).toBeDefined();
    expect(episode.videoId).toBeDefined();
    expect(episode.streamId).toBeDefined();
    
    // 3. Resolve stream URL
    const stream = await episodeService.resolveStream(episode.streamId!);
    expect(stream.hlsUrl).toMatch(/\.m3u8/);
    expect(stream.drm).toBe(false);
    
    // 4. Download first KB to verify accessibility
    const downloader = new StreamDownloader();
    const result = await downloader.downloadRange(stream.hlsUrl, 0, 1024 * 100);
    expect(result.success).toBe(true);
  }, 60000); // 60s timeout for integration test
});
```

---

## 11. Existing Codebase Integration

### What exists in `@thuis/core` today

| File | What It Has |
|---|---|
| `src/graphql/client.ts` | `GraphQLClient.createClient(baseUrl, token)` — has `searchEpisodes()` and `getEpisodeByUrl()` |
| `src/graphql/queries.ts` | Search + episode queries (but uses `PaginatedTileList`, not `VideoPage`) |
| `src/graphql/types.ts` | Zod schemas for tile responses |
| `src/types/episode.ts` | `EpisodeSchema`, `EpisodeDetailSchema` |
| `src/types/download.ts` | `DownloadJobSchema`, `DownloadStatusSchema` |
| `src/types/index.ts` | `SearchResultSchema` |

### What needs to change

1. **`src/graphql/client.ts`** — The existing `createClient` requires a `token` parameter but there's no way to acquire one. Need to inject `VrtAuthService` or add a `login()` method.

2. **`src/graphql/queries.ts`** — Need to add the `VideoPage` GraphQL query (the current `EPISODE_BY_URL_QUERY` uses a different query pattern).

3. **`src/graphql/types.ts`** — Need VideoPage response Zod schemas.

4. **`src/types/episode.ts`** — Might need updates to match the real API response.

5. **New files needed**:
   - `src/auth/VrtAuthService.ts`
   - `src/auth/types.ts`
   - `src/download/StreamResolver.ts`
   - `src/download/Downloader.ts`
   - `src/download/types.ts`
   - `src/__tests__/auth/VrtAuthService.test.ts`
   - `src/__tests__/episode/VrtEpisodeService.test.ts`
   - `src/__tests__/download/StreamResolver.test.ts`
   - `src/__tests__/integration/thuis-download.test.ts`

---

## Quick Reference: Cookie Domain Mapping

```
Cookie                     Domain             Path
─────────────────────────────────────────────────────────
SESSION                    .login.vrt.be      /
OIDCXSRF                   .login.vrt.be      /
vrtnu-site_profile_at      .www.vrt.be        /
vrtnu-site_profile_vt      .www.vrt.be        /
vrtnu-site_profile_rt      .www.vrt.be        /vrtmax/sso
```

---

## Appendix: Common Gotchas

1. **`perform_login` returns 403 on success!** This is not an error. yt-dlp uses `expected_status=403`.

2. **Cookies are scoped by domain.** `SESSION`/`OIDCXSRF` are on `login.vrt.be`, while tokens are on `.www.vrt.be`.

3. **The GraphQL requires specific headers.** Without `x-vrt-client-name: WEB`, the API returns 400.

4. **Two VRT GraphQL endpoints exist:** authenticated (`/v1`) and public (`/public/v1`). Without a token, use the public one.

5. **The `pageId` variable in the GraphQL query is a URL path**, not a component ID. e.g. `/vrtmax/a-z/thuis/31/thuis-s31a6105/`.

6. **Player info JWT key may change.** The keys in yt-dlp are from reverse-engineering VRT's player scripts. If they stop working, the signing key needs to be re-extracted.

7. **Player tokens (`vrtPlayerToken`) start with `b1` for authorized tokens.** (Unauthorized ones start with `b0` and won't work for on-demand content.)

8. **The streaming API version matters.** v2 is the current version. v1 was the old one.
