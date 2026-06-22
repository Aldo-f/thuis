import { app, Tray, Menu, nativeImage, BrowserWindow } from "electron";
import path from "node:path";

let tray: Tray | null = null;

export function createTray() {
  if (tray) return tray;

  const iconPath = path.join(__dirname, "..", "assets", "icon.png");
  const icon = nativeImage.createFromPath(iconPath);
  tray = new Tray(icon);
  tray.setToolTip("Thuis");

  const contextMenu = Menu.buildFromTemplate([
    {
      label: "Thuis",
      enabled: false,
    },
    { type: "separator" },
    {
      label: "Afsluiten",
      role: "quit",
    },
  ]);

  tray.setContextMenu(contextMenu);
  tray.on("click", () => {
    const window = BrowserWindow.getAllWindows()[0];
    if (window) {
      if (window.isVisible()) window.hide();
      else window.show();
    }
  });

  return tray;
}

export function updateTrayProgress(progress: number, status: string) {
  if (!tray) return;
  const statusText = {
    downloading: `Downloadend ${progress}%`,
    completed: "Download voltooid",
    failed: "Download mislukt",
    paused: "Download gepauzeerd",
    pending: "Wachten...",
    cancelled: "Geannuleerd",
  }[status] ?? status;

  tray.setToolTip(`Thuis - ${statusText}`);
}

export function destroyTray() {
  if (tray) {
    tray.destroy();
    tray = null;
  }
}
