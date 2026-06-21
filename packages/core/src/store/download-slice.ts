import { DownloadJob, EpisodeDetail } from "../types/index.js";

export interface DownloadSlice {
  downloads: DownloadJob[];
  activeDownloads: string[];
  enqueueDownload: (episode: EpisodeDetail) => void;
  updateDownloadProgress: (id: string, progress: number, speed?: string, eta?: string) => void;
  completeDownload: (id: string, outputPath?: string) => void;
  failDownload: (id: string, error: string) => void;
  cancelDownload: (id: string) => void;
  clearCompleted: () => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- Zustand slice creators receive untyped `set` until composition
export const createDownloadSlice = (set: any): DownloadSlice => ({
  downloads: [],
  activeDownloads: [],
  enqueueDownload: (episode: EpisodeDetail) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    set((state: any) => {
      const newJob: DownloadJob = {
        id: Math.random().toString(36).substring(7),
        episodeId: episode.id,
        episodeTitle: episode.title,
        streamId: episode.streamId,
        status: "pending",
        progress: 0,
        createdAt: new Date().toISOString(),
      };
      return {
        downloads: [newJob, ...state.downloads],
        activeDownloads: [...state.activeDownloads, newJob.id],
      };
    }),
  updateDownloadProgress: (id: string, progress: number, speed?: string, eta?: string) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    set((state: any) => ({
      downloads: state.downloads.map((job: DownloadJob) =>
        job.id === id ? { ...job, status: "downloading" as const, progress, speed, eta } : job
      ),
    })),
  completeDownload: (id: string, outputPath?: string) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    set((state: any) => ({
      downloads: state.downloads.map((job: DownloadJob) =>
        job.id === id ? { ...job, status: "completed" as const, progress: 100, completedAt: new Date().toISOString(), outputPath } : job
      ),
      activeDownloads: state.activeDownloads.filter((activeId: string) => activeId !== id),
    })),
  failDownload: (id: string, error: string) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    set((state: any) => ({
      downloads: state.downloads.map((job: DownloadJob) =>
        job.id === id ? { ...job, status: "failed" as const, error } : job
      ),
      activeDownloads: state.activeDownloads.filter((activeId: string) => activeId !== id),
    })),
  cancelDownload: (id: string) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    set((state: any) => ({
      downloads: state.downloads.map((job: DownloadJob) =>
        job.id === id ? { ...job, status: "cancelled" as const } : job
      ),
      activeDownloads: state.activeDownloads.filter((activeId: string) => activeId !== id),
    })),
  clearCompleted: () =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    set((state: any) => ({
      downloads: state.downloads.filter((job: DownloadJob) => job.status !== "completed"),
    })),
});
