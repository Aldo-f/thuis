import { useState, useCallback, useEffect } from "react";

export type VaultState = "uninitialized" | "locked" | "unlocked";

interface StoredCredential {
  provider: string;
  email: string;
  isActive: boolean;
}

// Simulated vault — in production this uses crypto.subtle + IndexedDB
const VAULT_KEY = "thuis-vault-state";

function getStoredState(): VaultState {
  const raw = localStorage.getItem(VAULT_KEY);
  if (!raw) return "uninitialized";
  try {
    const state = JSON.parse(raw);
    return state.locked === false ? "unlocked" : "locked";
  } catch {
    return "uninitialized";
  }
}

export function useVault() {
  const [vaultState, setVaultState] = useState<VaultState>(getStoredState);
  const [providers, setProviders] = useState<StoredCredential[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Load providers when vault unlocks
  useEffect(() => {
    if (vaultState === "unlocked") {
      try {
        const raw = localStorage.getItem("thuis-providers");
        if (raw) {
          setProviders(JSON.parse(raw));
        }
      } catch {
        setProviders([]);
      }
    }
  }, [vaultState]);

  const setup = useCallback(async (password: string) => {
    // In production: derive key with PBKDF2, store encrypted blob
    localStorage.setItem(VAULT_KEY, JSON.stringify({ locked: false, hint: "" }));
    localStorage.setItem("thuis-providers", JSON.stringify([]));
    setVaultState("unlocked");
    setProviders([]);
    setError(null);
  }, []);

  const unlock = useCallback(async (password: string) => {
    // In production: attempt to decrypt, if fails → wrong password
    const raw = localStorage.getItem(VAULT_KEY);
    if (!raw) {
      setError("Geen vault gevonden. Start opnieuw met een nieuw wachtwoord.");
      return false;
    }
    // Password check simulation — in production this tries AES-GCM decryption
    if (password.length < 3) {
      // Simulated wrong password
      setError("Ongeldig hoofdwachtwoord.");
      return false;
    }
    localStorage.setItem(VAULT_KEY, JSON.stringify({ locked: false }));
    setVaultState("unlocked");
    setError(null);
    return true;
  }, []);

  const lock = useCallback(() => {
    localStorage.setItem(VAULT_KEY, JSON.stringify({ locked: true }));
    setVaultState("locked");
    setError(null);
  }, []);

  const addProvider = useCallback(async (
    provider: string,
    email: string,
    _password: string,
  ) => {
    // In production: encrypt and store in vault
    const updated = [...providers.filter((p) => p.provider !== provider), { provider, email, isActive: true }];
    setProviders(updated);
    localStorage.setItem("thuis-providers", JSON.stringify(updated));
  }, [providers]);

  const removeProvider = useCallback((provider: string) => {
    const updated = providers.filter((p) => p.provider !== provider);
    setProviders(updated);
    localStorage.setItem("thuis-providers", JSON.stringify(updated));
  }, [providers]);

  const resetVault = useCallback(() => {
    localStorage.removeItem(VAULT_KEY);
    localStorage.removeItem("thuis-providers");
    setVaultState("uninitialized");
    setProviders([]);
    setError(null);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return {
    vaultState,
    providers,
    error,
    setup,
    unlock,
    lock,
    addProvider,
    removeProvider,
    resetVault,
    clearError,
  };
}
