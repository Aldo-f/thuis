import { create } from "zustand";
import { persist } from "zustand/middleware";
import { createEpisodeSlice } from "./episode-slice.js";
import { createDownloadSlice } from "./download-slice.js";
import { createUISlice } from "./ui-slice.js";
import type { ThuisStore } from "./types.js";

export type { ThuisStore } from "./types.js";

export const useThuisStore = create<ThuisStore>()(
  persist(
    (set) => ({
      ...createEpisodeSlice(set),
      ...createDownloadSlice(set),
      ...createUISlice(set),
      _hasHydrated: false,
    }),
    {
      name: "thuis-combined-store",
      onRehydrateStorage: () => (state) => {
        if (state) {
          state._hasHydrated = true;
        }
      },
    }
  )
);

export * from "./episode-slice.js";
export * from "./download-slice.js";
export * from "./ui-slice.js";
