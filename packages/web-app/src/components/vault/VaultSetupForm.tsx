import { useState, type FormEvent } from "react";

interface VaultSetupFormProps {
  onSetup: (password: string) => void;
}

function VaultSetupForm({ onSetup }: VaultSetupFormProps) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const isLongEnough = password.length >= 8;
  const passwordsMatch = password === confirm && password.length > 0;
  const canSubmit = isLongEnough && passwordsMatch;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (canSubmit) {
      onSetup(password);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-stone-800">
          Vault instellen
        </h2>
        <p className="mt-1 text-sm text-stone-500">
          Kies een hoofdwachtwoord om je inloggegevens te beveiligen.
        </p>

        {/* Warning banner */}
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
          <span className="font-medium">⚠ Dit wachtwoord kan niet worden hersteld.</span>{" "}
          Verlies je het, dan ben je al je opgeslagen inloggegevens kwijt.
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {/* New password */}
          <div>
            <label
              htmlFor="vault-password"
              className="block text-sm font-medium text-stone-700"
            >
              Nieuw hoofdwachtwoord
            </label>
            <div className="relative mt-1">
              <input
                id="vault-password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimaal 8 tekens"
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
            {password.length > 0 && !isLongEnough && (
              <p className="mt-1 text-xs text-amber-600">
                Minimaal 8 tekens vereist
              </p>
            )}
          </div>

          {/* Confirm password */}
          <div>
            <label
              htmlFor="vault-confirm"
              className="block text-sm font-medium text-stone-700"
            >
              Herhaal wachtwoord
            </label>
            <div className="relative mt-1">
              <input
                id="vault-confirm"
                type={showConfirm ? "text" : "password"}
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="Herhaal je hoofdwachtwoord"
                className="w-full rounded-lg border border-stone-300 px-4 py-2.5 pr-10 text-sm outline-none transition-colors focus:border-stone-500 focus:ring-2 focus:ring-stone-400"
              />
              <button
                type="button"
                onClick={() => setShowConfirm((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600"
                tabIndex={-1}
                aria-label={showConfirm ? "Wachtwoord verbergen" : "Wachtwoord tonen"}
              >
                {showConfirm ? (
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
            {confirm.length > 0 && !passwordsMatch && (
              <p className="mt-1 text-xs text-red-600">
                Wachtwoorden komen niet overeen
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={!canSubmit}
            className="w-full rounded-lg bg-stone-800 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Vault aanmaken
          </button>
        </form>
      </div>
    </div>
  );
}

export default VaultSetupForm;
