// packages/ytdlp-service/src/YtDlpService.ts

import { spawn } from "child_process";
import { z } from "zod";
import type { Episode, StreamUrl } from "./types.js";

/**
 * Service wrapper around the `yt-dlp` binary.
 * Provides small utility methods used by other parts of the package.
 */
export default class YtDlpService {
/**
    * Check if the `yt-dlp` executable is available in the system PATH.
    */
   async isAvailable(): Promise<boolean> {
     return new Promise((resolve) => {
       const proc = spawn("yt-dlp", ["--version"]);
       proc.on("error", () => resolve(false));
       proc.on("close", (code: number) => resolve(code === 0));
     });
   }

  /**
   * Get the version string of the installed `yt-dlp` binary.
*/
   async getVersion(): Promise<string> {
     return new Promise((resolve, reject) => {
       const proc = spawn("yt-dlp", ["--version"]);
       let stdout = "";
       let stderr = "";
       proc.stdout.on("data", (data) => (stdout += data.toString()));
       proc.stderr.on("data", (data) => (stderr += data.toString()));
       proc.on("error", (err: Error) => reject(new Error(`yt-dlp not found: ${err.message}`)));
       proc.on("close", (code) => {
         if (code === 0) {
           return resolve(stdout.trim());
         } else {
           return reject(new Error(`yt-dlp exited with ${code}: ${stderr.trim()}`));
         }
       });
     });
   }

  /**
   * Extract full metadata for a given URL.
   */
  async extractMetadata(url: string): Promise<any> {
    if (!url) throw new Error("URL must be provided");
    return new Promise((resolve, reject) => {
      const proc = spawn("yt-dlp", ["--dump-json", url]);
      let stdout = "";
      let stderr = "";
      proc.stdout.on("data", (data) => (stdout += data.toString()));
      proc.stderr.on("data", (data) => (stderr += data.toString()));
      proc.on("error", (err) => reject(err));
      proc.on("close", (code) => {
        if (code === 0) {
          try {
            const json = JSON.parse(stdout);
            resolve(json);
          } catch (e) {
            reject(new Error(`Failed to parse yt-dlp JSON: ${(e as Error).message}`));
          }
        } else {
          reject(new Error(`yt-dlp error ${code}: ${stderr.trim()}`));
        }
      });
    });
  }

  /**
   * Get the direct stream URL (usually an HLS manifest) for the given video URL.
   */
  async extractStreamUrl(url: string): Promise<string> {
    if (!url) throw new Error("URL must be provided");
    return new Promise((resolve, reject) => {
      const proc = spawn("yt-dlp", ["-g", url]);
      let stdout = "";
      let stderr = "";
      proc.stdout.on("data", (data) => (stdout += data.toString()));
      proc.stderr.on("data", (data) => (stderr += data.toString()));
      proc.on("error", (err) => reject(err));
      proc.on("close", (code) => {
        if (code === 0) {
          const url = stdout.trim();
          // Optional lightweight validation using Zod
          const UrlSchema = z.string().url();
          try {
            UrlSchema.parse(url);
            resolve(url);
          } catch (e) {
            reject(new Error(`Invalid stream URL returned by yt-dlp: ${url}`));
          }
        } else {
          reject(new Error(`yt-dlp error ${code}: ${stderr.trim()}`));
        }
      });
    });
  }

  /**
   * Extract a flat playlist – returns an array of episode objects.
   */
  async extractPlaylist(url: string): Promise<Episode[]> {
    if (!url) throw new Error("URL must be provided");
    return new Promise((resolve, reject) => {
      const proc = spawn("yt-dlp", ["--dump-json", "--flat-playlist", url]);
      let stdout = "";
      let stderr = "";
      proc.stdout.on("data", (data) => (stdout += data.toString()));
      proc.stderr.on("data", (data) => (stderr += data.toString()));
      proc.on("error", (err) => reject(err));
      proc.on("close", (code) => {
        if (code === 0) {
          try {
            const lines = stdout.trim().split(/\n+/);
            const episodes = lines.map((line) => JSON.parse(line) as Episode);
            resolve(episodes);
          } catch (e) {
            reject(new Error(`Failed to parse playlist JSON: ${(e as Error).message}`));
          }
        } else {
          reject(new Error(`yt-dlp error ${code}: ${stderr.trim()}`));
        }
      });
    });
  }

  /**
   * Login to a site using yt-dlp's built‑in login flow.
   * The actual cookie storage implementation lives in `CookieStore`.
   */
  async login(email: string, password: string): Promise<void> {
    if (!email || !password) throw new Error("Both email and password are required");
    // Placeholder implementation – actual cookie handling will be added later.
    return new Promise((resolve, reject) => {
      const proc = spawn("yt-dlp", ["--username", email, "--password", password, "--cookies", "-", "--skip-download", "dummy"]);
      let stderr = "";
      proc.stderr.on("data", (data) => (stderr += data.toString()));
      proc.on("error", (err) => reject(err));
      proc.on("close", (code) => {
        if (code === 0) {
          // TODO: integrate CookieStore to persist cookies
          resolve();
        } else {
          reject(new Error(`yt-dlp login failed with ${code}: ${stderr.trim()}`));
        }
      });
    });
  }
}
