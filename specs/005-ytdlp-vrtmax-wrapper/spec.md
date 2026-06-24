# Feature Specification: yt-dlp VRT MAX Integration

**Feature Directory**: `specs/005-ytdlp-vrtmax-wrapper/`

**Created**: 2026-06-24

**Status**: Draft

**Input**: Implement a VRT MAX front-end wrapper built on the official yt-dlp release (login, episode list, HLS playback, and download) inside the existing thuis monorepo.

---

## User Scenarios & Testing

### User Story 1 — Login via yt-dlp Cookie Extraction (Priority: P1)

As a user, I want to log in to VRT MAX using my email and password, with yt-dlp handling the authentication and cookie storage, so that I can access age-restricted and subscriber content without managing tokens manually.

**Why this priority**: Login is the prerequisite for all other functionality. The existing custom VRT auth service works, but yt-dlp's cookie-based login is more resilient to API changes.

**Independent Test**: Can be tested by providing valid VRT MAX credentials and verifying that yt-dlp produces a valid cookies.txt file after authentication. Mock the yt-dlp binary for automated tests.

**Acceptance Scenarios**:

1. **Given** valid VRT MAX email and password, **When** the user initiates login via yt-dlp, **Then** cookies are extracted and stored securely in the credential vault.
2. **Given** invalid VRT MAX credentials, **When** the user attempts login via yt-dlp, **Then** a clear Dutch error message is displayed and no cookies are stored.
3. **Given** expired cookies, **When** the user tries to access protected content, **Then** the system automatically re-authenticates using stored credentials or prompts for a new login.

---

### User Story 2 — Episode Metadata via yt-dlp (Priority: P1)

As a user, I want to retrieve episode details (title, description, season, episode number, thumbnail, duration) from VRT MAX via yt-dlp, so that I can browse and select content to watch or download.

**Why this priority**: Episode metadata is the foundation for the browse-and-select experience. yt-dlp's `--dump-json` flag provides richer metadata than the current custom GraphQL queries.

**Independent Test**: Can be tested with a mock URL and simulated yt-dlp JSON output. Verify that the output is correctly parsed into the existing EpisodeDetail type.

**Acceptance Scenarios**:

1. **Given** a valid VRT MAX episode URL, **When** the user opens the episode page, **Then** the title, description, season/episode numbers, and duration are displayed.
2. **Given** a VRT MAX series URL, **When** the user browses the series, **Then** all available episodes are listed with their metadata.
3. **Given** an invalid or non-existent URL, **When** the user requests metadata, **Then** a Dutch error message is shown without crashing.

---

### User Story 3 — HLS Stream Resolution via yt-dlp (Priority: P1)

As a user, I want to watch VRT MAX content via HLS streaming, with yt-dlp resolving the stream URL, so that I can play videos instantly without downloading them first.

**Why this priority**: HLS playback is the core viewing experience. yt-dlp handles the token management and stream format negotiation that the current custom StreamResolver does manually.

**Independent Test**: Can be tested by running yt-dlp with `-g` on a known VRT MAX URL and verifying the output is a valid HLS manifest URL. Mock the binary for automated unit tests.

**Acceptance Scenarios**:

1. **Given** a VRT MAX episode with an available HLS stream, **When** the user opens the episode page, **Then** the HLS stream URL is resolved and playback begins.
2. **Given** an episode protected by DRM, **When** yt-dlp resolves the stream, **Then** the DRM status is detected and the user sees a Dutch message that the video is protected.
3. **Given** geographic restrictions, **When** yt-dlp resolves the stream, **Then** the user sees a Dutch message that the content is only available in Belgium.

---

### User Story 4 — Download Episodes via yt-dlp (Priority: P2)

As a user, I want to download VRT MAX episodes for offline viewing, with yt-dlp managing the download process including progress reporting, format selection, and subtitle extraction.

**Why this priority**: Download is a key differentiator from the standard VRT MAX website. yt-dlp's native download capabilities eliminate the need for the current FFmpeg-based segment joining approach.

**Independent Test**: Can be tested by running yt-dlp with a mock video URL and verifying that the download process starts, progresses, and completes. Mock the binary for automated tests.

**Acceptance Scenarios**:

1. **Given** a resolved episode stream, **When** the user clicks "Download", **Then** yt-dlp starts downloading with visible progress (speed, ETA, percentage).
2. **Given** an active download, **When** the user pauses it, **Then** the partial file is saved and can be resumed later.
3. **Given** a completed download, **When** the user views the download queue, **Then** the episode appears as available for offline playback.
4. **Given** multiple episodes selected for download, **When** the user queues them, **Then** they download sequentially with configurable concurrency.

---

### User Story 5 — Series Episode List (Priority: P2)

As a user, I want to view all episodes of a VRT MAX series via yt-dlp, so that I can browse and select episodes without navigating through the VRT MAX website.

**Why this priority**: Series browsing is essential for the "Thuis" use case (the namesake soap opera with many episodes).

**Independent Test**: Can be tested with a mock series URL and simulated yt-dlp playlist JSON output.

**Acceptance Scenarios**:

1. **Given** a VRT MAX series URL, **When** the user views the series page, **Then** all episodes are listed with thumbnails, titles, and air dates.
2. **Given** a series with multiple seasons, **When** the user filters by season, **Then** only episodes from that season are shown.
3. **Given** a series with new episodes, **When** the user checks for updates, **Then** newly available episodes are highlighted.

---

### Edge Cases

- What happens when yt-dlp is not installed or the wrong version is installed?
- How does the system handle yt-dlp producing unexpected output format?
- What happens when the user's internet connection is lost during a download?
- How does the system handle concurrent downloads and system resource limits?
- What happens when the VRT MAX API changes and yt-dlp has not been updated?
- How does the system switch between yt-dlp provider and the existing custom provider?
- What happens when yt-dlp binary crashes or hangs (stale process)?

---

## Requirements

### Functional Requirements

- **FR-001**: The system MUST allow users to log in to VRT MAX via yt-dlp using email and password.
- **FR-002**: The yt-dlp wrapper MUST extract and store authentication cookies in the existing credential vault.
- **FR-003**: The system MUST provide episode metadata from VRT MAX using yt-dlp's `--dump-json` output.
- **FR-004**: The system MUST resolve HLS stream URLs for VRT MAX episodes using yt-dlp's `-g` flag.
- **FR-005**: The system MUST detect and report DRM-protected content to the user in Dutch.
- **FR-006**: The system MUST support downloading VRT MAX episodes via yt-dlp with progress reporting.
- **FR-007**: The yt-dlp wrapper MUST implement the existing `ProviderAdapter` interface.
- **FR-008**: The system MUST gracefully fall back to the existing custom VRT provider if yt-dlp is unavailable.
- **FR-009**: The system MUST show download progress (percentage, speed, ETA) in the UI.
- **FR-010**: Download queue MUST support pause, resume, and cancellation of active downloads.
- **FR-011**: The system MUST validate yt-dlp presence and version at startup.
- **FR-012**: All user-facing messages from the yt-dlp feature MUST be in Dutch.
- **FR-013**: The yt-dlp wrapper MUST use Zod schemas to validate all parsed output.
- **FR-014**: The system MUST NOT crash if yt-dlp produces unexpected output; errors must be caught and reported in Dutch.

### Key Entities

- **YtDlpService**: Core service that manages the yt-dlp binary process lifecycle. Provides methods for login, metadata extraction, stream URL resolution, and download management. Communicates with yt-dlp via CLI subprocess calls.
- **YtDlpProviderAdapter**: Implements the `ProviderAdapter` interface using `YtDlpService` as the backend engine. Registers in `ProviderRegistry` and can be selected by the user as an alternative to the existing custom VRT adapter.
- **DownloadJob**: Represents a single download task tracked in the download queue. Contains URL, file path, progress state, speed, ETA, pause/resume capability, and cancellation support.
- **DownloadManager**: Manages the lifecycle of all active and queued DownloadJobs. Controls concurrency, handles retries, and persists queue state across sessions.
- **CookieStore**: Manages yt-dlp authentication cookies in the credential vault, providing get/set/refresh operations linked to the master password.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can log in to VRT MAX via yt-dlp and access protected content within 30 seconds of entering credentials.
- **SC-002**: Episode metadata is displayed within 5 seconds of navigating to an episode page (with warm cache).
- **SC-003**: HLS playback starts within 10 seconds of opening an episode page (includes stream resolution time).
- **SC-004**: Downloads complete at a speed within 90% of the raw download speed of `curl` or `wget` for the same URL.
- **SC-005**: Download progress updates the UI at least once per second.
- **SC-006**: The system gracefully handles yt-dlp not being installed (falls back to existing custom provider) without crashing.
- **SC-007**: Queue management (pause/resume/cancel) responds within 1 second of user action.

---

## Assumptions

- yt-dlp is installed on the system and available in PATH (checked at startup).
- The user has a valid VRT MAX subscription for accessing premium content.
- yt-dlp's VRT MAX extractor continues to work as it does at the time of implementation (yt-dlp maintainers update it independently).
- The existing credential vault and master password system remains the primary credential storage mechanism.
- Network connectivity is available for streaming and downloading; offline mode is for playing already-downloaded content.
- Download storage location defaults to the system's standard downloads directory, configurable in settings.
- The Electron app is the primary environment for downloads (background process capability); web-app downloads are limited to streaming only.
- VRT MAX may change their API at any time; yt-dlp updates are the primary defense, with the fallback custom provider as a secondary option.
