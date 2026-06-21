import { ipcMain, dialog, Notification } from "electron";

export function registerIpcHandlers() {
  // Download channels (wired in Phase 3)
  ipcMain.handle("download:start", async (_event, streamId: string, outputPath: string) => {
    // TODO: Implement download via core downloader
    return "job-id-placeholder";
  });

  ipcMain.handle("download:cancel", async (_event, jobId: string) => {
    // TODO: Implement cancel
  });

  // Dialog
  ipcMain.handle("dialog:select-folder", async () => {
    const result = await dialog.showOpenDialog({
      properties: ["openDirectory"],
    });
    return result.canceled ? null : result.filePaths[0];
  });

  // App info
  ipcMain.handle("app:get-version", () => {
    return process.env.npm_package_version || "0.1.0";
  });

  // Notifications
  ipcMain.handle("app:show-notification", async (_event, title: string, body: string) => {
    if (Notification.isSupported()) {
      const notif = new Notification({ title, body });
      notif.show();
    }
  });

  // Download progress updates (Renderer ← Main)
  ipcMain.handle("download:progress", (_event, jobId: string, progress: number, status: string) => {
    // Forwarded via webContents.send in real implementation
  });
}
