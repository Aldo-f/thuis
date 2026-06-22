import { app, BrowserWindow, ipcMain, dialog, Notification, Tray } from "electron";
import { createTray, updateTrayProgress, destroyTray } from "./tray-manager.js";
import { DownloadEngine } from "./download-engine.js";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { registerIpcHandlers } from "./ipc-handlers.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

let mainWindow: BrowserWindow | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: "Thuis — VRT MAX Content Monitor",
    webPreferences: {
      preload: join(__dirname, "..", "preload", "index.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  if (process.env.NODE_ENV === "development") {
    mainWindow.loadURL("http://localhost:5173");
  } else {
    mainWindow.loadFile(join(__dirname, "..", "..", "..", "web-app", "dist", "index.html"));
  }
}

app.whenReady().then(() => {
  createTray();
  registerIpcHandlers();
  createWindow();

  // Wire up download engine progress to tray
  const engine = new DownloadEngine();
  engine.onProgress((jobId, progress, status) => {
    updateTrayProgress(progress, status);
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    destroyTray();
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
