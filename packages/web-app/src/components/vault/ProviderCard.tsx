type ProviderId = "vrt" | "vtm" | "playtv";

interface Provider {
  id: ProviderId;
  displayName: string;
}

interface ProviderCardProps {
  provider: Provider;
  email: string;
  isActive: boolean;
  isImplemented: boolean;
  onEdit: () => void;
  onRemove: () => void;
}

const PROVIDER_COLORS: Record<ProviderId, string> = {
  vrt: "#FFC00E",
  vtm: "#E10A1D",
  playtv: "#00B8A9",
};

function maskEmail(email: string): string {
  const [local, domain] = email.split("@");
  if (!local || !domain) return email;
  const maskedLocal = local.length <= 2
    ? local[0] + "*".repeat(local.length - 1)
    : local[0] + "*".repeat(local.length - 2) + local[local.length - 1];
  return `${maskedLocal}@${domain}`;
}

function ProviderCard({
  provider,
  email,
  isActive,
  isImplemented,
  onEdit,
  onRemove,
}: ProviderCardProps) {
  const color = PROVIDER_COLORS[provider.id] ?? "#78716c";

  return (
    <div className="overflow-hidden rounded-lg border border-stone-200 bg-white shadow-sm">
      {/* Color bar */}
      <div className="h-1.5" style={{ backgroundColor: color }} />

      <div className="p-4">
        <div className="flex items-start justify-between">
          {/* Left: provider info */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <div
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold"
                style={{
                  backgroundColor: `${color}1A`,
                  color: color,
                }}
              >
                {provider.displayName.charAt(0)}
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-800">
                  {provider.displayName}
                </h3>
                <p className="text-xs text-stone-400">{maskEmail(email)}</p>
              </div>
            </div>
          </div>

          {/* Right: status */}
          <span
            className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${
              isImplemented && isActive
                ? "bg-green-50 text-green-600"
                : "bg-stone-100 text-stone-400"
            }`}
          >
            {isImplemented && isActive ? "Actief" : "Nog niet beschikbaar"}
          </span>
        </div>

        {/* Actions */}
        <div className="mt-3 flex gap-2 border-t border-stone-100 pt-3">
          <button
            type="button"
            onClick={onEdit}
            disabled={!isImplemented}
            className="rounded-lg px-3 py-1.5 text-xs font-medium text-stone-600 transition-colors hover:bg-stone-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Bewerken
          </button>
          <button
            type="button"
            onClick={onRemove}
            disabled={!isImplemented}
            className="rounded-lg px-3 py-1.5 text-xs font-medium text-red-600 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Verwijderen
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProviderCard;
