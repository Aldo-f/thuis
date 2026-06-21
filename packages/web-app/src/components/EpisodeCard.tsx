import { Link } from "react-router-dom";

interface EpisodeCardProps {
  title: string;
  season: number;
  episode: number;
  duration: string;
  thumbnailUrl?: string;
}

function EpisodeCard({ title, season, episode, duration, thumbnailUrl }: EpisodeCardProps) {
  return (
    <Link
      to={`/episode/${encodeURIComponent(title.toLowerCase().replace(/\s+/g, "-"))}`}
      className="group block overflow-hidden rounded-lg border border-stone-200 bg-white transition-shadow hover:shadow-md"
    >
      {/* Thumbnail */}
      <div className="aspect-video bg-stone-100">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-stone-300">
            <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3">
        <h3 className="truncate text-sm font-semibold text-stone-800 group-hover:text-stone-600">
          {title}
        </h3>
        <p className="mt-1 text-xs text-stone-400">
          S{season} &middot; E{episode} &middot; {duration}
        </p>
      </div>
    </Link>
  );
}

export default EpisodeCard;
