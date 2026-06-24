# Feature Specification: Thuis Web Downloader

**Feature Branch**: `002-thuis-web-downloader`

**Created**: 2026-06-22

**Status**: Draft

**Input**: SPEC.md v0.2.0 sections 1–7, 11–14, 17–21

---

## User Scenarios & Testing

### User Story 1 — VRT MAX Login with Token Management (Priority: P1)

As a user, I want to log in to my VRT MAX account so that the app can access episode metadata and stream URLs.

**Why this priority**: Without authentication, no protected content can be accessed. Every other story depends on this.

**Independent Test**: Can be fully tested with mocked HTTP (nock) — verify that `VrtAuthService.login()`:
1. Calls GET /sso/login to obtain SESSION + OIDCXSRF cookies
2. POSTs credentials to /perform_login with correct Oidcxsrf header
3. Follows redirectUrl to extract access/video/refresh tokens from Set-Cookie headers
4. Returns typed VrtTokens with all tokens and expiry
5. Throws InvalidCredentialsError on wrong email/password
6. Throws TokenAcquisitionError when redirect doesn't set expected cookies

**Acceptance Scenarios**:

1. **Given** valid VRT MAX credentials, **When** login() is called, **Then** VrtTokens are returned containing accessToken, videoToken, and refreshToken.
2. **Given** invalid credentials, **When** login() is called, **Then** InvalidCredentialsError is thrown.
3. **Given** a network failure during /sso/login, **When** login() is called, **Then** a network error is thrown.
4. **Given** stored non-expired tokens, **When** getAccessToken() is called, **Then** the cached token is returned without re-logging.
5. **Given** tokens within 5 minutes of expiry, **When** getAccessToken() is called, **Then** refreshTokens() is triggered automatically.
6. **Given** an expired refresh token, **When** getAccessToken() is called, **Then** AuthenticationError is thrown — user must re-login.

---

### User Story 2 — Episode Metadata Fetching (Priority: P1)

As a user, I want to provide a VRT MAX episode URL and receive structured episode metadata so that I can see what content is available.

**Why this priority**: Episode metadata (title, season, description, streamId) is required before any download or playback can happen.

**Independent Test**: Can be tested with mocked GraphQL responses — verify that `VrtEpisodeService.getEpisode()`:
1. Sends the VideoPage GraphQL query with the URL path as pageId
2. Parses the response into a typed EpisodeDetail object
3. Uses the public endpoint (/graphql/public/v1) when no auth token exists
4. Automatically refreshes the auth token on 401 and retries

**Acceptance Scenarios**:

1. **Given** a valid VRT MAX episode URL, **When** getEpisode() is called, **Then** an EpisodeDetail is returned with title, season, episode, description, and streamId.
2. **Given** a URL for an unavailable episode, **When** getEpisode() is called, **Then** EpisodeUnavailableError is thrown.
3. **Given** an expired access token during the request, **When** getEpisode() is called, **Then** the token is refreshed and the request retried automatically.

---

### User Story 3 — HLS Stream Resolution (Priority: P1)

As a user, I want to resolve an episode's streamId into a downloadable HLS URL so that I can watch or download the content.

**Why this priority**: Without stream resolution, no actual video content can be accessed. This is the bridge between metadata and media.

**Independent Test**: Can be tested with mocked vualto API — verify that:
1. `resolveStream()` calls /v2/tokens with video token + signed playerInfo JWT
2. Uses the returned vrtPlayerToken to call /v2/videos/{streamId}
3. Extracts the HLS URL from targetUrls
4. Throws DrmError when drm=true
5. Throws GeoBlockedError for geo-restricted error codes

**Acceptance Scenarios**:

1. **Given** a valid streamId, **When** resolveStream() is called, **Then** a StreamData object is returned containing an HLS URL.
2. **Given** DRM-protected content, **When** resolveStream() is called, **Then** DrmError is thrown.
3. **Given** geo-restricted content, **When** resolveStream() is called, **Then** GeoBlockedError is thrown.
4. **Given** content requiring login, **When** resolveStream() is called without valid tokens, **Then** EpisodeUnavailableError is thrown.

---

### User Story 4 — FFmpeg Download (Priority: P2)

As a user, I want to download an HLS stream to a local MP4 file so that I can watch it offline.

**Why this priority**: Download is the core feature of the app, but requires the previous 3 stories to be complete first.

**Independent Test**: Can be tested with a synthetic HLS stream on localhost or by verifying FFmpeg argument construction.

**Acceptance Scenarios**:

1. **Given** an HLS URL, **When** download() is called with an output path, **Then** FFmpeg is spawned with correct arguments.
2. **Given** a running download, **When** progress events are emitted, **Then** they contain bytes downloaded, speed, and ETA.
3. **Given** a network failure during download, **When** FFmpeg exits with non-zero code, **Then** DownloadError is thrown.

---

### User Story 5 — Download Queue with Persistence (Priority: P2)

As a user, I want to queue multiple episode downloads and see their progress so that I can batch-download content.

**Why this priority**: Batch downloading is a key differentiator from manual single-episode download.

**Independent Test**: Test queue state machine in isolation without actual downloads.

**Acceptance Scenarios**:

1. **Given** multiple episodes, **When** added to the queue, **Then** they are processed sequentially (or in parallel based on config).
2. **Given** a queue with paused items, **When** resume() is called, **Then** download resumes from where it stopped.
3. **Given** completed downloads, **When** the queue view is opened, **Then** completed items show file size and duration.

---

### Edge Cases

- What happens when the user has no network during login? → Network error, retry button.
- What happens when the refresh token is expired and credentials are not stored? → Prompt for re-login.
- What happens when a VRT API endpoint changes (403 becomes 404)? → Error thrown, user sees "Could not connect".
- What happens when FFmpeg is not installed? → DownloadError with clear instruction to install ffmpeg.
- What happens when disk is full during download? → DownloadError, partial file cleaned up.
- What happens when the same episode is queued twice? → Second attempt is ignored (dedup by episodeId).
- What happens when a JWT signing key changes? → Player token request fails → logged as error, user sees "Stream temporarily unavailable".

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST authenticate with VRT MAX using email + password credentials via the OIDC flow.
- **FR-002**: System MUST automatically refresh access and video tokens when they are within 5 minutes of expiry.
- **FR-003**: System MUST cache access and video tokens in memory to avoid re-login on every request.
- **FR-004**: System MUST support token refresh even when the app is restarted (persist refresh token).
- **FR-005**: System MUST fetch episode metadata from VRT MAX's GraphQL API using the VideoPage query.
- **FR-006**: System MUST fall back to the public GraphQL endpoint when no access token is available.
- **FR-007**: System MUST resolve an episode's streamId to an HLS manifest URL via the vualto media API.
- **FR-008**: System MUST construct a valid JWT playerInfo for the vualto token request using known signing keys.
- **FR-009**: System MUST detect DRM-protected content and refuse to download, reporting a clear error.
- **FR-010**: System MUST detect geo-restricted content and report a clear error.
- **FR-011**: System MUST download HLS streams via FFmpeg with copy-codec (no re-encode).
- **FR-012**: System MUST report download progress (bytes, speed, ETA) via events/callbacks.
- **FR-013**: System MUST support pausing and resuming downloads (via FFmpeg segment caching or temp files).
- **FR-014**: System MUST persist download queue state across app restarts (IndexedDB/localStorage for web, JSON for Electron).
- **FR-015**: System MUST deduplicate download queue entries by episodeId.
- **FR-016**: System MUST display all user-facing errors in Dutch.
- **FR-017**: System MUST require `x-vrt-client-name: WEB` and `x-vrt-client-version` headers on all GraphQL requests.

### Key Entities

- **VrtTokens**: Access token, video token, refresh token with expiry timestamps. Stored in-memory; refresh token persisted for session recovery.
- **EpisodeDetail**: Full episode metadata including streamId. Fetched from GraphQL, validated via Zod.
- **StreamData**: HLS/manifest URLs, DRM flag, error codes. Resolved from vualto media API.
- **DownloadJob**: Queue item with status (pending/downloading/paused/completed/failed), progress, file path. Persisted across restarts.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Login completes in under 5 seconds on a standard broadband connection (excluding page load).
- **SC-002**: Episode metadata fetch completes in under 3 seconds.
- **SC-003**: Stream resolution completes in under 2 seconds.
- **SC-004**: Token refresh takes under 1 second and happens transparently to the user.
- **SC-005**: A 30-minute episode downloads in under 10 minutes on a 10 Mbps connection.
- **SC-006**: Download progress updates are emitted at least every 2 seconds.
- **SC-007**: All error conditions (wrong password, DRM, geo-block, network failure) show a Dutch error message with a retry option.

---

## Assumptions

- FFmpeg is installed on the user's system and available in PATH (Electron) or available via a server proxy (web).
- JWK signing keys for playerInfo are stable and match those documented in yt-dlp. If they change, a maintenance update is needed.
- VRT MAX's GraphQL API schema is stable. Breaking changes would require a spec update.
- The vualto media aggregator API endpoint URL pattern remains stable.
- Users have a valid VRT MAX account with email/password login (not Google/Facebook SSO).
- The web app cannot run FFmpeg directly — downloads will only work in Electron or via a proxy server.
- For the web app MVP, download is limited to Electron; web users see the stream URL and can manually download.

---

## Notes

- The web app uses `nock` for all HTTP mocking in unit tests. No real API calls during unit tests.
- Integration tests use real credentials from `VRT_USERNAME` / `VRT_PASSWORD` environment variables and are excluded from CI.
- The existing `@thuis/core` GraphQL client needs refactoring to support the VideoPage query (currently uses PaginatedTileList approach).
- Player info JWT uses a known HMAC-SHA256 key extracted from VRT's player scripts. This may change without notice.
