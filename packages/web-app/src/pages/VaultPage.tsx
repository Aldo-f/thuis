import { useState } from "react";
import { useVault } from "../hooks/useVault.js";

const PROVIDERS = [
  { id: "vrt", displayName: "VRT MAX", color: "#FFC00E", implemented: true },
  { id: "vtm", displayName: "VTM GO", color: "#E10A1D", implemented: false },
  { id: "playtv", displayName: "Play.TV", color: "#00B8A9", implemented: false },
];

function maskEmail(email: string): string {
  const [name, domain] = email.split("@");
  if (!name || !domain) return email;
  const visible = name.slice(0, 3);
  return `${visible}***@${domain}`;
}

export default function VaultPage() {
  const {
    vaultState, providers, error,
    setup, unlock, lock, addProvider, removeProvider, resetVault, clearError,
  } = useVault();

  const [masterPassword, setMasterPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // Provider form state
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [providerEmail, setProviderEmail] = useState("");
  const [providerPassword, setProviderPassword] = useState("");

  // Reset confirmation
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [, /* unused masterPassword for locked state */] = useState("");

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

      {/* Provider list */}
      <div className="mt-6 space-y-3">
        {PROVIDERS.map((p) => {
          const stored = providers.find((s) => s.provider === p.id);
          return (
            <div
              key={p.id}
              className="overflow-hidden rounded-lg border border-stone-200 bg-white shadow-sm"
            >
              <div className="flex" style={{ borderLeft: `4px solid ${p.color}` }}>
                <div className="flex flex-1 items-center justify-between p-4">
                  <div>
                    <h3 className="font-medium text-stone-900">{p.displayName}</h3>
                    {stored ? (
                      <p className="text-sm text-stone-500">
                        {maskEmail(stored.email)}
                      </p>
                    ) : (
                      <p className="text-sm text-stone-400">
                        {p.implemented ? "Nog niet geconfigureerd" : "Nog niet beschikbaar"}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {stored && (
                      <span className="rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700">
                        Actief
                      </span>
                    )}
                    {!p.implemented && (
                      <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs text-stone-500">
                        Binnenkort
                      </span>
                    )}
                  </div>
                </div>
                {p.implemented && (
                  <div className="flex items-center gap-1 border-l border-stone-200 px-3">
                    {selectedProvider === p.id ? (
                      <button
                        onClick={() => setSelectedProvider(null)}
                        className="rounded px-2 py-1 text-sm text-stone-500 hover:bg-stone-100"
                      >
                        Annuleren
                      </button>
                    ) : (
                      <button
                        onClick={() => setSelectedProvider(p.id)}
                        className="rounded px-2 py-1 text-sm text-stone-500 hover:bg-stone-100"
                      >
                        {stored ? "Wijzigen" : "Toevoegen"}
                      </button>
                    )}
                    {stored && (
                      <button
                        onClick={() => removeProvider(p.id)}
                        className="rounded px-2 py-1 text-sm text-red-500 hover:bg-red-50"
                      >
                        Verwijderen
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Inline form */}
              {selectedProvider === p.id && (
                <div className="border-t border-stone-200 bg-stone-50 p-4">
                  <div className="space-y-3">
                    <input
                      type="email"
                      value={providerEmail}
                      onChange={(e) => setProviderEmail(e.target.value)}
                      placeholder="E-mailadres"
                      className="block w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-stone-400 focus:outline-none focus:ring-2 focus:ring-stone-400"
                    />
                    <input
                      type="password"
                      value={providerPassword}
                      onChange={(e) => setProviderPassword(e.target.value)}
                      placeholder="Wachtwoord"
                      className="block w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-stone-400 focus:outline-none focus:ring-2 focus:ring-stone-400"
                    />
                    <div className="flex gap-3">
                      <button
                        onClick={async () => {
                          if (providerEmail && providerPassword) {
                            await addProvider(p.id, providerEmail, providerPassword);
                            setProviderEmail("");
                            setProviderPassword("");
                            setSelectedProvider(null);
                          }
                        }}
                        disabled={!providerEmail || !providerPassword}
                        className="rounded-lg bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        Opslaan
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {providers.length === 0 && (
        <div className="mt-8 rounded-lg border border-dashed border-stone-300 p-8 text-center text-sm text-stone-400">
          Nog geen providers geconfigureerd. Voeg hierboven je VRT MAX-account toe om te beginnen.
        </div>
      )}
    </div>
  );
}
