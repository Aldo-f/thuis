export interface UISlice {
  theme: "light" | "dark" | "system";
  sidebarOpen: boolean;
  setTheme: (theme: "light" | "dark" | "system") => void;
  toggleSidebar: () => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- Zustand slice creators receive untyped `set` until composition
export const createUISlice = (set: any): UISlice => ({
  theme: "system",
  sidebarOpen: false,
  setTheme: (theme) => set({ theme }),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  toggleSidebar: () => set((state: any) => ({ sidebarOpen: !state.sidebarOpen })),
});
