import { useState, useCallback } from "react";
import { VrtAuthService, InMemoryTokenStorage } from "@thuis/core";

const authService = new VrtAuthService({
  storage: new InMemoryTokenStorage(),
});

export function useAuth() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await authService.login({ email, password });
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
    await authService.logout();
    setIsLoggedIn(false);
  }, []);

  const getAccessToken = useCallback(async () => {
    try {
      return await authService.getAccessToken();
    } catch {
      setIsLoggedIn(false);
      return null;
    }
  }, []);

  return { isLoggedIn, isLoading, error, login, logout, getAccessToken, authService };
}
