import { create } from "zustand";

export type Episode = {
  id: string;
  title: string;
  season: number;
  episode: number;
  duration: string;
  url: string;
};

type State = {
  episodes: Record<string, Episode>;
  addEpisode: (episode: Episode) => void;
  removeEpisode: (id: string) => void;
};

export const useThuisStore = create<State>((set) => ({
  episodes: {},
  addEpisode: (episode) =>
    set((state) => ({
      episodes: {
        ...state.episodes,
        [episode.id]: episode,
      },
    })),
  removeEpisode: (id) =>
    set((state) => {
      const { [id]: _removed, ...rest } = state.episodes;
      return { episodes: rest };
    }),
}));