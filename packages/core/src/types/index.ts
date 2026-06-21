import { z } from "zod";
import { EpisodeSchema } from "./episode.js";

export * from "./episode.js";
export * from "./download.js";

export const SearchResultSchema = z.object({
  total: z.number(),
  episodes: z.array(EpisodeSchema),
  hasMore: z.boolean(),
  cursor: z.string().optional(),
});

export type SearchResult = z.infer<typeof SearchResultSchema>;
