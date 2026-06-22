export interface ThuisAPI {
  download: {
    start: (streamUrl: string, outputPath: string, title: string) => Promise<string>;
    cancel: (jobId: string) => Promise<void>;
    list: () => Promise<Array<{
      id: string;
      streamUrl: string;
      outputPath: string;
      title: string;
      status: string;
      progress: number;
    }>>;
    onProgress: (callback: (data: { jobId: string; progress: number; status: string }) => void) => () => void;
  };
  dialog: {
    selectFolder: () => Promise<string | null>;
    saveFile: (defaultName: string) => Promise<string | null>;
  };
  app: {
    getVersion: () => Promise<string>;
    showNotification: (title: string, body: string) => Promise<void>;
  };
  vault: {
    isAvailable: () => Promise<boolean>;
    encrypt: (plaintext: string) => Promise<string>;
    decrypt: (encrypted: string) => Promise<string>;
  };
}

declare global {
  interface Window {
    thuisAPI: ThuisAPI;
  }
}
