import { z } from "zod";

export const EpisodeSchema = z.object({
  id: z.string(),
  title: z.string(),
  seriesTitle: z.string(),
  season: z.number(),
  episode: z.number(),
  episodeCode: z.string(),
  duration: z.string(),
  durationSeconds: z.number().optional(),
  imageUrl: z.string().url().optional(),
  url: z.string().url(),
  description: z.string().optional(),
  available: z.boolean().optional(),
  videoId: z.string().optional(),
  provider: z.string().default("vrt"),
  airedAt: z.string().optional(),
});

export type Episode = z.infer<typeof EpisodeSchema>;

export const EpisodeDetailSchema = EpisodeSchema.extend({
  streamId: z.string(),
  manifestUrl: z.string().url().optional(),
  downloadUrl: z.string().url().optional(),
  brand: z.string().optional(),
  seasonEpisodes: z.number().optional(),
  nextEpisode: z.object({ id: z.string(), title: z.string() }).optional(),
  previousEpisode: z.object({ id: z.string(), title: z.string() }).optional(),
  videoId: z.string(),
});

export type EpisodeDetail = z.infer<typeof EpisodeDetailSchema>;
