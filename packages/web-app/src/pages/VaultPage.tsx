import { useState, useEffect } from "react";
import ProviderList from "../components/vault/ProviderCard.js";
import ProviderCredentialForm from "../components/vault/ProviderCredentialForm.js";
import { useVault } from "../hooks/useVault.js";
import { ProviderRegistry } from "@thuis/core";



function maskEmail(email: string): string {
  const [name, domain] = email.split("@");
  if (!name || !domain) return email;
  const visible = name.slice(0, 3);
  return `${visible}***@${domain}`;
}

export default function VaultPage() {
  const {
    vaultState, providers, error,
    setup, unlock, lock, resetVault, clearError,
    addProvider, removeProvider, getCredentials,
  } = useVault();

  const [masterPassword, setMasterPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // Provider form state
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [providerEmail, setProviderEmail] = useState("");
  const [providerPassword, setProviderPassword] = useState("");
  const [showAddPicker, setShowAddPicker] = useState(false);

  // Pre-fill form when editing an existing provider
  useEffect(() => {
    if (!selectedProvider) return;
    const creds = getCredentials(selectedProvider);
    if (creds) {
      setProviderEmail(creds.email);
      setProviderPassword(creds.password ?? "");
    } else {
      setProviderEmail("");
      setProviderPassword("");
    }
  }, [selectedProvider, getCredentials]);

  // Reset confirmation
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [, /* unused masterPassword for locked state */] = useState("");

  // ── Provider list callbacks ──
  const handleEditProvider = (providerId: string) => {
    setShowAddPicker(false);
    setSelectedProvider(providerId);
  };

  const handleRemoveProvider = async (providerId: string) => {
    await removeProvider(providerId);
  };

  const handleFormSubmit = () => {
    setSelectedProvider(null);
    setProviderEmail("");
    setProviderPassword("");
  };

  const handleFormCancel = () => {
    setSelectedProvider(null);
    setShowAddPicker(false);
    setProviderEmail("");
    setProviderPassword("");
  };

  // ── Uninitialized vault — create master password ──
  if (vaultState === "uninitialized") {
    const isValid = masterPassword.length >= 8 && masterPassword === confirmPassword;

    return (
      <div className="mx-auto max-w-md py-12">
        <div className="rounded-lg border border-stone-200 bg-white p-8 shadow-sm">
          <h1 className="text-2xl font-bold text-stone-900">
            Welkom bij Thuis
          </h1>
          <p className="mt-2 text-sm text-stone-500">
            Maak een hoofdwachtwoord aan om je inloggegevens voor providers veilig op te slaan.
          </p>

          {error && (
            <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-stone-700">
                Hoofdwachtwoord
              </label>
              <div className="relative mt-1">
                <input
                  type={showPassword ? "text" : "password"}
                  value={masterPassword}
                  onChange={(e) => { setMasterPassword(e.target.value); clearError(); }}
                  className="block w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-stone-400 focus:outline-none focus:ring-2 focus:ring-stone-400"
                  placeholder="Minimaal 8 tekens"
                  minLength={8}
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-stone-700">
                Herhaal wachtwoord
              </label>
              <input
                type={showPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-stone-400 focus:outline-none focus:ring-2 focus:ring-stone-400"
                placeholder="Herhaal het wachtwoord"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-stone-500">
              <input
                type="checkbox"
                checked={showPassword}
                onChange={() => setShowPassword(!showPassword)}
                className="rounded border-stone-300"
              />
              Toon wachtwoord
            </label>

            <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
              ⚠ Dit wachtwoord kan niet worden hersteld. Verlies je het, dan ben je
              al je opgeslagen inloggegevens kwijt.
            </div>

            <button
              onClick={() => setup(masterPassword)}
              disabled={!isValid}
              className="w-full rounded-lg bg-stone-800 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Vault aanmaken
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Locked vault — enter master password ──
  if (vaultState === "locked") {
    return (
      <div className="mx-auto max-w-md py-12">
        <div className="rounded-lg border border-stone-200 bg-white p-8 shadow-sm">
          <h1 className="text-2xl font-bold text-stone-900">
            Vault ontgrendelen
          </h1>
          <p className="mt-2 text-sm text-stone-500">
            Voer je hoofdwachtwoord in om toegang te krijgen tot je opgeslagen inloggegevens.
          </p>

          {error && (
            <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="mt-6 space-y-4">
            <input
              type="password"
              value={masterPassword}
              onChange={(e) => { setMasterPassword(e.target.value); clearError(); }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && masterPassword.length > 0) {
                  unlock(masterPassword);
                }
              }}
              className="block w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-stone-400 focus:outline-none focus:ring-2 focus:ring-stone-400"
              placeholder="Hoofdwachtwoord"
              autoFocus
            />
            <button
              onClick={() => unlock(masterPassword)}
              disabled={masterPassword.length === 0}
              className="w-full rounded-lg bg-stone-800 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Ontgrendelen
            </button>

            <button
              onClick={() => setShowResetConfirm(true)}
              className="w-full text-sm text-stone-400 underline transition-colors hover:text-stone-600"
            >
              Wachtwoord vergeten?
            </button>
          </div>

          {showResetConfirm && (
            <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4">
              <p className="text-sm font-medium text-red-800">
                Alle opgeslagen inloggegevens zullen verloren gaan.
              </p>
              <p className="mt-1 text-sm text-red-600">
                Je moet daarna opnieuw al je provider-inloggegevens invoeren.
              </p>
              <div className="mt-3 flex gap-3">
                <button
                  onClick={() => {
                    resetVault();
                    setShowResetConfirm(false);
                  }}
                  className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
                >
                  Vault resetten
                </button>
                <button
                  onClick={() => setShowResetConfirm(false)}
                  className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
                >
                  Annuleren
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Unlocked vault — manage providers ──
  if (selectedProvider) {
    // Get provider info for the credential form
    const registry = ProviderRegistry.getInstance();
    const adapter = registry.get(selectedProvider);

    return (
      <div className="mx-auto max-w-2xl py-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-stone-900">
            Inloggegevens
          </h1>
          <button
            onClick={lock}
            className="rounded-lg border border-stone-300 px-3 py-1.5 text-sm text-stone-600 hover:bg-stone-50"
          >
            Vergrendelen
          </button>
        </div>

        <div className="mt-6">
          <ProviderCredentialForm
            provider={{
              id: selectedProvider as "vrt" | "vtm" | "playtv",
              displayName: adapter?.displayName ?? selectedProvider,
            }}
            initialValues={{
              email: providerEmail,
              password: providerPassword,
            }}
            onSubmit={handleFormSubmit}
            onCancel={handleFormCancel}
          />
        </div>
      </div>
    );
  }

  if (showAddPicker) {
    const registry = ProviderRegistry.getInstance();
    const allAdapters = registry.getAll();
    const configuredIds = new Set(providers.map((p) => p.provider));
    const available = allAdapters.filter((a) => !configuredIds.has(a.id));

    return (
      <div className="mx-auto max-w-2xl py-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-stone-900">
            Inloggegevens
          </h1>
          <button
            onClick={lock}
            className="rounded-lg border border-stone-300 px-3 py-1.5 text-sm text-stone-600 hover:bg-stone-50"
          >
            Vergrendelen
          </button>
        </div>

        <div className="mt-6">
          <h2 className="text-lg font-semibold text-stone-800">
            Kies een provider
          </h2>
          <p className="mt-1 text-sm text-stone-500">
            Selecteer de provider waarvoor je inloggegevens wilt toevoegen.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {available.map((a) => (
              <button
                key={a.id}
                onClick={() => {
                  setShowAddPicker(false);
                  setSelectedProvider(a.id);
                }}
                className="rounded-lg border border-stone-200 bg-white p-4 text-left shadow-sm transition-colors hover:border-stone-300 hover:shadow"
              >
                <span className="text-sm font-semibold text-stone-800">
                  {a.displayName}
                </span>
                {a.supportsAuth && (
                  <span className="ml-2 inline-flex items-center rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-600">
                    Beschikbaar
                  </span>
                )}
              </button>
            ))}
          </div>
          {available.length === 0 && (
            <p className="mt-4 text-sm text-stone-400">
              Alle providers zijn al geconfigureerd.
            </p>
          )}
          <button
            onClick={handleFormCancel}
            className="mt-4 text-sm text-stone-400 underline hover:text-stone-600"
          >
            Annuleren
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-stone-900">
          Inloggegevens
        </h1>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-sm text-green-600">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            Ontgrendeld
          </span>
          <button
            onClick={lock}
            className="rounded-lg border border-stone-300 px-3 py-1.5 text-sm text-stone-600 hover:bg-stone-50"
          >
            Vergrendelen
          </button>
        </div>
      </div>

      <p className="mt-2 text-sm text-stone-500">
        Voeg je inloggegevens toe voor elke provider. Je hoofdwachtwoord beschermt alle gegevens.
      </p>

      {error && (
        <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="mt-6">
        <ProviderList
          onEdit={handleEditProvider}
          onRemove={handleRemoveProvider}
        />
      </div>

      <button
        onClick={() => setShowAddPicker(true)}
        className="mt-4 w-full rounded-lg border border-dashed border-stone-300 px-4 py-3 text-sm font-medium text-stone-500 transition-colors hover:border-stone-400 hover:text-stone-700"
      >
        + Nieuwe provider toevoegen
      </button>

      {providers.length === 0 && (
        <div className="mt-4 rounded-lg border border-dashed border-stone-300 p-8 text-center text-sm text-stone-400">
          Nog geen providers geconfigureerd. Voeg hierboven je VRT MAX-account toe om te beginnen.
        </div>
      )}
    </div>
  );
}
