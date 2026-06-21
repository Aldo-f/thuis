import { create } from "zustand";
import { persist } from "zustand/middleware";
import { Episode } from "../types/episode.js";

export interface EpisodeSlice {
  episodes: Record<string, Episode>;
  addEpisode: (episode: Episode) => void;
  removeEpisode: (id: string) => void;
  clearEpisodes: () => void;
}

export const createEpisodeSlice = (set: any) =>
  persist(
    (set: any) => ({
      episodes: {},
      addEpisode: (episode: Episode) =>
        set((state: any) => ({
          episodes: { ...state.episodes, [episode.id]: episode },
        })),
      removeEpisode: (id: string) =>
        set((state: any) => {
          const { [id]: _, ...rest } = state.episodes;
          return { episodes: rest };
        }),
      clearEpisodes: () => set({ episodes: {} }),
    }),
    {
      name: "thuis-episode-store", // storage key
    }
  );
