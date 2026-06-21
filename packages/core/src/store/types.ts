import type { EpisodeSlice } from "./episode-slice.js";
import type { DownloadSlice } from "./download-slice.js";
import type { UISlice } from "./ui-slice.js";

export interface ThuisStore extends EpisodeSlice, DownloadSlice, UISlice {
  _hasHydrated: boolean;
}
