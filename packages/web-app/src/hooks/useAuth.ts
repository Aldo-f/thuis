import { useState, useCallback } from "react";
import { ProviderRegistry } from "@thuis/core";

function getVrtAdapter() {
  const adapter = ProviderRegistry.getInstance().get('vrt');
  if (!adapter) {
    throw new Error('VRT adapter not registered in ProviderRegistry');
  }
  return adapter;
}

export function useAuth() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await getVrtAdapter().login({ username: email, password });
      setIsLoggedIn(true);
      return true;
    } catch (err: unknown) {
      const message = (err as Error)?.message ?? "Onbekende fout bij inloggen.";
      setError(message);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await getVrtAdapter().dispose();
    setIsLoggedIn(false);
  }, []);

  const getAccessToken = useCallback(async () => {
    try {
      const auth = new (await import("@thuis/core")).VrtAuthService();
      return await auth.getAccessToken();
    } catch {
      setIsLoggedIn(false);
      return null;
    }
  }, []);

  return { isLoggedIn, isLoading, error, login, logout, getAccessToken };
}
