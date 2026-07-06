# VRT MAX Season URL Handling Plan

## TL;DR
> Extend the downloader to recognise season URLs, fetch all episode URLs via VRT MAX’s GraphQL API (with fallback), and process them as a playlist. Preserve dry‑run output and stop cleanly on 404.

## Context
- Current implementation treats a season URL as a single video, leading to “Unsupported URL” errors.
- The GraphQL API can list episodes for a given show/season, but the script does not yet use it for season URLs.
- Existing fallback logic (`_guess_episode_urls`) works but is unreliable for shows with special slug rules (e.g., “F.C. De Kampioenen”).

## Work Objectives
- [x] Detect season URLs (both `/…/<season>` and `?...seizoen=seizoen-<n>`).
- [x] Derive canonical show slug suitable for the GraphQL API (preserve double hyphens).
- [x] Query GraphQL API to obtain the `listId` for the requested season.
- [x] Paginate through episode tiles to collect all episode URLs.
- [x] Fallback to HEAD‑guessing when the API yields no results.
- [x] Stop on hard 404 (HTTP status ≥ 400) or VRT’s custom “soft‑stop” page containing the text *"Deze pagina lijkt verloren"*.
- [x] Integrate with existing dry‑run and normal download flows.
- [x] Add a `--max-episodes` CLI flag to limit processed episodes per season.
- [x] Add unit & integration tests covering success, fallback, and stop detection.
- [x] Update documentation (README, usage examples).

---
