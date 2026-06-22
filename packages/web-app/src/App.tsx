import { Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home.js";
import Search from "./pages/Search.js";
import EpisodeDetailPage from "./pages/EpisodeDetail.js";
import VaultPage from "./pages/VaultPage.js";
import DownloadQueuePage from "./pages/DownloadQueuePage.js";

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
              Zoeken
            </Link>
            <Link to="/queue" className="transition-colors hover:text-stone-800">
              Downloads
            </Link>
            <Link to="/vault" className="transition-colors hover:text-stone-800">
              Inloggen
            </Link>
          </nav>
        </div>
      </header>

      {/* Main layout */}
      <div className="mx-auto flex w-full max-w-7xl flex-1 px-4 sm:px-6 lg:px-8">
        <main className="min-w-0 flex-1 py-6">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<Search />} />
            <Route path="/episode/:id" element={<EpisodeDetailPage />} />
            <Route path="/queue" element={<DownloadQueuePage />} />
            <Route path="/vault" element={<VaultPage />} />
          </Routes>
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-stone-200 bg-white py-4 text-center text-xs text-stone-400">
        Thuis — Bekijk en download VRT MAX content
      </footer>
    </div>
  );
}

export default App;
