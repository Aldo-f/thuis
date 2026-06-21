import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [url, setUrl] = useState("");

  function handleSearch(e: FormEvent) {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  }

  function handleUrlSubmit(e: FormEvent) {
    e.preventDefault();
    if (url.trim()) {
      // TODO: resolve episode ID from VRT MAX URL
      navigate(`/episode/unknown`);
    }
  }

  return (
    <div className="space-y-12">
      {/* Hero */}
      <section className="text-center">
        <h1 className="text-4xl font-bold tracking-tight text-stone-800 sm:text-5xl">
          Thuis
        </h1>
        <p className="mt-3 text-lg text-stone-500">
          Browse, search and download VRT MAX content.
        </p>
      </section>

      {/* Search bar */}
      <section className="mx-auto max-w-xl">
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
      </section>

      {/* URL paste */}
      <section className="mx-auto max-w-xl">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-stone-400">
          Or paste a VRT MAX URL
        </h2>
        <form onSubmit={handleUrlSubmit} className="flex gap-2">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.vrt.be/vrtmax/…"
            className="flex-1 rounded-lg border border-stone-300 px-4 py-2.5 text-sm outline-none transition-colors focus:border-stone-500 focus:ring-1 focus:ring-stone-500"
          />
          <button
            type="submit"
            className="rounded-lg border border-stone-300 px-5 py-2.5 text-sm font-medium text-stone-700 transition-colors hover:bg-stone-100"
          >
            Open
          </button>
        </form>
      </section>
    </div>
  );
}

export default Home;
