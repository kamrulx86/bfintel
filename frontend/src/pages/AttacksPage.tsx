import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { useEffect, useState } from "react";
import TableFilters from "../components/TableFilters";
import { api } from "../lib/api";

function riskClass(level: string) {
  if (level === "critical") return "text-critical";
  if (level === "high") return "text-warning";
  if (level === "medium") return "text-primary";
  return "text-muted";
}

export default function AttacksPage() {
  const [params] = useSearchParams();
  const [hours, setHours] = useState("");
  const [riskLevel, setRiskLevel] = useState("");
  const [service, setService] = useState("");
  const [query, setQuery] = useState("");

  const hostFilter = params.get("host") ?? undefined;
  const usernameFilter = params.get("username") ?? undefined;

  useEffect(() => {
    if (hostFilter) setQuery("");
  }, [hostFilter, usernameFilter]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["attacks", hours, riskLevel, service, query, hostFilter, usernameFilter],
    queryFn: () =>
      api.attacks({
        hours: hours ? Number(hours) : undefined,
        risk_level: riskLevel || undefined,
        service: service || undefined,
        source_ip: query || undefined,
        host: hostFilter,
        username: usernameFilter,
      }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Attack sessions</h1>
        <p className="text-muted text-sm mt-1">Correlated brute-force activity grouped by source IP.</p>
        {(hostFilter || usernameFilter) && (
          <p className="text-xs text-muted mt-2 font-mono">
            Filtered by {hostFilter ? `host=${hostFilter}` : ""}
            {hostFilter && usernameFilter ? " · " : ""}
            {usernameFilter ? `username=${usernameFilter}` : ""}
          </p>
        )}
      </div>

      <TableFilters
        hours={hours}
        onHoursChange={setHours}
        riskLevel={riskLevel}
        onRiskLevelChange={setRiskLevel}
        service={service}
        onServiceChange={setService}
        query={query}
        onQueryChange={setQuery}
      />

      {isLoading && <p className="text-muted text-sm">Loading sessions…</p>}
      {isError && <p className="text-critical text-sm">Could not load attack sessions.</p>}

      {data && (
        <div className="panel overflow-hidden">
          <div className="px-4 py-3 border-b border-[var(--border)] text-xs text-muted">
            {data.total} session{data.total === 1 ? "" : "s"}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs uppercase text-muted bg-surface2/50">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Source IP</th>
                  <th className="text-left px-4 py-3 font-medium">Attempts</th>
                  <th className="text-left px-4 py-3 font-medium">Targets</th>
                  <th className="text-left px-4 py-3 font-medium">Services</th>
                  <th className="text-left px-4 py-3 font-medium">Risk</th>
                  <th className="text-left px-4 py-3 font-medium">Last seen</th>
                </tr>
              </thead>
              <tbody>
                {data.items.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-muted">
                      No sessions match filters.
                    </td>
                  </tr>
                ) : (
                  data.items.map((s) => (
                    <tr key={s.id} className="border-t border-[var(--border)] hover:bg-surface2/30">
                      <td className="px-4 py-3 font-mono">
                        <Link to={`/app/sources/${encodeURIComponent(s.source_ip)}`} className="text-primary hover:underline">
                          {s.source_ip}
                        </Link>
                      </td>
                      <td className="px-4 py-3 tabular-nums">{s.attempt_count}</td>
                      <td className="px-4 py-3">{(s.target_hosts || []).slice(0, 2).join(", ") || "—"}</td>
                      <td className="px-4 py-3">{(s.services || []).join(", ") || "—"}</td>
                      <td className={`px-4 py-3 font-medium capitalize ${riskClass(s.risk_level)}`}>
                        {s.risk_level} ({s.risk_score})
                      </td>
                      <td className="px-4 py-3 text-muted text-xs">{new Date(s.last_seen).toLocaleString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
