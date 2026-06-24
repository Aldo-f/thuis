// src/YtDlpProviderAdapter.ts
/**
 * Adapter that bridges the YtDlpService to the generic ProviderAdapter interface.
 * It validates inputs/outputs using the Zod schemas exported from `types.ts`.
 */
import { ProviderAdapter } from "@thuis/core/src/providers/ProviderAdapter";
import { YtDlpService } from "./YtDlpService";
import { CookieStore } from "./CookieStore";
import { SearchResultSchema, EpisodeSchema, StreamInfoSchema } from "./types";
import type { ZodTypeAny } from "zod";

export default class YtDlpProviderAdapter implements ProviderAdapter {
  /**
   * Checks whether yt-dlp is available on the system.
   * @throws if yt-dlp binary is not found.
   */
  async init(): Promise<void> {
    const available = await YtDlpService.isAvailable();
    if (!available) {
      throw new Error("yt-dlp is not available on this system");
    }
  }

  /**
   * Perform login using credentials and persist cookies.
   * @param credentials - any object accepted by YtDlpService.login.
   */
  async login(credentials: unknown): Promise<void> {
    // Validate credentials shape if needed – any validation is delegated to the service.
    await YtDlpService.login(credentials as Record<string, unknown>);
    // Persist any cookies set by the service.
    await CookieStore.saveCookies();
  }

  /**
   * Search for videos based on a query string.
   * Currently returns an empty array as a placeholder.
   * @param query Search query.
   */
  async search(query: string): Promise<ZodTypeAny[]> {
    // Placeholder implementation – real search would call YtDlpService.extractMetadata with appropriate args.
    // Returning empty array conforms to ProviderAdapter contract.
    // Future implementation can map YtDlpService results to SearchResultSchema.
    return [];
  }

  /**
   * Retrieve full episode metadata for a given URL.
   * @param url Video URL.
   * @returns Parsed episode object.
   */
  async getEpisode(url: string): Promise<unknown> {
    const raw = await YtDlpService.extractMetadata(url);
    // Validate against schema – will throw if invalid.
    return EpisodeSchema.parse(raw);
  }

  /**
   * Resolve the direct stream URL for an episode.
   * @param episode Episode metadata (validated shape).
   * @returns Stream information.
   */
  async resolveStream(episode: unknown): Promise<unknown> {
    const raw = await YtDlpService.extractStreamUrl(episode as any);
    return StreamInfoSchema.parse(raw);
  }
}
