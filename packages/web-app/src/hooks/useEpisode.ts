import { useState, useCallback } from "react";
import { VrtEpisodeService, VrtAuthService } from "@thuis/core";
import type { EpisodeDetail, StreamData } from "@thuis/core";

// Hook returns authService dependency — in production, inject via context
let episodeService: VrtEpisodeService | null = null;

function getService(auth: VrtAuthService): VrtEpisodeService {
  if (!episodeService) {
    episodeService = new VrtEpisodeService(auth);
  }
  return episodeService;
}

export function useEpisode(authService: VrtAuthService) {
  const [episode, setEpisode] = useState<EpisodeDetail | null>(null);
  const [stream, setStream] = useState<StreamData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEpisode = useCallback(async (url: string) => {
    setIsLoading(true);
    setError(null);
    setEpisode(null);
    setStream(null);
    try {
      const service = getService(authService);
      const ep = await service.getEpisode(url);
      setEpisode(ep);
      return ep;
    } catch (err: any) {
      setError(err?.message ?? "Kon aflevering niet ophalen.");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [authService]);

  const resolveStream = useCallback(async (streamId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const { StreamResolver } = await import("@thuis/core");
      const resolver = new StreamResolver(authService);
      const s = await resolver.resolveStream(streamId);
      setStream(s);
      return s;
    } catch (err: any) {
      setError(err?.message ?? "Kon stream niet oplossen.");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [authService]);

  return { episode, stream, isLoading, error, fetchEpisode, resolveStream };
}
