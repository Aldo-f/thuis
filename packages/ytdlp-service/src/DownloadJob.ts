// packages/ytdlp-service/src/DownloadJob.ts

import { EventEmitter } from "node:events";
import { spawn } from "node:child_process";
import type { ChildProcess } from "node:child_process";
import { z } from "zod";
import type { StreamUrl } from "./types.js";

/**
 * Status of a download job.
 */
export const JobStatusSchema = z.enum([
  "queued",
  "downloading",
  "paused",
  "completed",
  "failed",
  "cancelled",
]);
export type JobStatus = z.infer<typeof JobStatusSchema>;

/**
 * Progress information for a download job.
 */
export const JobProgressSchema = z.object({
  percentage: z.number().min(0).max(100).default(0),
  speed: z.string().optional(),
  eta: z.string().optional(),
  bytesDownloaded: z.number().int().nonnegative().default(0),
});
export type JobProgress = z.infer<typeof JobProgressSchema>;

/**
 * Represents an individual download task with state transitions and progress tracking.
 * Extends EventEmitter to notify subscribers about progress updates.
 */
export default class DownloadJob extends EventEmitter {
  private id: string;
  private streamUrl: StreamUrl;
  private outputPath: string;
  private title: string;
  private status: JobStatus = "queued";
  private progress: JobProgress = {
    percentage: 0,
    bytesDownloaded: 0,
  };
  private process: ChildProcess | null = null;
  private startTime: number = 0;

  /**
   * Create a new download job.
   * @param id - Unique identifier for the job
   * @param streamUrl - Direct stream URL to download
   * @param outputPath - Local file path to save the download
   * @param title - Human-readable title for the download
   */
  constructor(id: string, streamUrl: StreamUrl, outputPath: string, title: string) {
    super();
    this.id = id;
    this.streamUrl = streamUrl;
    this.outputPath = outputPath;
    this.title = title;
  }

  /**
   * Get the job ID.
   */
  getId(): string {
    return this.id;
  }

  /**
   * Get the current job status.
   */
  getStatus(): JobStatus {
    return this.status;
  }

  /**
   * Get the current progress.
   */
  getProgress(): JobProgress {
    return { ...this.progress };
  }

  /**
   * Start the download process using yt-dlp.
   * Emits 'progress' updates during download and 'complete' or 'error' when finished.
   */
  async start(): Promise<void> {
    if (this.status !== "queued" && this.status !== "paused") {
      throw new Error(`Cannot start job in status: ${this.status}`);
    }

    this.status = "downloading";
    this.startTime = Date.now();
    this.emit("statusChange", this.status);

    return new Promise((resolve, reject) => {
      // Spawn yt-dlp process
      // Using -o to specify output format, --newline for progress updates
      const proc = spawn("yt-dlp", [
        "--newline",
        "--progress-template", "progress:[%(percent).1f]",
        "-o", this.outputPath,
        this.streamUrl,
      ], {
        stdio: ["ignore", "pipe", "pipe"],
      });

      this.process = proc;

      let stderr = "";
      let stdout = "";

      proc.stdout.on("data", (data: Buffer) => {
        const output = data.toString();
        stdout += output;
        
        // Parse yt-dlp progress output
        // Format: progress:[xx.x]
        const progressMatch = output.match(/progress:\[([0-9]+\.?[0-9]*)\]/);
        if (progressMatch && progressMatch[1]) {
          const percentage = parseFloat(parseFloat(progressMatch[1]).toString());
          this.progress.percentage = Math.min(99.9, percentage);
          
          // Calculate speed and ETA if possible (yt-dlp doesn't provide these directly in simple format)
          // For now, we'll emit progress with what we have
          this.emit("progress", {
            ...this.progress,
            speed: this.calculateSpeed(),
            eta: this.calculateETA(),
          });
        }
      });

      proc.stderr.on("data", (data: Buffer) => {
        stderr += data.toString();
      });

      proc.on("error", (err) => {
        this.status = "failed";
        this.emit("statusChange", this.status);
        this.emit("error", new Error(`yt-dlp process error: ${err.message}`));
        reject(err);
      });

      proc.on("close", (code) => {
        this.process = null;
        
        if (code === 0) {
          this.status = "completed";
          this.status = "completed";
          this.progress.percentage = 100;
          this.emit("statusChange", this.status);
          this.emit("progress", { ...this.progress });
          this.emit("complete");
          resolve();
        } else if (this.status === "paused") {
          // Process was paused, not actually finished
          return;
        } else {
          this.status = "failed";
          this.emit("statusChange", this.status);
          this.emit("error", new Error(`yt-dlp exited with code ${code}: ${stderr.slice(-200)}`));
          reject(new Error(`yt-dlp exited with code ${code}`));
        }
      });
    });
  }

/**
    * Pause the download process by sending SIGSTOP to the child process.
    */
   pause(): void {
     if (!this.process || this.status !== "downloading") {
       return;
     }

     try {
       const pid = this.process.pid;
       if (pid === null || pid === undefined) {
         throw new Error("Process PID is not available");
       }
       process.kill(pid, "SIGSTOP");
       this.status = "paused";
       this.emit("statusChange", this.status);
     } catch (err) {
       // Process might have already ended
       this.status = "failed";
       this.emit("statusChange", this.status);
       this.emit("error", new Error(`Failed to pause process: ${err instanceof Error ? err.message : String(err)}`));
     }
   }

/**
    * Resume the download process by sending SIGCONT to the child process.
    */
   resume(): void {
     if (!this.process || this.status !== "paused") {
       return;
     }

     try {
       const pid = this.process.pid;
       if (pid === null || pid === undefined) {
         throw new Error("Process PID is not available");
       }
       process.kill(pid, "SIGCONT");
       this.status = "downloading";
       this.emit("statusChange", this.status);
     } catch (err) {
       // Process might have already ended
       this.status = "failed";
       this.emit("statusChange", this.status);
       this.emit("error", new Error(`Failed to resume process: ${err instanceof Error ? err.message : String(err)}`));
     }
   }

/**
    * Cancel the download process by terminating the child process.
    */
   cancel(): void {
     if (!this.process) {
       this.status = "cancelled";
       this.emit("statusChange", this.status);
       return;
     }

     try {
       const pid = this.process.pid;
       if (pid === null || pid === undefined) {
         throw new Error("Process PID is not available");
       }
       process.kill(pid, "SIGTERM");
       // Force kill after 5 seconds if still running
       setTimeout(() => {
         if (this.process && !this.process.killed) {
           const killPid = this.process.pid;
           if (killPid !== null && killPid !== undefined) {
             process.kill(killPid, "SIGKILL");
           }
         }
       }, 5000);
       
       this.status = "cancelled";
       this.emit("statusChange", this.status);
     } catch (err) {
       this.status = "failed";
       this.emit("statusChange", this.status);
       this.emit("error", new Error(`Failed to cancel process: ${err instanceof Error ? err.message : String(err)}`));
     }
   }

  /**
   * Calculate download speed based on progress and time elapsed.
   * @returns Speed string (e.g., "1.2 MB/s") or empty string if cannot calculate
   */
  private calculateSpeed(): string {
    if (this.progress.bytesDownloaded === 0 || this.startTime === 0) {
      return "";
    }

    const elapsedSeconds = (Date.now() - this.startTime) / 1000;
    if (elapsedSeconds <= 0) {
      return "";
    }

    // Since yt-dlp doesn't give us bytes directly in simple progress format,
    // we'll estimate based on percentage if we had total size
    // For now, return empty as we don't have byte count from simple progress
    return "";
  }

  /**
   * Calculate ETA based on progress and speed.
   * @returns ETA string (e.g., "02:30") or empty string if cannot calculate
   */
  private calculateETA(): string {
    // Without knowing total size or actual bytes downloaded, we can't calculate ETA accurately
    // yt-dlp's --progress-template doesn't easily give us ETA in machine-readable format
    // For a real implementation, we'd need to parse more detailed progress or use JSON format
    return "";
  }
}