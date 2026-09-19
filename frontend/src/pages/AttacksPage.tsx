import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { useEffect, useState } from "react";
import PageHeader from "../components/PageHeader";
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
    <>
      <PageHeader
        title="Attack sessions"
        description="Correlated brute-force activity grouped by source IP."
        meta={
          hostFilter || usernameFilter ? (
            <span className="text-xs font-mono text-muted">
              Filtered by {hostFilter ? `host=${hostFilter}` : ""}
              {hostFilter && usernameFilter ? " · " : ""}
              {usernameFilter ? `username=${usernameFilter}` : ""}
            </span>
          ) : undefined
        }
      />

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
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Source IP</th>
                  <th>Attempts</th>
                  <th>Targets</th>
                  <th>Services</th>
                  <th>Risk</th>
                  <th>Last seen</th>
                </tr>
              </thead>
              <tbody>
                {data.items.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-10 text-center text-muted">
                      No sessions match filters.
                    </td>
                  </tr>
                ) : (
                  data.items.map((s) => (
                    <tr key={s.id} className="hover:bg-surface2/40">
                      <td className="font-mono text-xs">
                        <Link to={`/app/sources/${encodeURIComponent(s.source_ip)}`} className="text-primary hover:underline">
                          {s.source_ip}
                        </Link>
                      </td>
                      <td className="tabular-nums">{s.attempt_count}</td>
                      <td className="text-xs max-w-[120px] truncate">{(s.target_hosts || []).slice(0, 2).join(", ") || "—"}</td>
                      <td className="text-xs">{(s.services || []).join(", ") || "—"}</td>
                      <td className={`font-medium capitalize text-xs ${riskClass(s.risk_level)}`}>
                        {s.risk_level} ({s.risk_score})
                      </td>
                      <td className="text-muted text-xs whitespace-nowrap">{new Date(s.last_seen).toLocaleString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
