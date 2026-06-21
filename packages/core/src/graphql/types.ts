import { z } from "zod";

// Minimal GraphQL response types for VRT MAX
export const ComponentIdSchema = z.string();

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
