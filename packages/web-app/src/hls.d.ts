declare module "hls.js" {
  interface HlsConfig {}
  interface HlsEvent {}
  interface HlsErrorData { fatal: boolean }
  interface HlsManifestData {}

  class Hls {
    static isSupported(): boolean;
    constructor(config?: HlsConfig);
    loadSource(url: string): void;
    attachMedia(element: HTMLMediaElement): void;
    on(event: string, handler: (event: any, data: any) => void): void;
    destroy(): void;
    static Events: {
      MANIFEST_PARSED: string;
      ERROR: string;
    };
  }
  export default Hls;
}
