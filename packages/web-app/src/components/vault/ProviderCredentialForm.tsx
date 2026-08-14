import { useState, type FormEvent } from "react";
import { ProviderRegistry } from "@thuis/core";
import { useVault } from "../../hooks/useVault.js";

type ProviderId = "vrt" | "vtm" | "playtv";

interface Provider {
  id: ProviderId;
  displayName: string;
}

interface Credentials {
  email: string;
  password: string;
  label: string;
  verifyAfterSave: boolean;
}

interface ProviderCredentialFormProps {
  provider: Provider;
  onSubmit: (credentials: Credentials) => void;
  onCancel?: () => void;
  onError?: (error: string) => void;
  initialValues?: Partial<Credentials>;
  isSubmitting?: boolean;
}

const PROVIDER_STYLES: Record<
  ProviderId,
  { color: string; bg: string; border: string; ring: string; label: string }
> = {
  vrt: {
    color: "#FFC00E",
    bg: "bg-[#FFC00E]/10",
    border: "border-[#FFC00E]/30",
    ring: "focus:ring-[#FFC00E]",
    label: "VRT MAX",
  },
  vtm: {
    color: "#E10A1D",
    bg: "bg-[#E10A1D]/10",
    border: "border-[#E10A1D]/30",
    ring: "focus:ring-[#E10A1D]",
    label: "VTM GO",
  },
  playtv: {
    color: "#00B8A9",
    bg: "bg-[#00B8A9]/10",
    border: "border-[#00B8A9]/30",
    ring: "focus:ring-[#00B8A9]",
    label: "Play.TV",
  },
};

function ProviderCredentialForm({
  provider,
  onSubmit,
  onCancel,
  onError,
  initialValues,
  isSubmitting = false,
}: ProviderCredentialFormProps) {
  const [email, setEmail] = useState(initialValues?.email ?? "");
  const [password, setPassword] = useState(initialValues?.password ?? "");
  const [label, setLabel] = useState(initialValues?.label ?? "");
  const [verifyAfterSave, setVerifyAfterSave] = useState(
    initialValues?.verifyAfterSave ?? false,
  );
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

const { addProvider } = useVault();

const styles = PROVIDER_STYLES[provider.id];
const registry = ProviderRegistry.getInstance();
const adapter = registry.get(provider.id);
const isImplemented = !!adapter && adapter.supportsAuth;
const canSubmit = email.length > 0 && password.length > 0 && isImplemented;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canSubmit || isSubmitting) return;
    if (!adapter?.supportsAuth) return;

    setFormError(null);

    (async () => {
      try {
        await adapter.login({ username: email, password });
        await addProvider(provider.id, email, password);
        onSubmit({ email, password, label, verifyAfterSave });
      } catch (err: unknown) {
        const msg = (err as Error)?.message ?? "Onbekende fout bij inloggen";
        setFormError(msg);
        onError?.(msg);
      }
    })();
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="overflow-hidden rounded-lg border border-stone-200 bg-white shadow-sm">
        {/* Provider header with color bar */}
        <div className="h-1.5" style={{ backgroundColor: styles.color }} />

        <div className="p-6">
          {/* Provider label */}
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold"
              style={{
                backgroundColor: styles.bg,
                color: styles.color,
                borderColor: styles.border,
              }}
            >
              {provider.displayName.charAt(0)}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-stone-800">
                {provider.displayName}
              </h2>
              <p className="text-xs text-stone-400">{styles.label}</p>
            </div>
          </div>

          {!isImplemented && (
            <div className="mt-4 rounded-lg border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-500">
              {provider.displayName} wordt nog niet ondersteund.{" "}
              <span className="italic">Binnenkort beschikbaar.</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {/* Email */}
            <div>
              <label
                htmlFor={`${provider.id}-email`}
                className="block text-sm font-medium text-stone-700"
              >
                E-mailadres
              </label>
              <input
                id={`${provider.id}-email`}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="naam@voorbeeld.com"
                disabled={!isImplemented}
                className="mt-1 w-full rounded-lg border border-stone-300 px-4 py-2.5 text-sm outline-none transition-colors focus:border-stone-500 focus:ring-2 focus:ring-stone-400 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor={`${provider.id}-password`}
                className="block text-sm font-medium text-stone-700"
              >
                Wachtwoord
              </label>
              <div className="relative mt-1">
                <input
                  id={`${provider.id}-password`}
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={!isImplemented}
                  className="w-full rounded-lg border border-stone-300 px-4 py-2.5 pr-10 text-sm outline-none transition-colors focus:border-stone-500 focus:ring-2 focus:ring-stone-400 disabled:cursor-not-allowed disabled:opacity-50"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600 disabled:cursor-not-allowed disabled:opacity-50"
                  tabIndex={-1}
                  disabled={!isImplemented}
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
            </div>

            {/* Label */}
            <div>
              <label
                htmlFor={`${provider.id}-label`}
                className="block text-sm font-medium text-stone-700"
              >
                Label <span className="text-stone-400">(optioneel)</span>
              </label>
              <input
                id={`${provider.id}-label`}
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder="Bijv. Mijn VRT-account"
                disabled={!isImplemented}
                className="mt-1 w-full rounded-lg border border-stone-300 px-4 py-2.5 text-sm outline-none transition-colors focus:border-stone-500 focus:ring-2 focus:ring-stone-400 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            {/* Error message */}
            {formError && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
                {formError}
              </div>
            )}

            {/* Verify checkbox */}
            <label className="flex items-center gap-2 text-sm text-stone-600">
              <input
                type="checkbox"
                checked={verifyAfterSave}
                onChange={(e) => setVerifyAfterSave(e.target.checked)}
                disabled={!isImplemented}
                className="h-4 w-4 rounded border-stone-300 text-stone-800 focus:ring-stone-400 disabled:cursor-not-allowed disabled:opacity-50"
              />
              Verifieer nu
            </label>

            <div className="flex gap-3">
              {onCancel && (
                <button
                  type="button"
                  onClick={onCancel}
                  disabled={isSubmitting}
                  className="flex-1 rounded-lg border border-stone-300 px-4 py-2.5 text-sm font-medium text-stone-700 transition-colors hover:bg-stone-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Annuleren
                </button>
              )}
              <button
                type="submit"
                disabled={!canSubmit || isSubmitting}
                className="flex-1 rounded-lg bg-stone-800 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSubmitting ? "Bezig met opslaan…" : "Opslaan"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default ProviderCredentialForm;
