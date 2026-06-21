import { z } from "zod";

export const DownloadStatusSchema = z.enum([
  "pending",
  "downloading",
  "completed",
  "failed",
  "cancelled",
]);

export type DownloadStatus = z.infer<typeof DownloadStatusSchema>;

export const DownloadJobSchema = z.object({
  id: z.string(),
  episodeId: z.string(),
  episodeTitle: z.string(),
  streamId: z.string(),
  status: DownloadStatusSchema,
  progress: z.number().min(0).max(100).default(0),
  speed: z.string().optional(),
  eta: z.string().optional(),
  error: z.string().optional(),
  outputPath: z.string().optional(),
  createdAt: z.string().datetime(),
  completedAt: z.string().datetime().optional(),
  fileSize: z.number().optional(),
});

export type DownloadJob = z.infer<typeof DownloadJobSchema>;
