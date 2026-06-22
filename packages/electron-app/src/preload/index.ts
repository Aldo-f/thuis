import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("thuisAPI", {
  download: {
    start: (streamUrl: string, outputPath: string, title: string) =>
      ipcRenderer.invoke("download:start", streamUrl, outputPath, title),
    cancel: (jobId: string) =>
      ipcRenderer.invoke("download:cancel", jobId),
    list: () =>
      ipcRenderer.invoke("download:list"),
    onProgress: (callback: (data: { jobId: string; progress: number; status: string }) => void) => {
      const handler = (_event: Electron.IpcRendererEvent, data: { jobId: string; progress: number; status: string }) => callback(data);
      ipcRenderer.on("download:progress", handler);
      return () => ipcRenderer.removeListener("download:progress", handler);
    },
  },
  dialog: {
    selectFolder: () => ipcRenderer.invoke("dialog:select-folder"),
    saveFile: (defaultName: string) => ipcRenderer.invoke("dialog:save-file", defaultName),
  },
  app: {
    getVersion: () => ipcRenderer.invoke("app:get-version"),
    showNotification: (title: string, body: string) =>
      ipcRenderer.invoke("app:show-notification", title, body),
  },
  vault: {
    isAvailable: () => ipcRenderer.invoke("vault:is-available"),
    encrypt: (plaintext: string) => ipcRenderer.invoke("vault:encrypt", plaintext),
    decrypt: (encrypted: string) => ipcRenderer.invoke("vault:decrypt", encrypted),
  },
});
