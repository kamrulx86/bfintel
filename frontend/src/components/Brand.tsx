export function Brand({ compact }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className="relative flex h-9 w-9 items-center justify-center rounded-lg bg-primary/15 ring-1 ring-primary/30">
        <svg viewBox="0 0 24 24" className="h-5 w-5 text-primary" fill="none" stroke="currentColor" strokeWidth="1.75">
          <path d="M12 3 4 8v8l8 5 8-5V8l-8-5Z" />
          <path d="M12 12 4 8M12 12l8-4M12 12v8" />
        </svg>
      </div>
      {!compact && (
        <div>
          <p className="font-semibold tracking-tight leading-none">BFIntel</p>
          <p className="text-[11px] text-muted mt-0.5">Wazuh intelligence layer</p>
        </div>
      )}
    </div>
  );
}
