declare module "hls.js" {
  interface HlsConfig { [key: string]: unknown }
  interface HlsEvent { [key: string]: unknown }
  interface HlsErrorData { fatal: boolean }
  interface HlsManifestData { [key: string]: unknown }

  class Hls {
    static isSupported(): boolean;
    constructor(config?: HlsConfig);
    loadSource(url: string): void;
    attachMedia(element: HTMLMediaElement): void;
    on(event: string, handler: (event: unknown, data: unknown) => void): void;
    destroy(): void;
    static Events: {
      MANIFEST_PARSED: string;
      ERROR: string;
    };
  }
  export default Hls;
}
