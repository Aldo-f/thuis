interface VaultStatusBadgeProps {
  isLocked: boolean;
  isInitialized: boolean;
}

function VaultStatusBadge({ isLocked, isInitialized }: VaultStatusBadgeProps) {
  if (!isInitialized) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-stone-100 px-3 py-1 text-xs font-medium text-stone-500">
        <span className="h-2 w-2 rounded-full bg-stone-400" />
        Niet ingesteld
      </span>
    );
  }

  if (isLocked) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-600">
        <span className="h-2 w-2 rounded-full bg-red-500" />
        Grendel
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-600">
      <span className="h-2 w-2 rounded-full bg-green-500" />
      Ontgrendeld
    </span>
  );
}

export default VaultStatusBadge;
