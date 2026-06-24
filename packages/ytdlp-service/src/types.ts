import { z } from "zod";

// Schema for a single episode information as produced by `yt-dlp --dump-json`
// This mirrors the typical fields we rely on in the VRT MAX use‑case.
export const EpisodeSchema = z.object({
  // Unique video identifier (e.g. "12345abcde")
  id: z.string(),
  // Full title of the episode
  title: z.string(),
  // Duration in seconds
  duration: z.number().int().nonnegative(),
  // Direct URL to the video page
  webpage_url: z.string().url(),
  // Primary thumbnail image URL
  thumbnail: z.string().url(),
  // Optional description, can be omitted or empty
  description: z.string().optional(),
  // Optional upload date in YYYYMMDD format
  upload_date: z.string().regex(/^\d{8}$/).optional(),
  // Optional list of formats, we only need to keep it loosely typed for now
  formats: z.array(z.any()).optional(),
});

// Export the inferred TypeScript type for consumer code
export type EpisodeInfo = z.infer<typeof EpisodeSchema>;

// Schema for the output of `yt-dlp -g` which prints one or more URLs, one per line.
// In our service we only handle the first line (the main stream URL).
export const StreamUrlSchema = z.string().url();
export type StreamUrl = z.infer<typeof StreamUrlSchema>;
