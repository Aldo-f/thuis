/**
 * DownloadManager
 *
 * Manages a pool of {@link DownloadJob} instances with a configurable concurrency limit.
 * It provides a simple queue API: `add`, `pause`, `resume`, `cancel`, `retry`, `clear`.
 * Jobs are automatically started when a slot becomes free. Progress events from each
 * {@link DownloadJob} are re‑emitted on the manager instance allowing a single listener
 * to monitor overall activity.
 *
 * The manager can optionally persist its queue to a JSON file (default location `./download-queue.json`).
 * Persistence is useful for restarting the service without losing queued work. The
 * persisted format mirrors the constructor arguments of {@link DownloadJob}.
 *
 * @example
 * ```ts
 * const manager = new DownloadManager({ concurrency: 3, persistPath: './queue.json' })
 * manager.add({ url: 'https://example.com/video', format: 'mp4' })
 * manager.on('progress', ({ jobId, downloaded, total }) => {
 *   console.log(`Job ${jobId}: ${downloaded}/${total}`)
 * })
 * ```
 */

import { EventEmitter } from 'events'
import { promises as fs } from 'fs'
import path from 'path'
import { DownloadJob } from './DownloadJob.js'
import type { DownloadJobOptions, DownloadJobState } from './types.js'

/**
 * Options for constructing a {@link DownloadManager}.
 */
export interface DownloadManagerOptions {
  /** Maximum number of jobs running in parallel. Defaults to 2. */
  concurrency?: number
  /** Path to a JSON file used for persisting the queue. If omitted the manager is in‑memory only. */
  persistPath?: string
  /** If true the manager will load the persisted queue during construction. */
  loadOnStart?: boolean
}

/**
 * Internal representation of a queued item. It stores the original options used to
 * create the {@link DownloadJob} together with the current job instance (if any) and
 * its runtime state.
 */
interface QueueEntry {
  id: string
  options: DownloadJobOptions
  job?: DownloadJob
  state: DownloadJobState
}

/**
 * DownloadManager class – extends {@link EventEmitter} so callers can subscribe to
 * events emitted by any job in the queue.
 *
 * Emitted events (mirrored from {@link DownloadJob}):
 * - `progress` – `{ jobId, downloaded, total }`
 * - `completed` – `{ jobId, result }`
 * - `error` – `{ jobId, error }`
 * - `started` – `{ jobId }`
 * - `cancelled` – `{ jobId }`
 */
export class DownloadManager extends EventEmitter {
  private readonly concurrency: number
  private readonly persistPath?: string
  private queue: QueueEntry[] = []
  private activeCount = 0

  /**
   * Creates a new manager.
   * @param options Configuration for concurrency and persistence.
   */
  constructor(options: DownloadManagerOptions = {}) {
    super()
    this.concurrency = options.concurrency ?? 2
    if (options.persistPath) {
      this.persistPath = path.resolve(options.persistPath)
    }
    if (options.loadOnStart && this.persistPath) {
      void this.loadQueue().catch(err => this.emit('error', { jobId: 'manager', error: err }))
    }
  }

  /**
   * Adds a new download job to the queue and returns its generated identifier.
   */
  add(options: DownloadJobOptions): string {
    const id = `job-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`
    const entry: QueueEntry = { id, options, state: 'queued' }
    this.queue.push(entry)
    this.emit('added', { jobId: id, options })
    this.tryStartNext()
    this.persist().catch(() => {})
    return id
  }

  /** Pause a running or queued job. */
  pause(jobId: string): void {
    const entry = this.queue.find(e => e.id === jobId)
    if (!entry) return
    if (entry.job && entry.state === 'running') {
      entry.job.pause()
      entry.state = 'paused'
      this.emit('paused', { jobId })
    } else if (entry.state === 'queued') {
      entry.state = 'paused'
      this.emit('paused', { jobId })
    }
    this.persist().catch(() => {})
  }

  /** Resume a paused job. */
  resume(jobId: string): void {
    const entry = this.queue.find(e => e.id === jobId)
    if (!entry || entry.state !== 'paused') return
    entry.state = 'queued'
    this.emit('resumed', { jobId })
    this.tryStartNext()
    this.persist().catch(() => {})
  }

  /** Cancel a job – removes it from the queue and stops the underlying {@link DownloadJob}. */
  cancel(jobId: string): void {
    const index = this.queue.findIndex(e => e.id === jobId)
    if (index === -1) return
    const entry = this.queue[index]
    if (entry.job && entry.state === 'running') {
      entry.job.cancel()
    }
    this.queue.splice(index, 1)
    this.emit('cancelled', { jobId })
    this.tryStartNext()
    this.persist().catch(() => {})
  }

  /** Retry a completed/failed job – creates a fresh {@link DownloadJob} with the original options. */
  retry(jobId: string): void {
    const entry = this.queue.find(e => e.id === jobId)
    if (!entry) return
    // Reset state and delete old job reference
    entry.state = 'queued'
    entry.job = undefined
    this.emit('retried', { jobId })
    this.tryStartNext()
    this.persist().catch(() => {})
  }

  /** Remove all jobs from the queue (running jobs are cancelled). */
  clear(): void {
    // Cancel running jobs first
    for (const entry of this.queue) {
      if (entry.job && entry.state === 'running') {
        entry.job.cancel()
      }
    }
    this.queue = []
    this.activeCount = 0
    this.emit('cleared')
    this.persist().catch(() => {})
  }

  /** Returns a shallow copy of the current queue entries (for inspection). */
  getQueue(): ReadonlyArray<{ id: string; options: DownloadJobOptions; state: DownloadJobState }> {
    return this.queue.map(e => ({ id: e.id, options: e.options, state: e.state }))
  }

  /** Internal – tries to start jobs while respecting concurrency limits. */
  private tryStartNext(): void {
    while (this.activeCount < this.concurrency) {
      const next = this.queue.find(e => e.state === 'queued')
      if (!next) break
      this.startJob(next)
    }
  }

  /** Internal – starts a specific job and wires its events to the manager. */
  private startJob(entry: QueueEntry): void {
    const job = new DownloadJob(entry.options)
    entry.job = job
    entry.state = 'running'
    this.activeCount++
    this.emit('started', { jobId: entry.id })

    const forward = (event: string, payload: any) => {
      this.emit(event as any, { jobId: entry.id, ...payload })
    }
    job.on('progress', data => forward('progress', data))
    job.on('completed', data => forward('completed', data))
    job.on('error', err => forward('error', { error: err }))
    job.on('cancelled', () => forward('cancelled', {}))

    job.start().finally(() => {
      this.activeCount--
      entry.state = 'finished'
      this.tryStartNext()
      this.persist().catch(() => {})
    })
  }

  /** Persist the queue (excluding live job instances) to disk as JSON. */
  private async persist(): Promise<void> {
    if (!this.persistPath) return
    const data = this.queue.map(e => ({ id: e.id, options: e.options, state: e.state }))
    await fs.writeFile(this.persistPath, JSON.stringify(data, null, 2), 'utf-8')
  }

  /** Load a persisted queue from disk. */
  private async loadQueue(): Promise<void> {
    if (!this.persistPath) return
    try {
      const raw = await fs.readFile(this.persistPath, 'utf-8')
      const persisted: Array<{ id: string; options: DownloadJobOptions; state: DownloadJobState }> = JSON.parse(raw)
      // Re‑create entries – only queued or paused entries become active again
      this.queue = persisted.map(p => ({ id: p.id, options: p.options, state: p.state }))
      // Attempt to start any jobs that were left in queued state
      this.tryStartNext()
    } catch (e) {
      // If the file does not exist we simply start with an empty queue.
      if ((e as any).code !== 'ENOENT') {
        this.emit('error', { jobId: 'manager', error: e })
      }
    }
  }
}
