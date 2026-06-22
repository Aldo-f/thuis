import {
  ipcMain,
  dialog,
  BrowserWindow,
  safeStorage,
  Notification,
} from "electron";
import { DownloadEngine } from "./download-engine.js";

const engine = new DownloadEngine();

export function registerIpcHandlers(): void {
  // ─── Download ─────────────────────────────────────────

  ipcMain.handle("download:start", async (_event, streamUrl: string, outputPath: string, title: string) => {
    const jobId = await engine.startDownload(streamUrl, outputPath, title);
    return jobId;
  });

  ipcMain.handle("download:cancel", async (_event, jobId: string) => {
    engine.cancelDownload(jobId);
  });

  ipcMain.handle("download:progress", (_event, jobId: string, progress: number, status: string) => {
    // Forward progress to renderer
    const windows = BrowserWindow.getAllWindows();
    for (const win of windows) {
      win.webContents.send("download:progress", { jobId, progress, status });
    }
  });

  ipcMain.handle("download:list", () => {
    return engine.getAllJobs();
  });

  // Listen for engine progress and forward to all renderers
  engine.onProgress((jobId, progress, status) => {
    const windows = BrowserWindow.getAllWindows();
    for (const win of windows) {
      win.webContents.send("download:progress", { jobId, progress, status });
    }
  });

  // ─── Dialog ────────────────────────────────────────────

  ipcMain.handle("dialog:select-folder", async () => {
    const result = await dialog.showOpenDialog({
      properties: ["openDirectory"],
    });
    return result.canceled ? null : result.filePaths[0];
  });

  ipcMain.handle("dialog:save-file", async (_event, defaultName: string) => {
    const result = await dialog.showSaveDialog({
      defaultPath: defaultName,
      filters: [{ name: "Video", extensions: ["mp4"] }],
    });
    return result.canceled ? null : result.filePath;
  });

  // ─── App info ──────────────────────────────────────────

  ipcMain.handle("app:get-version", () => {
    return process.env.npm_package_version || "0.1.0";
  });

  ipcMain.handle("app:show-notification", async (_event, title: string, body: string) => {
    if (Notification.isSupported()) {
      const notif = new Notification({ title, body });
      notif.show();
    }
  });

  // ─── Vault (safeStorage) ─────────────────────────────────

  ipcMain.handle("vault:is-available", () => {
    return safeStorage.isEncryptionAvailable();
  });

  ipcMain.handle("vault:encrypt", async (_event, plaintext: string) => {
    const encrypted = safeStorage.encryptString(plaintext);
    return encrypted.toString("base64");
  });

  ipcMain.handle("vault:decrypt", async (_event, encryptedBase64: string) => {
    const encrypted = Buffer.from(encryptedBase64, "base64");
    return safeStorage.decryptString(encrypted);
  });
}
