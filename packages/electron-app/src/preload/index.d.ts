export interface ThuisAPI {
  download: {
    start: (streamId: string, outputPath: string) => Promise<string>;
    cancel: (jobId: string) => Promise<void>;
    onProgress: (callback: (event: { jobId: string; progress: number; status: string }) => void) => void;
  };
  dialog: {
    selectFolder: () => Promise<string | null>;
  };
  app: {
    getVersion: () => Promise<string>;
    showNotification: (title: string, body: string) => Promise<void>;
  };
}

declare global {
  interface Window {
    thuisAPI: ThuisAPI;
  }
}
