# Feature Specification: In-App Video Viewer & Download Engine

**Feature Branch**: `004-video-viewer-download`

**Priority key**: P0 = ship first, P1 = ship immediately after, P2 = future, P3 = nice-to-have

**Created**: 2026-06-22

**Status**: Draft

**Input**: SPEC.md v0.2.0 sections 10, 13, 14

---

## User Scenarios & Testing

### User Story 1 — HLS Video Playback (Priority: P1 — view without download)

**Direct viewing is the primary UX**: users watch first, download only when they want offline copies.

As a user, I want to watch an episode directly in the app so that I don't have to download it first to preview the content.

**Why this priority**: Instant playback is the core value of a video viewer. All other player features build on this.

**Independent Test**: Can be tested with a synthetic HLS stream served from a local Playwright route handler. Verify that the HLS.js player loads, plays for N seconds, and emits play/pause events.

**Acceptance Scenarios**:

1. **Given** a resolved HLS stream URL, **When** the episode page loads, **Then** the video starts buffering and the player controls appear.
2. **Given** a playing video, **When** the user clicks pause, **Then** playback pauses and the play button appears.
3. **Given** a paused video, **When** the user clicks play, **Then** playback resumes from the paused position.
4. **Given** a resolved stream, **When** HLS.js fails to load the manifest, **Then** an error message is shown ("Video kan niet worden geladen.").
5. **Given** DRM-protected content, **When** the episode page loads, **Then** a clear message is shown: "Deze video is beveiligd en kan niet worden afgespeeld in de app."

---

### User Story 2 — Player Controls (Priority: P1)

As a user, I want standard video controls — seek, volume, fullscreen, playback speed — so that I have a comfortable viewing experience.

**Why this priority**: Controls are essential for usability. Without them, the player is unusable beyond "play what loads."

**Independent Test**: Test each control independently via Playwright component tests. Verify that clicking seek bar changes currentTime, volume slider changes volume, fullscreen button triggers Fullscreen API, etc.

**Acceptance Scenarios**:

1. **Given** a playing video, **When** the user drags the seek bar to 50%, **Then** the video seeks to the corresponding timestamp.
2. **Given** a playing video, **When** the user moves the volume slider to 0%, **Then** the video is muted.
3. **Given** a playing video, **When** the user clicks the fullscreen button, **Then** the video enters fullscreen mode.
4. **Given** a playing video, **When** the user selects 1.5x speed from the speed menu, **Then** playback speed increases.
5. **Given** a playing video in fullscreen, **When** the user presses Escape, **Then** fullscreen is exited.
6. **Given** a playing video, **When** the user presses Space, **Then** playback toggles pause/play.
7. **Given** a playing video, **When** the user presses M, **Then** audio toggles mute/unmute.
8. **Given** a playing video, **When** the user presses → (right arrow), **Then** the video seeks forward by 10 seconds.
9. **Given** a playing video, **When** the user presses ← (left arrow), **Then** the video seeks backward by 10 seconds.

---

### User Story 3 — Episode Info Overlay (Priority: P2)

As a user, I want to see episode metadata (title, description, season, episode number) while watching so that I know what I'm viewing.

**Why this priority**: Context matters for viewing — users often want to know "what episode is this?" without leaving the video.

**Independent Test**: Render the overlay with mock episode data. Verify all fields are displayed correctly. Verify that the overlay auto-hides after N seconds of playback.

**Acceptance Scenarios**:

1. **Given** a loaded episode, **When** the video starts, **Then** the overlay shows title, series name, season/episode numbers for 5 seconds then fades.
2. **Given** a playing video, **When** the user moves the mouse, **Then** the overlay reappears.
3. **Given** the overlay visible, **When** the user does not move the mouse for 3 seconds, **Then** the overlay fades out.

---

### User Story 4 — Download Button in Player (Priority: P2)

As a user, I want to download the episode I'm currently watching with one click so that I can save it for offline viewing.

**Why this priority**: The download-from-player flow is the most intuitive way to initiate downloads and connects the viewer to the download queue.

**Independent Test**: Verify that clicking the download button adds a DownloadJob to the queue store with the correct episodeId and streamId. Mock the queue store.

**Acceptance Scenarios**:

1. **Given** a loaded episode with resolved stream, **When** the user clicks the download button, **Then** a DownloadJob is created with status "pending".
2. **Given** an existing download for the same episode, **When** the user clicks download, **Then** a toast notification says "Deze aflevering staat al in de downloadwachtrij."
3. **Given** DRM-protected content, **When** the user clicks download, **Then** a toast notification says "Deze video is beveiligd en kan niet worden gedownload."

---

### User Story 5 — Auto-Next Episode (Priority: P3)

As a user, I want the next episode to start playing automatically when the current one ends so that I can binge-watch without interruption.

**Why this priority**: Auto-next is a quality-of-life feature for series watching that significantly improves the experience.

**Independent Test**: With 2 mock episodes in a season, verify that when the first emits "ended" event, the second episode loads and starts playing within 5 seconds. No user interaction needed.

**Acceptance Scenarios**:

1. **Given** a playing episode that is not the season finale, **When** it reaches the end, **Then** the next episode loads and starts playing after a 5-second countdown.
2. **Given** an auto-next countdown, **When** the user clicks "Cancel", **Then** playback stops and the episode detail page is shown.
3. **Given** a playing episode that is the season finale, **When** it reaches the end, **Then** a message "Dit was het einde van het seizoen" is shown instead of auto-next.

---

### User Story 6 — FFmpeg Download Engine (Priority: P0)

As a user, I want to download episodes as MP4 files so that I can watch them offline or keep a copy.

**Why this priority**: Download is a core feature — users expect to save episodes for offline viewing.

**Independent Test**: Unit test FFmpeg argument construction with mocked child_process. Integration test with a real HLS stream (optional, requires credentials).

**Acceptance Scenarios**:

1. **Given** a resolved HLS URL, **When** download() is called with an output path, **Then** FFmpeg is spawned with correct `-i <hls_url> -c copy -y <output>` arguments.
2. **Given** a running download, **When** progress events are emitted, **Then** they contain bytes downloaded, speed, and ETA.
3. **Given** a network failure during download, **When** FFmpeg exits with non-zero code, **Then** DownloadError is thrown with the FFmpeg stderr message.
4. **Given** FFmpeg is not found in PATH, **When** download() is called, **Then** a clear error "FFmpeg is niet geïnstalleerd" is shown with install instructions.
5. **Given** an Electron environment, **When** the download completes, **Then** an OS notification is shown.
6. **Given** a web environment, **When** download is requested, **Then** the HLS URL is provided for manual download via a third-party tool, or stream capture is attempted.

**Platform differences**:

| Platform | Download Mechanism |
|----------|-------------------|
| Electron | FFmpeg `child_process.spawn` — full download to user-chosen directory |
| Web | No FFmpeg available. Option 1: Show HLS URL for manual use. Option 2: HLS stream capture via `MediaRecorder` (lossy, P3). Option 3: Server-side proxy with FFmpeg on the VPS (P3). |

---

### User Story 7 — Download Queue (Priority: P0)

As a user, I want to queue multiple episode downloads and see their progress so that I can batch-download content overnight.

**Why this priority**: Batch downloading is essential for users who want to grab entire seasons.

**Independent Test**: Test queue state machine in isolation without actual FFmpeg.

**Acceptance Scenarios**:

1. **Given** multiple episodes, **When** added to the queue, **Then** they are processed sequentially.
2. **Given** a queue with a running download, **When** pause() is called, **Then** FFmpeg receives SIGSTOP and the job status changes to 'paused'.
3. **Given** a paused download, **When** resume() is called, **Then** FFmpeg receives SIGCONT and the job resumes.
4. **Given** completed downloads, **When** the queue view is opened, **Then** completed items show file size and duration.
5. **Given** an app restart with pending downloads, **When** the app reopens, **Then** the queue state is restored from persisted storage.

---

### User Story 8 — Episode Page Design (Priority: P1)

As a user, I want a dedicated episode page that shows metadata, the video player, and download options so that I have all episode-related actions in one place.

**Why this priority**: The episode page is the primary UI for all video interactions (play, view info, download). Without it, users have no way to access resolved content.

**Independent Test**: Render the page with mock episode data. Verify layout: player at top, metadata below, download button present. Test loading, error, and empty states.

**Acceptance Scenarios**:

1. **Given** a resolved episode with stream, **When** the episode page renders, **Then** the player is visible at the top with controls.
2. **Given** a resolved episode, **When** the episode page renders, **Then** metadata (title, series, season, episode, description, duration) is displayed below the player.
3. **Given** a resolved episode, **When** the episode page renders, **Then** a download button is visible in the player controls and below the metadata.
4. **Given** an episode that is still loading, **When** the episode page renders, **Then** skeleton loaders are shown for the player and metadata areas.
5. **Given** a stream resolution failure, **When** the episode page renders, **Then** an error message with a retry button is displayed in place of the player.

---

### Edge Cases

- What happens when HLS.js is not supported (e.g., very old browser)? → Show "Uw browser ondersteunt geen HLS-streaming" with a direct HLS URL for manual use.
- What happens when the user switches browser tabs during playback? → Playback continues (no pause on tab switch — standard browser behavior).
- What happens when the network drops during playback? → HLS.js adaptive bitrate will try lower quality; if stream dies, show "Verbinding verbroken" with retry.
- What happens when the user has multiple tabs with the player open? → Each tab plays independently (no cross-tab sync — expected behavior).
- What happens when PiP is not supported? → PiP button is hidden (feature detection).
- What happens when the next episode fails to load during auto-next? → Show error message and a "Manual" button to go back to the episode list.
- What happens when the download button is clicked during an active download? → Show "Al in wachtrij" toast.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST render an HLS stream using HLS.js as the playback engine.
- **FR-002**: System MUST provide standard media controls: play/pause, seek, volume, fullscreen, picture-in-picture.
- **FR-003**: System MUST support playback speed control (0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x).
- **FR-004**: System MUST support keyboard shortcuts: Space (play/pause), F (fullscreen), M (mute), ←/→ (seek ±10s), ↑/↓ (volume ±10%).
- **FR-005**: System MUST show an episode info overlay at video start that auto-hides after 5 seconds and reappears on mouse movement.
- **FR-006**: System MUST provide a download button in the player controls and on the episode detail page.
- **FR-007**: System MUST prevent duplicate download queue entries (dedup by episodeId).
- **FR-008**: System MUST support auto-next episode playback with a 5-second countdown and cancel option.
- **FR-009**: System MUST NOT auto-next for the final episode of a season.
- **FR-010**: System MUST display Dutch error messages for all failure modes.
- **FR-011**: System MUST show skeleton loading states while episode metadata and stream URL are being fetched.
- **FR-012**: System MUST NOT expose the raw HLS URL in the UI unless the user explicitly requests it via a "Show technical details" option.
- **FR-013**: System MUST provide a responsive layout: player is full-width on mobile, max 1200px centered on desktop.

### UI Component States

Every interactive component on the episode page must handle:

| State | Component | Display |
|-------|-----------|---------|
| **Loading** | Player area | Skeleton with animated shimmer (16:9 aspect ratio placeholder) |
| **Loading** | Metadata area | 3 skeleton lines of varying width |
| **Error** | Player area | Error card with icon + message + "Probeer opnieuw" button |
| **Error** | Metadata fallback | Title only (from episode list data) if GraphQL failed |
| **Empty** | Player area | N/A (player always has content or error) |
| **Success** | Player + Metadata | Normal rendering |

### Error Messages (all in Dutch)

| Condition | Message |
|-----------|---------|
| HLS.js fails to load | "Video kan niet worden geladen. Probeer het later opnieuw." |
| DRM detected | "Deze video is beveiligd en kan niet worden afgespeeld in de app." |
| Network dropped | "Verbinding verbroken. Probeer opnieuw." |
| Browser doesn't support HLS | "Uw browser ondersteunt geen HLS-streaming." |
| Auto-next fail | "Volgende aflevering kon niet worden geladen." |
| Season finale reached | "Dit was het einde van het seizoen." |
| Duplicate download | "Deze aflevering staat al in de downloadwachtrij." |
| DRM download blocked | "Deze video is beveiligd en kan niet worden gedownload." |

### Key Entities

- **PlayerState**: currentTime, duration, paused, volume, muted, playbackRate, isFullscreen, isPiP. Managed via Zustand slice or React context.
- **EpisodePageState**: episode (EpisodeDetail | null), stream (StreamData | null), loading (boolean), error (string | null). Managed via Zustand or react-query.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Video starts playing within 5 seconds of clicking the episode (network-dependent; measured from page load to first frame).
- **SC-002**: All player controls respond within 100ms of user interaction.
- **SC-003**: Seek bar drag updates video position within 200ms.
- **SC-004**: Fullscreen transition completes within 300ms.
- **SC-005**: Auto-next triggers within 5 seconds of episode end and is cancelable.
- **SC-006**: All player keyboard shortcuts work without focus issues.
- **SC-007**: Episode page renders below 60fps frame budget (measured via React DevTools profiler).
- **SC-008**: Zero console errors in player-related tests.

---

## Assumptions

- The browser supports MediaSource Extensions (MSE) — required by HLS.js. All modern browsers do, but Safari uses native HLS.
- HLS.js v1+ is used, which handles most HLS variants including fMP4 segments.
- The VRT MAX HLS streams use AES-128 encryption (not SAMPLE-AES) — FFmpeg can handle this with `-decryption_key`.
- VRT MAX streams do not require per-request tokens beyond the vrtPlayerToken (which is obtained during stream resolution).
- The user's screen is at least 360px wide (mobile minimum). Below that, the player collapses to full-width with minimal controls.
- Picture-in-PiP is available in most modern browsers except some mobile browsers.
- For the initial implementation, the player shows only VRT MAX content. Cross-provider playback (VTM, Play.TV) is future scope.

---

## Notes

- HLS.js should be configured with `startLevel: -1` (auto) for adaptive bitrate, with manual quality selection available via a settings menu.
- For Electron, consider using the native Chromium `<video>` element with HLS.js rather than Chromium's native HLS support (for consistent behavior with the web app).
- DRM detection should happen at stream resolution time (in `VrtEpisodeService.resolveStream()`), so the UI never attempts to play DRM content.
- The player should lazy-load below-the-fold content (episode description, comments if any) to prioritize first-frame time.
- Consider using `React.lazy()` for the player component itself — not everyone visits the episode page.
- The keyboard shortcuts should be scoped to the player-focused state (not global) to avoid interfering with other page interactions.
- Auto-next requires pre-fetching the next episode's stream URL so there's no loading delay between episodes.
