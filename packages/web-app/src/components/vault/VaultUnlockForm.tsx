import { useState, type FormEvent } from "react";

interface VaultUnlockFormProps {
  onUnlock: (password: string) => void;
  onReset: () => void;
  error?: string;
}

function VaultUnlockForm({ onUnlock, onReset, error }: VaultUnlockFormProps) {
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (password.length > 0) {
      onUnlock(password);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-stone-800">
          Vault ontgrendelen
        </h2>
        <p className="mt-1 text-sm text-stone-500">
          Voer je hoofdwachtwoord in om toegang te krijgen tot je opgeslagen inloggegevens.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {/* Password */}
          <div>
            <label
              htmlFor="unlock-password"
              className="block text-sm font-medium text-stone-700"
            >
              Hoofdwachtwoord
            </label>
            <div className="relative mt-1">
              <input
                id="unlock-password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Voer je hoofdwachtwoord in"
                className="w-full rounded-lg border border-stone-300 px-4 py-2.5 pr-10 text-sm outline-none transition-colors focus:border-stone-500 focus:ring-2 focus:ring-stone-400"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600"
                tabIndex={-1}
                aria-label={showPassword ? "Wachtwoord verbergen" : "Wachtwoord tonen"}
              >
                {showPassword ? (
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                  </svg>
                ) : (
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
            {error && (
              <p className="mt-1 text-xs text-red-600">{error}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={password.length === 0}
            className="w-full rounded-lg bg-stone-800 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Ontgrendelen
          </button>
        </form>

        {/* Forgot password */}
        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => setShowResetConfirm(true)}
            className="text-xs text-stone-400 underline transition-colors hover:text-stone-600"
          >
            Wachtwoord vergeten?
          </button>
        </div>
      </div>

      {/* Reset confirmation dialog */}
      {showResetConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
          <div className="w-full max-w-sm rounded-lg border border-stone-200 bg-white p-6 shadow-lg">
            <h3 className="text-base font-semibold text-stone-800">
              Vault resetten?
            </h3>
            <p className="mt-2 text-sm text-stone-500">
              Alle opgeslagen inloggegevens zullen verloren gaan.
            </p>
            <div className="mt-4 flex gap-3">
              <button
                type="button"
                onClick={() => setShowResetConfirm(false)}
                className="flex-1 rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 transition-colors hover:bg-stone-100"
              >
                Annuleren
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowResetConfirm(false);
                  onReset();
                }}
                className="flex-1 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
              >
                Reset vault
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default VaultUnlockForm;
