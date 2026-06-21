import { Episode } from "../types/index.js";

export interface EpisodeSlice {
  episodes: Record<string, Episode>;
  addEpisode: (episode: Episode) => void;
  removeEpisode: (id: string) => void;
  clearEpisodes: () => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- Zustand slice creators receive untyped `set` until composition
export const createEpisodeSlice = (set: any): EpisodeSlice => ({
  episodes: {},
  addEpisode: (episode: Episode) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    set((state: any) => ({
      episodes: { ...state.episodes, [episode.id]: episode },
    })),
  removeEpisode: (id: string) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    set((state: any) => {
      const { [id]: _removed, ...rest } = state.episodes;
      return { episodes: rest };
    }),
  clearEpisodes: () => set({ episodes: {} }),
});
