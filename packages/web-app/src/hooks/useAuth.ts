import { useState, useCallback } from "react";
import { ProviderRegistry } from "@thuis/core";

function getVrtAdapter() {
  const adapter = ProviderRegistry.getInstance().get('vrt');
  if (!adapter) {
    throw new Error('VRT adapter not registered in ProviderRegistry');
  }
  return adapter;
}
const authService = { get: getVrtAdapter };


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
    } catch (err: any) {
      const message = err?.message ?? "Onbekende fout bij inloggen.";
      setError(message);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await (getVrtAdapter() as any).logout();
    setIsLoggedIn(false);
  }, []);

  const getAccessToken = useCallback(async () => {
    try {
      return await (getVrtAdapter() as any).getAccessToken();
    } catch {
      setIsLoggedIn(false);
      return null;
    }
  }, []);

  return { isLoggedIn, isLoading, error, login, logout, getAccessToken, authService: getVrtAdapter() };
}
