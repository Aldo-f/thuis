import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("thuisAPI", {
  download: {
    start: (streamId: string, outputPath: string) =>
      ipcRenderer.invoke("download:start", streamId, outputPath),
    cancel: (jobId: string) =>
      ipcRenderer.invoke("download:cancel", jobId),
    onProgress: (callback: (event: { jobId: string; progress: number; status: string }) => void) => {
      ipcRenderer.on("download:progress", (_event, data) => callback(data));
    },
  },
  dialog: {
    selectFolder: () => ipcRenderer.invoke("dialog:select-folder"),
  },
  app: {
    getVersion: () => ipcRenderer.invoke("app:get-version"),
    showNotification: (title: string, body: string) =>
      ipcRenderer.invoke("app:show-notification", title, body),
  },
});
