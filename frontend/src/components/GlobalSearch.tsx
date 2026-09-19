import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";

export default function GlobalSearch() {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const debounced = useDebouncedValue(q, 250);
  const navigate = useNavigate();
  const wrapRef = useRef<HTMLDivElement>(null);

  const { data } = useQuery({
    queryKey: ["search", debounced],
    queryFn: () => api.search(debounced),
    enabled: debounced.length >= 2,
  });

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  return (
    <div ref={wrapRef} className="relative flex-1 max-w-lg">
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted pointer-events-none"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="M20 20l-3-3" />
        </svg>
        <input
          type="search"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder="Search IP, hostname, username…"
          className="input-field py-2.5 text-xs w-full pl-10"
        />
      </div>
      {open && debounced.length >= 2 && data && data.results.length > 0 && (
        <div className="absolute z-50 mt-1 w-full panel py-1 max-h-72 overflow-auto shadow-lg">
          {data.results.map((r) => (
            <button
              key={`${r.type}-${r.label}`}
              type="button"
              className="w-full text-left px-3 py-2 hover:bg-surface2/80 text-sm flex justify-between gap-2"
              onClick={() => {
                navigate(r.href);
                setOpen(false);
                setQ("");
              }}
            >
              <span className="font-mono truncate">{r.label}</span>
              <span className="text-muted text-xs shrink-0">{r.meta}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function useDebouncedValue<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}
