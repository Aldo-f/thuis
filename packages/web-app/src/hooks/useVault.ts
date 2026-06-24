import { useState, useCallback, useEffect, useRef } from "react";
import {
  CredentialVault,
  VaultLockedError,
  MissingPasswordError,
} from "@thuis/core";
import type { ProviderCredential } from "@thuis/core";

export type VaultState = "uninitialized" | "locked" | "unlocked";

interface StoredCredential {
  provider: string;
  email: string;
  isActive: boolean;
}

/** LocalStorage key that marks whether the vault has ever been set up. */
const VAULT_INIT_KEY = "thuis-vault-setup";

// Singleton vault instance — the in-memory state (locked/unlocked, decrypted cache)
// is shared across all hook consumers so they stay in sync.
const vault = new CredentialVault();

/**
 * React hook that wraps the {@link CredentialVault} service and exposes both
 * the original (localStorage‑based) API and the new vault‑centric API.
 *
 * **Backward‑compatible surface:** `vaultState`, `providers`, `error`,
 * `setup()`, `unlock()`, `lock()`, `addProvider()`, `removeProvider()`,
 * `resetVault()`, `clearError()`.
 *
 * **New API:** `isLocked`, `addCredentials()`, `getCredentials()`.
 */
export function useVault() {
  const [vaultState, setVaultState] = useState<VaultState>(() =>
    localStorage.getItem(VAULT_INIT_KEY) === "true" ? "locked" : "uninitialized",
  );
  const [providers, setProviders] = useState<StoredCredential[]>([]);
  const [error, setError] = useState<string | null>(null);
  const lockCheckTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Helpers ──────────────────────────────────────────────────────────

  /** Reload the provider list from the vault's in‑memory cache. */
  const refreshProviders = useCallback(() => {
    if (!vault.isLocked()) {
      try {
        const list = vault.listProviders();
        setProviders(
          list.map((p: { provider: string; email: string }) => ({ provider: p.provider, email: p.email, isActive: true })),
        );
      } catch {
        setProviders([]);
      }
    } else {
      setProviders([]);
    }
  }, []);

  // ── Lifecycle ────────────────────────────────────────────────────────

  // Sync React state with the vault when vaultState becomes unlocked.
  useEffect(() => {
    if (vaultState === "unlocked") {
      refreshProviders();
    } else {
      setProviders([]);
    }
  }, [vaultState, refreshProviders]);

  // Poll vault.isLocked() while unlocked so the UI reacts to auto‑lock.
  useEffect(() => {
    if (vaultState !== "unlocked") {
      if (lockCheckTimer.current) {
        clearInterval(lockCheckTimer.current);
        lockCheckTimer.current = null;
      }
      return;
    }
    lockCheckTimer.current = setInterval(() => {
      if (vault.isLocked()) {
        setVaultState("locked");
      }
    }, 2_000);
    return () => {
      if (lockCheckTimer.current) {
        clearInterval(lockCheckTimer.current);
        lockCheckTimer.current = null;
      }
    };
  }, [vaultState]);

  // ── Public API ───────────────────────────────────────────────────────

  /**
   * First‑time setup.
   * Delegates to `vault.unlock(password)` which creates an empty encrypted
   * blob when none exists yet.
   */
  const setup = useCallback(async (password: string) => {
    try {
      await vault.unlock(password);
      localStorage.setItem(VAULT_INIT_KEY, "true");
      setVaultState("unlocked");
      setError(null);
    } catch (e) {
      if (e instanceof MissingPasswordError) {
        setError("Wachtwoord vereist");
      } else {
        setError("Er is een fout opgetreden bij het aanmaken van de vault.");
      }
    }
  }, []);

  /**
   * Unlock the vault with the master password.
   * Returns `true` on success, `false` on wrong password / error.
   */
  const unlock = useCallback(async (password: string): Promise<boolean> => {
    try {
      await vault.unlock(password);
      setVaultState("unlocked");
      setError(null);
      return true;
    } catch (e) {
      if (e instanceof VaultLockedError) {
        setError("Ongeldig hoofdwachtwoord.");
      } else if (e instanceof MissingPasswordError) {
        setError("Wachtwoord vereist.");
      } else {
        setError("Er is een fout opgetreden bij het ontgrendelen.");
      }
      return false;
    }
  }, []);

  /** Lock the vault. */
  const lock = useCallback(() => {
    vault.lock();
    setVaultState("locked");
    setError(null);
  }, []);

  /**
   * Add or update credentials for a provider.
   * (Original API – kept for backward compatibility.)
   */
  const addProvider = useCallback(
    async (provider: string, email: string, password: string) => {
      try {
        await vault.addCredentials(provider, email, password);
        refreshProviders();
        setError(null);
      } catch (e) {
        if (e instanceof VaultLockedError) {
          setError("Vault is vergrendeld.");
        } else {
          setError("Fout bij opslaan van inloggegevens.");
        }
      }
    },
    [refreshProviders],
  );

  /**
   * Remove credentials for a provider.
   * (Original API – kept for backward compatibility.)
   */
  const removeProvider = useCallback(
    async (provider: string) => {
      try {
        await vault.removeCredentials(provider);
        refreshProviders();
        setError(null);
      } catch (e) {
        if (e instanceof VaultLockedError) {
          setError("Vault is vergrendeld.");
        } else {
          setError("Fout bij verwijderen van inloggegevens.");
        }
      }
    },
    [refreshProviders],
  );

  /**
   * Reset the vault – destroys all stored data and returns to
   * the "uninitialized" screen.
   */
  const resetVault = useCallback(() => {
    vault.lock();
    // Delete the entire IndexedDB database so a fresh vault starts clean.
    try {
      const req = indexedDB.deleteDatabase("credential-vault");
      req.onerror = () => {
        /* ignore – will be re‑created on next setup */
      };
    } catch {
      /* noop in non‑browser environments */
    }
    localStorage.removeItem(VAULT_INIT_KEY);
    setVaultState("uninitialized");
    setProviders([]);
    setError(null);
  }, []);

  /** Clear any displayed error. */
  const clearError = useCallback(() => setError(null), []);

  // ── New API surface ──────────────────────────────────────────────────

  /**
   * Retrieve stored credentials for a provider (including the decrypted
   * password, only available in memory). Returns `null` if not found or
   * when vault is locked.
   */
  const getCredentials = useCallback(
    (provider: string): ProviderCredential | null => {
      try {
        return vault.getCredentials(provider);
      } catch {
        return null;
      }
    },
    [],
  );

  /**
   * Alias for {@link addProvider} — new API name.
   */
  const addCredentials = addProvider;

  // ── Return ───────────────────────────────────────────────────────────

  const isLocked = vaultState !== "unlocked";

  return {
    // Legacy API (stable)
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
    // New API
    isLocked,
    getCredentials,
    addCredentials,
  };
}
