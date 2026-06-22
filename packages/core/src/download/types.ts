import { z } from "zod";

// ─── Stream Data ───────────────────────────────────────────

export const TargetUrlSchema = z.object({
  type: z.enum(["hls", "hls_aes", "mp4", "mpeg_dash", "hds", "hss"]),
  url: z.string().url(),
  quality: z.string().optional(),
});

export const SubtitleUrlSchema = z.object({
  url: z.string().url(),
  language: z.string().default("nl"),
  format: z.string().default("vtt"),
});

export type TargetUrl = z.infer<typeof TargetUrlSchema>;
export type SubtitleUrl = z.infer<typeof SubtitleUrlSchema>;

export const StreamDataSchema = z.object({
  title: z.string().optional(),
  duration: z.number().optional(),
  drm: z.boolean().default(false),
  posterImageUrl: z.string().url().optional(),
  targetUrls: z.array(TargetUrlSchema).default([]),
  subtitles: z.array(SubtitleUrlSchema).optional(),
  code: z.string().optional(),
});

export type StreamData = z.infer<typeof StreamDataSchema>;

// ─── Stream Error Codes ────────────────────────────────────

// ─── Stream Error Codes ────────────────────────────────────

export const STREAM_ERROR_CODES = {
  GEO_BLOCKED: "CONTENT_AVAILABLE_ONLY_FOR_BE_RESIDENTS",
  GEO_BLOCKED_ALT: "CONTENT_AVAILABLE_ONLY_IN_BE",
  GEO_BLOCKED_PROXY: "CONTENT_UNAVAILABLE_VIA_PROXY",
  AGE_RESTRICTED: "CONTENT_IS_AGE_RESTRICTED",
  LOGIN_REQUIRED: "CONTENT_REQUIRES_AUTHENTICATION",
  EXPATS: "CONTENT_AVAILABLE_ONLY_FOR_BE_RESIDENTS_AND_EXPATS",
} as const;

// ─── Error types ───────────────────────────────────────────

export class StreamError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = "StreamError";
  }
}

export class DrmError extends StreamError {
  constructor(message = "Deze video is beveiligd en kan niet worden gedownload.") {
    super(message, "DRM_PROTECTED");
    this.name = "DrmError";
  }
}

export class GeoBlockedError extends StreamError {
  constructor(message = "Deze video is enkel beschikbaar in België.") {
    super(message, "GEO_BLOCKED");
    this.name = "GeoBlockedError";
  }
}
