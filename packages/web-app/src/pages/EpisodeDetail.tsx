import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import { useEpisode } from "../hooks/useEpisode.js";
import { useVault } from "../hooks/useVault.js";
import { ProviderRegistry } from "@thuis/core";
import type { EpisodeDetail, StreamData } from "@thuis/core";
import type { Hls } from "hls.js";

type PageState = "loading" | "error" | "metadata" | "stream" | "playing";

function formatTime(t: number) {
  if (!isFinite(t)) return "0:00";
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function EpisodeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { authService } = useAuth();
  const { episode, isLoading, error, fetchEpisode } = useEpisode(authService);
  const vault = useVault();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [pageState, setPageState] = useState<PageState>("loading");
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [stream, setStream] = useState<StreamData | null>(null);
  const [showTechDetails, setShowTechDetails] = useState(false);
  const hlsRef = useRef<Hls | null>(null);

  const episodeUrl = id
    ? `https://www.vrt.be/vrtmax/a-z/${id.replace(/-/g, "/")}/`
    : "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6105/";

  useEffect(() => {
    loadEpisode();
  }, [id]);

  async function loadEpisode() {
    setPageState("loading");
    setStream(null);
    const ep = await fetchEpisode(episodeUrl);
    if (!ep) {
      setPageState("error");
      return;
    }
    setPageState("metadata");

    // Resolve stream via provider adapter with vault credentials
    try {
      const adapter = ProviderRegistry.getInstance().get("vrt");
      if (!adapter) {
        setPageState("error");
        return;
      }

      // Fetch credentials from vault before stream resolution
      try {
        const creds = vault.getCredentials("vrt");
        if (creds) {
          await adapter.login({ username: creds.email, password: creds.password });
        }
      } catch {
        // Vault locked of login mislukt — adapter heeft mogelijk al geldige tokens
      }

      const s = await adapter.resolveStream(ep);
      setStream(s);
      setPageState("stream");
      if (s.code) {
        setPageState("error");
      }
    } catch {
      setPageState("error");
    }
  }

  useEffect(() => {
    if (stream && stream.targetUrls.length > 0 && !stream.drm && videoRef.current) {
      const hlsUrl = stream.targetUrls.find((t: { type: string }) => t.type === "hls" || t.type === "hls_aes");
      if (hlsUrl) {
        loadHlsStream(hlsUrl.url);
      }
    }
  }, [stream]);

  async function loadHlsStream(url: string) {
    try {
      const Hls = (await import("hls.js")).default;
      if (Hls.isSupported() && videoRef.current) {
        const hls = new Hls();
        hlsRef.current = hls;
        hls.loadSource(url);
        hls.attachMedia(videoRef.current);
        hls.on(Hls.Events.MANIFEST_PARSED, () => setPageState("playing"));
        hls.on(Hls.Events.ERROR, () => {
          setPageState("error");
        });
      } else if (videoRef.current?.canPlayType("application/vnd.apple.mpegurl")) {
        videoRef.current.src = url;
        setPageState("playing");
      }
    } catch {
      setPageState("error");
    }
  }

  const togglePlay = useCallback(() => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  }, []);

  const handleTimeUpdate = useCallback(() => {
    if (!videoRef.current) return;
    setCurrentTime(videoRef.current.currentTime);
    setDuration(videoRef.current.duration || 0);
  }, []);

  const handleSeek = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (videoRef.current) videoRef.current.currentTime = time;
    setCurrentTime(time);
  }, []);

  const handleVolumeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const v = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.volume = v;
    }
    setVolume(v);
    setIsMuted(v === 0);
  }, []);

  const toggleMute = useCallback(() => {
    if (!videoRef.current) return;
    videoRef.current.muted = !videoRef.current.muted;
    setIsMuted(videoRef.current.muted);
  }, []);

  const toggleFullscreen = useCallback(async () => {
    if (!videoRef.current) return;
    if (document.fullscreenElement) {
      await document.exitFullscreen();
      setIsFullscreen(false);
    } else {
      await videoRef.current.requestFullscreen();
      setIsFullscreen(true);
    }
  }, []);

  const handleSpeed = useCallback((rate: number) => {
    if (videoRef.current) videoRef.current.playbackRate = rate;
    setPlaybackRate(rate);
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (pageState !== "playing") return;
      switch (e.key) {
        case " ": e.preventDefault(); togglePlay(); break;
        case "f": case "F": toggleFullscreen(); break;
        case "m": case "M": toggleMute(); break;
        case "ArrowLeft": if (videoRef.current) videoRef.current.currentTime -= 10; break;
        case "ArrowRight": if (videoRef.current) videoRef.current.currentTime += 10; break;
        case "ArrowUp": if (videoRef.current) videoRef.current.volume = Math.min(1, videoRef.current.volume + 0.1); break;
        case "ArrowDown": if (videoRef.current) videoRef.current.volume = Math.max(0, videoRef.current.volume - 0.1); break;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [pageState, togglePlay, toggleFullscreen, toggleMute]);

  useEffect(() => {
    return () => { hlsRef.current?.destroy(); };
  }, []);

  // --- Render ---

  if (pageState === "loading" || isLoading) {
    return (
      <div className="mx-auto max-w-4xl py-8">
        <div className="aspect-video animate-pulse rounded-lg bg-stone-200" />
        <div className="mt-4 space-y-3">
          <div className="h-6 w-3/4 animate-pulse rounded bg-stone-200" />
          <div className="h-4 w-1/2 animate-pulse rounded bg-stone-200" />
          <div className="h-20 animate-pulse rounded bg-stone-200" />
        </div>
      </div>
    );
  }

  if (pageState === "error") {
    return (
      <div className="mx-auto max-w-4xl py-8">
        <div className="rounded-lg border border-red-200 bg-red-50 p-8 text-center">
          <p className="text-lg font-medium text-red-800">
            {error || "Deze video kan niet worden geladen."}
          </p>
          {stream?.drm && (
            <p className="mt-2 text-sm text-red-600">
              Deze video is beveiligd en kan niet worden afgespeeld.
            </p>
          )}
          {stream?.code === "CONTENT_AVAILABLE_ONLY_FOR_BE_RESIDENTS" && (
            <p className="mt-2 text-sm text-red-600">
              Deze video is enkel beschikbaar in België.
            </p>
          )}
          <button
            onClick={loadEpisode}
            className="mt-4 rounded-lg bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700"
          >
            Probeer opnieuw
          </button>
        </div>
      {showTechDetails && stream && (
        <div className="mt-4 rounded-lg border border-stone-200 bg-stone-50 p-4 text-xs text-stone-500 font-mono">
          {stream.targetUrls.filter((t: { type: string }) => t.type === "hls" || t.type === "hls_aes").map((t: { type: string; url: string }, i: number) => (
            <div key={i} className="mb-1">
              <span className="font-semibold text-stone-600">HLS-URL:</span>{" "}
              <a href={t.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 break-all">
                {t.url}
              </a>
            </div>
          ))}
          {stream.drm && <p className="text-amber-600">DRM-beveiliging actief</p>}
          {stream.code && <p className="text-red-600">Code: {stream.code}</p>}
        </div>
      )}

      {episode && <EpisodeMetadata episode={episode} providerName="VRT MAX" />}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl py-8">
      {/* Player */}
      <div className="group relative overflow-hidden rounded-lg bg-black">
        <video
          ref={videoRef}
          className="aspect-video w-full"
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleTimeUpdate}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onClick={togglePlay}
          playsInline
        />

        {/* Controls — visible on hover or always when playing */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent p-4 opacity-0 transition-opacity group-hover:opacity-100">
          <input
            type="range"
            min={0}
            max={duration || 100}
            value={currentTime}
            onChange={handleSeek}
            className="player-seekbar mb-2 h-1 w-full cursor-pointer appearance-none rounded-full bg-white/30 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white"
          />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button onClick={togglePlay} className="text-white hover:text-stone-300">
                {isPlaying ? (
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" /></svg>
                ) : (
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
                )}
              </button>
              <span className="text-sm text-white/80">{formatTime(currentTime)} / {formatTime(duration)}</span>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={toggleMute} className="text-white hover:text-stone-300">
                {isMuted || volume === 0 ? (
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51A8.796 8.796 0 0021 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06a8.99 8.99 0 003.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" /></svg>
                ) : (
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" /></svg>
                )}
              </button>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={isMuted ? 0 : volume}
                onChange={handleVolumeChange}
                className="h-1 w-20 cursor-pointer appearance-none rounded-full bg-white/30 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white"
              />
              <select
                value={playbackRate}
                onChange={(e) => handleSpeed(parseFloat(e.target.value))}
                className="rounded bg-white/20 px-2 py-0.5 text-xs text-white"
              >
                {[0.5, 0.75, 1, 1.25, 1.5, 2].map(r => (
                  <option key={r} value={r} className="text-stone-900">{r}x</option>
                ))}
              </select>
              {stream && !stream.drm && (
                <button
                  onClick={() => setShowTechDetails((v) => !v)}
                  className="flex items-center gap-1 rounded bg-white/20 px-2 py-1 text-xs text-white hover:bg-white/30"
                  title={showTechDetails ? "Technische details verbergen" : "Technische details tonen"}
                >
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 15.5A3.5 3.5 0 0 1 8.5 12 3.5 3.5 0 0 1 12 8.5a3.5 3.5 0 0 1 3.5 3.5 3.5 3.5 0 0 1-3.5 3.5zm7.43-2.53c.76-1 .76-2.47 0-3.47l-1.21-1.58.34-2.06c.13-.8-.14-1.57-.7-2.06s-1.24-.72-2.02-.56l-2.01.47-1.69-1.19c-.9-.65-2.11-.65-3.02 0l-1.69 1.19-2.01-.47c-.78-.16-1.59.07-2.02.56s-.83 1.26-.7 2.06l.34 2.06L4.57 9.5c-.76 1-.76 2.47 0 3.47l1.21 1.58-.34 2.06c-.13.8.14 1.57.7 2.06s1.24.72 2.02.56l2.01-.47 1.69 1.19c.45.32.98.48 1.51.48s1.06-.16 1.51-.48l1.69-1.19 2.01.47c.78.16 1.59-.07 2.02-.56s.83-1.26.7-2.06l-.34-2.06 1.21-1.58z"/></svg>
                  {showTechDetails ? "Details verbergen" : "Technische details"}
                </button>
              )}
              <button onClick={toggleFullscreen} className="text-white hover:text-stone-300">
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" /></svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      {episode && <EpisodeMetadata episode={episode} />}
    </div>
  );
}

function EpisodeMetadata({ episode, providerName }: { episode: EpisodeDetail; providerName?: string }) {
  return (
    <div className="mt-6">
      <Link to={`/search?q=${encodeURIComponent(episode.seriesTitle)}`} className="text-sm text-stone-500 hover:text-stone-700">
        ← {episode.seriesTitle}
      </Link>
      <h1 className="mt-1 text-2xl font-bold text-stone-900">{episode.title}</h1>
      <p className="mt-1 text-sm text-stone-500">
        {providerName && <span className="font-medium">{providerName}</span>}
        {providerName && <span className="mx-1.5">•</span>}
        Seizoen {episode.season} • Aflevering {episode.episode}
        {episode.brand && <> • <span className="capitalize">{episode.brand}</span></>}
        {episode.airedAt && <> • {new Date(episode.airedAt).toLocaleDateString("nl-BE")}</>}
      </p>
      {episode.description && <p className="mt-4 text-stone-600">{episode.description}</p>}
      {episode.durationSeconds && (
        <p className="mt-2 text-sm text-stone-400">Duur: {Math.floor(episode.durationSeconds / 60)} minuten</p>
      )}
    </div>
  );
}
