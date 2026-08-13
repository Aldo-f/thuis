import { spawn, ChildProcess } from "node:child_process";
import { unlink } from "node:fs";
import { Notification } from "electron";
// Removed unused imports: createWriteStream, join, app

interface DownloadJob {
  id: string;
  streamUrl: string;
  outputPath: string;
  title: string;
  process: ChildProcess | null;
  status: "pending" | "downloading" | "paused" | "completed" | "failed" | "cancelled";
  progress: number;
  error?: string;
}

type ProgressCallback = (jobId: string, progress: number, status: string) => void;

export class DownloadEngine {
  private jobs = new Map<string, DownloadJob>();
  private progressCallbacks: ProgressCallback[] = [];
  private jobCounter = 0;

  onProgress(cb: ProgressCallback): void {
    this.progressCallbacks.push(cb);
  }

  /**
   * Start downloading an HLS stream via FFmpeg.
   * Returns the job ID.
   */
  async startDownload(
    streamUrl: string,
    outputPath: string,
    title: string,
  ): Promise<string> {
    const jobId = `dl-${++this.jobCounter}`;

    const job: DownloadJob = {
      id: jobId,
      streamUrl,
      outputPath,
      title,
      process: null,
      status: "pending",
      progress: 0,
    };

    this.jobs.set(jobId, job);

    // Check if ffmpeg is available
    try {
      await this.checkFfmpeg();
    } catch {
      job.status = "failed";
      job.error = "FFmpeg is niet geïnstalleerd. Installeer FFmpeg via je package manager.";
      this.emitProgress(jobId, 0, "failed");
      return jobId;
    }

    // Start download
    setImmediate(() => this.runDownload(jobId));
    return jobId;
  }

  cancelDownload(jobId: string): void {
    const job = this.jobs.get(jobId);
    if (!job) return;

    if (job.process) {
      job.process.kill("SIGTERM");
      setTimeout(() => {
        if (job.process && !job.process.killed) {
          job.process.kill("SIGKILL");
        }
      }, 5000);
    }

    // Clean up partial file
    job.status = "cancelled";
    this.emitProgress(jobId, 0, "cancelled");
    unlink(job.outputPath, () => {}); // ignore error
  }

  getJob(jobId: string): DownloadJob | undefined {
    return this.jobs.get(jobId);
  }

  getAllJobs(): DownloadJob[] {
    return Array.from(this.jobs.values());
  }

  private async runDownload(jobId: string): Promise<void> {
    const job = this.jobs.get(jobId);
    if (!job) return;

    job.status = "downloading";
    this.emitProgress(jobId, 0, "downloading");

    try {
      const result = await this.spawnFfmpeg(job);
      if (result.success) {
        job.status = "completed";
        job.progress = 100;
        this.emitProgress(jobId, 100, "completed");
        this.showNotification(job.title);
      } else {
        job.status = "failed";
        job.error = result.error;
        this.emitProgress(jobId, 0, "failed");
      }
    } catch (err: unknown) {
      job.status = "failed";
      job.error = err instanceof Error ? err.message : String(err);
      this.emitProgress(jobId, 0, "failed");
    }
  }

  private spawnFfmpeg(
    job: DownloadJob,
  ): Promise<{ success: boolean; error?: string }> {
    return new Promise((resolve) => {
      const args = [
        "-y",
        "-i", job.streamUrl,
        "-c", "copy",
        "-progress", "pipe:1",
        "-stats_period", "1",
        job.outputPath,
      ];

      const proc = spawn("ffmpeg", args, {
        stdio: ["ignore", "pipe", "pipe"],
      });

      job.process = proc;

      let stderr = "";

      proc.stdout?.on("data", (data: Buffer) => {
        const output = data.toString();
        // FFmpeg progress output: "out_time=... speed=..."
        const timeMatch = output.match(/out_time=(\d+):(\d+):(\d+)\.(\d+)/);
        if (timeMatch) {
          const hours = parseInt(timeMatch[1]!, 10);
          const minutes = parseInt(timeMatch[2]!, 10);
          const seconds = parseInt(timeMatch[3]!, 10);
          const currentSeconds = hours * 3600 + minutes * 60 + seconds;
          // Estimate duration from stream metadata — use progress as relative
          job.progress = Math.min(99, Math.round((currentSeconds / 3600) * 100));
          this.emitProgress(job.id, job.progress, "downloading");
        }
      });

      proc.stderr?.on("data", (data: Buffer) => {
        stderr += data.toString();
      });

      proc.on("error", (err) => {
        resolve({ success: false, error: err.message });
      });

      proc.on("close", (code) => {
        if (code === 0) {
          resolve({ success: true });
        } else if (job.status === "cancelled") {
          resolve({ success: false, error: "Geannuleerd." });
        } else {
          resolve({ success: false, error: `FFmpeg exit code ${code}: ${stderr.slice(-200)}` });
        }
      });
    });
  }

  private checkFfmpeg(): Promise<void> {
    return new Promise((resolve, reject) => {
      const proc = spawn("ffmpeg", ["-version"], { stdio: "pipe" });
      proc.on("error", () => reject(new Error("FFmpeg not found")));
      proc.on("close", (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error("FFmpeg not found"));
        }
      });
    });
  }

  private emitProgress(jobId: string, progress: number, status: string): void {
    for (const cb of this.progressCallbacks) {
      cb(jobId, progress, status);
    }
  }

  private showNotification(title: string): void {
    if (Notification.isSupported()) {
      const notif = new Notification({
        title: "Download voltooid",
        body: `"${title}" is gedownload.`,
      });
      notif.show();
    }
  }
}
