import { VrtAuthService } from "../auth/VrtAuthService.js";
import { EpisodeDetail, EpisodeDetailSchema } from "../types/episode.js";
import { VIDEO_PAGE_QUERY } from "../graphql/queries.js";
import { VideoPageSchema, extractStreamId } from "../graphql/types.js";

// ─── Error types ───────────────────────────────────────────

export class EpisodeUnavailableError extends Error {
  constructor(message = "Deze aflevering is niet beschikbaar.") {
    super(message);
    this.name = "EpisodeUnavailableError";
  }
}

// ─── Helpers ───────────────────────────────────────────────

const GRAPHQL_URL = "https://www.vrt.be/vrtnu-api/graphql/v1";
const GRAPHQL_PUBLIC_URL = "https://www.vrt.be/vrtnu-api/graphql/public/v1";

/**
 * Parse an ISO 8601 duration string to total seconds.
 * "PT30M" → 1800, "PT1H30M" → 5400, "P1DT2H" → 93600
 */
function parseIsoDuration(duration: string): number {
  const match = duration.match(/^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?$/);
  if (!match) return 0;
  const days = parseInt(match[1] ?? "0", 10);
  const hours = parseInt(match[2] ?? "0", 10);
  const minutes = parseInt(match[3] ?? "0", 10);
  const seconds = parseFloat(match[4] ?? "0");
  return days * 86400 + hours * 3600 + minutes * 60 + seconds;
}

/**
 * Extract the URL path from a VRT MAX episode URL to use as GraphQL pageId.
 */
function extractPageId(url: string): string {
  try {
    const parsed = new URL(url);
    return parsed.pathname;
  } catch {
    throw new EpisodeUnavailableError("Ongeldige VRT MAX URL.");
  }
}

// ─── VrtEpisodeService ─────────────────────────────────────

export class VrtEpisodeService {
  constructor(private authService: VrtAuthService) {}

  /**
   * Fetch episode metadata from a VRT MAX episode URL.
   *
   * 1. Extracts the URL path as pageId
   * 2. Sends VideoPage GraphQL query
   * 3. On 401: refreshes auth token and retries once
   * 4. Parses response into EpisodeDetail
   */
  async getEpisode(url: string): Promise<EpisodeDetail> {
    const pageId = extractPageId(url);

    let accessToken: string | null = null;
    try {
      accessToken = await this.authService.getAccessToken();
    } catch {
      // Not logged in — will use public endpoint
    }

    const endpoint = accessToken ? GRAPHQL_URL : GRAPHQL_PUBLIC_URL;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "x-vrt-client-name": "WEB",
      "x-vrt-client-version": "1.5.9",
      "x-vrt-zone": "default",
    };
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }

    const body = JSON.stringify({
      operationName: "VideoPage",
      query: VIDEO_PAGE_QUERY,
      variables: { pageId },
    });

    let response = await fetch(endpoint, {
      method: "POST",
      headers,
      body,
    });

    // On 401, try to refresh and retry once
    if (response.status === 401) {
      const newToken = await this.authService.getAccessToken();
      headers["Authorization"] = `Bearer ${newToken}`;
      response = await fetch(endpoint, {
        method: "POST",
        headers,
        body,
      });
    }

    if (!response.ok) {
      throw new EpisodeUnavailableError(
        `GraphQL-verzoek mislukt (status ${response.status})`,
      );
    }

    const json = await response.json();

    // Check for GraphQL errors
    if (json.errors && json.errors.length > 0) {
      throw new EpisodeUnavailableError(
        `GraphQL-fout: ${json.errors[0]!.message}`,
      );
    }

    // GraphQL response wraps data in a "data" field
    const data = json.data;
    if (!data) {
      throw new EpisodeUnavailableError("Geen data ontvangen van GraphQL API.");
    }

    // Validate response shape
    const parsed = VideoPageSchema.parse(data);
    const streamId = extractStreamId(parsed);
    if (!streamId) {
      throw new EpisodeUnavailableError(
        "Geen stream ID gevonden voor deze aflevering.",
      );
    }

    const episode = parsed.page.episode;
    if (!episode) {
      throw new EpisodeUnavailableError();
    }

    // Convert ISO 8601 duration to seconds
    const durationRaw = episode.durationRaw;
    const durationSeconds = durationRaw ? parseIsoDuration(durationRaw) : undefined;

    // Determine season number from titleRaw
    const seasonStr = episode.season?.titleRaw;
    const season = seasonStr ? parseInt(seasonStr, 10) || 0 : 0;
    const episodeNum = episode.episodeNumberRaw ?? 0;

    const detail: EpisodeDetail = {
      id: episode.id ?? streamId,
      title: episode.title ?? "Onbekende titel",
      seriesTitle: episode.program?.title ?? "Onbekend programma",
      season,
      episode: episodeNum,
      episodeCode: pageId.split("/").filter(Boolean).pop() ?? "",
      duration: durationRaw ?? "",
      durationSeconds,
      imageUrl: parsed.page.player?.image?.templateUrl,
      url,
      description: episode.description,
      available: true,
      videoId: streamId,
      provider: "vrt",
      brand: episode.brand,
      streamId,
      airedAt: episode.onTimeRaw,
    };

    return EpisodeDetailSchema.parse(detail);
  }
}
