import { z } from "zod";


export const ComponentIdSchema = z.string();

export const ProviderCredentialSchema = z.object({
  providerId: z.string(),
  email: z.string().email(),
  encryptedPassword: z.string(),
});

export type ProviderCredential = z.infer<typeof ProviderCredentialSchema>;


export const TileFragmentSchema = z.object({
  __typename: z.string(),
  title: z.string().optional(),
  description: z.string().optional(),
  image: z.object({ templateUrl: z.string().url() }).optional(),
  action: z.object({ link: z.string().url() }).optional(),
  primaryMeta: z.array(z.object({ type: z.string(), value: z.string() })).optional(),
  secondaryMeta: z.array(z.object({ type: z.string(), value: z.string() })).optional(),
});

export const EpisodeTileSchema = TileFragmentSchema.extend({
  __typename: z.literal("EpisodeTile"),
  season: z.number().optional(),
  episode: z.number().optional(),
});

export const PaginatedTileListSchema = z.object({
  title: z.string().optional(),
  paginatedItems: z.object({
    edges: z.array(
      z.object({
        node: TileFragmentSchema,
      })
    ),
    pageInfo: z.object({
      endCursor: z.string().nullable(),
      hasNextPage: z.boolean(),
      hasPreviousPage: z.boolean(),
      startCursor: z.string().nullable(),
    }),
  }),
});

export const ComponentResponseSchema = z.object({
  component: z.union([EpisodeTileSchema, PaginatedTileListSchema, z.object({ __typename: z.string() })]),
});

export type ComponentResponse = z.infer<typeof ComponentResponseSchema>;

// ─── VideoPage types (new VRT MAX GraphQL API) ──────────────

export const VideoPageEpisodeSchema = z.object({
  ageRaw: z.string().optional(),
  description: z.string().optional(),
  durationRaw: z.string().optional(),
  episodeNumberRaw: z.number().optional(),
  id: z.string().optional(),
  name: z.string().optional(),
  onTimeRaw: z.string().optional(),
  program: z.object({ title: z.string().optional() }).optional(),
  season: z.object({ id: z.string().optional(), titleRaw: z.string().optional() }).optional(),
  title: z.string().optional(),
  brand: z.string().optional(),
});

export const VideoPagePlayerSchema = z.object({
  image: z.object({ templateUrl: z.string().optional() }).optional(),
  modes: z.array(z.object({ streamId: z.string() })).optional(),
});

export const VideoPageSchema = z.object({
  page: z.object({
    episode: VideoPageEpisodeSchema.optional(),
    ldjson: z.any().optional(),
    player: VideoPagePlayerSchema.optional(),
  }),
});

export type VideoPageResponse = z.infer<typeof VideoPageSchema>;

/**
 * Extract streamId from a VideoPage response.
 * Returns the first streamId from player.modes, or null if none found.
 */
export function extractStreamId(response: VideoPageResponse): string | null {
  const modes = response?.page?.player?.modes;
  if (modes && modes.length > 0) {
    return modes[0]!.streamId;
  }
  return null;
}
