import { useState, useCallback } from "react";
import { ProviderRegistry, VrtAuthService } from "@thuis/core";
import type { EpisodeDetail, StreamData } from "@thuis/core";

// Hook returns authService dependency — in production, inject via context

function getVrtAdapter() {
  const provider = ProviderRegistry.getInstance().get('vrt');
  if (!provider) {
    throw new Error('VRT provider is not registered.');
  }
  return provider;
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
      const provider = getVrtAdapter();
      const ep = await provider.getEpisode(url);
      setEpisode(ep);
      return ep;
    } catch (err: unknown) {
      setError((err as Error)?.message ?? "Kon aflevering niet ophalen.");
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
    } catch (err: unknown) {
      setError((err as Error)?.message ?? "Kon stream niet oplossen.");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [authService]);

  return { episode, stream, isLoading, error, fetchEpisode, resolveStream };
}
