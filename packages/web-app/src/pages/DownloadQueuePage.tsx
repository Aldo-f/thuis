import { useState } from "react";

interface DownloadJob {
  id: string;
  episodeTitle: string;
  seriesTitle: string;
  progress: number;
  status: "pending" | "downloading" | "paused" | "completed" | "failed";
  fileSize?: string;
  error?: string;
}

// Placeholder — in production, this reads from Zustand store
const MOCK_JOBS: DownloadJob[] = [];

export default function DownloadQueuePage() {
  const [jobs] = useState<DownloadJob[]>(MOCK_JOBS);

  return (
    <div className="mx-auto max-w-2xl py-8">
      <h1 className="text-2xl font-bold text-stone-900">Downloadwachtrij</h1>
      <p className="mt-2 text-sm text-stone-500">
        Hier zie je de voortgang van je downloads.
      </p>

      {jobs.length === 0 && (
        <div className="mt-8 rounded-lg border border-dashed border-stone-300 p-12 text-center">
          <svg
            className="mx-auto h-12 w-12 text-stone-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="mt-4 text-sm font-medium text-stone-500">
            Geen downloads in de wachtrij
          </p>
          <p className="mt-1 text-sm text-stone-400">
            Download een aflevering via de kijkpagina om hem hier te zien.
          </p>
        </div>
      )}

      {jobs.length > 0 && (
        <div className="mt-6 space-y-3">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-stone-900">{job.episodeTitle}</h3>
                  <p className="text-sm text-stone-500">{job.seriesTitle}</p>
                </div>
                <span className={`text-sm font-medium ${
                  job.status === "completed" ? "text-green-600"
                  : job.status === "failed" ? "text-red-600"
                  : job.status === "paused" ? "text-amber-600"
                  : "text-blue-600"
                }`}>
                  {job.status === "downloading" && `${job.progress}%`}
                  {job.status === "pending" && "Wacht..."}
                  {job.status === "paused" && "Gepauzeerd"}
                  {job.status === "completed" && "Voltooid"}
                  {job.status === "failed" && "Mislukt"}
                </span>
              </div>
              {(job.status === "downloading" || job.status === "paused") && (
                <div className="mt-3">
                  <div className="h-2 w-full rounded-full bg-stone-200">
                    <div
                      className="h-2 rounded-full bg-stone-800 transition-all"
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                </div>
              )}
              {job.status === "failed" && job.error && (
                <p className="mt-2 text-sm text-red-600">{job.error}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
