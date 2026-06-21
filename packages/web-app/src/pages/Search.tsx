import { useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import EpisodeCard from "../components/EpisodeCard.js";

function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const currentQuery = searchParams.get("q") ?? "";
  const [query, setQuery] = useState(currentQuery);

  function handleSearch(e: FormEvent) {
    e.preventDefault();
    if (query.trim()) {
      setSearchParams({ q: query.trim() });
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search episodes…"
          className="flex-1 rounded-lg border border-stone-300 px-4 py-2.5 text-sm outline-none transition-colors focus:border-stone-500 focus:ring-1 focus:ring-stone-500"
        />
        <button
          type="submit"
          className="rounded-lg bg-stone-800 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-stone-700"
        >
          Search
        </button>
      </form>

      {currentQuery ? (
        <div>
          <p className="text-sm text-stone-500">
            Results for &ldquo;{currentQuery}&rdquo;
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <EpisodeCard
              title="Example Episode"
              season={1}
              episode={1}
              duration="45 min"
              thumbnailUrl={undefined}
            />
          </div>
        </div>
      ) : (
        <p className="text-center text-stone-400">
          Enter a search term to find episodes.
        </p>
      )}
    </div>
  );
}

export default Search;
