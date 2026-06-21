import { Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home.js";
import Search from "./pages/Search.js";
import EpisodeDetail from "./pages/EpisodeDetail.js";

function App() {
  return (
    <div className="flex min-h-screen flex-col bg-stone-50 text-stone-900">
      {/* Header */}
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <Link to="/" className="text-xl font-bold tracking-tight text-stone-800">
            Thuis
          </Link>
          <nav className="flex items-center gap-6 text-sm font-medium text-stone-500">
            <Link to="/" className="transition-colors hover:text-stone-800">
              Home
            </Link>
            <Link to="/search" className="transition-colors hover:text-stone-800">
              Search
            </Link>
          </nav>
        </div>
      </header>

      {/* Main layout: content + sidebar */}
      <div className="mx-auto flex w-full max-w-7xl flex-1 px-4 sm:px-6 lg:px-8">
        {/* Page content */}
        <main className="min-w-0 flex-1 py-6">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<Search />} />
            <Route path="/episode/:id" element={<EpisodeDetail />} />
          </Routes>
        </main>

        {/* Sidebar — download queue placeholder */}
        <aside className="ml-8 hidden w-72 shrink-0 lg:block">
          <div className="sticky top-4 rounded-lg border border-stone-200 bg-white p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-stone-400">
              Download Queue
            </h2>
            <p className="mt-3 text-sm text-stone-400">
              No downloads in progress.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default App;
