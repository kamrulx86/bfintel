import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useState } from "react";
import TableFilters from "../components/TableFilters";
import { countryFlag } from "../lib/country";
import { api } from "../lib/api";

function riskClass(level: string) {
  if (level === "critical") return "text-critical";
  if (level === "high") return "text-warning";
  if (level === "medium") return "text-primary";
  return "text-muted";
}

export default function SourcesPage() {
  const [hours, setHours] = useState("");
  const [riskLevel, setRiskLevel] = useState("");
  const [service, setService] = useState("");
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["sources", hours, riskLevel, service, query, country],
    queryFn: () =>
      api.sources({
        hours: hours ? Number(hours) : undefined,
        risk_level: riskLevel || undefined,
        service: service || undefined,
        q: query || undefined,
        country: country || undefined,
      }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Source IPs</h1>
        <p className="text-muted text-sm mt-1">Click an IP to open the investigation view.</p>
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
        country={country}
        onCountryChange={setCountry}
      />

      {isLoading && <p className="text-muted text-sm">Loading sources…</p>}
      {isError && <p className="text-critical text-sm">Could not load source list.</p>}

      {data && (
        <div className="panel overflow-hidden">
          <div className="px-4 py-3 border-b border-[var(--border)] text-xs text-muted">
            {data.total} source{data.total === 1 ? "" : "s"}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs uppercase text-muted bg-surface2/50">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">IP</th>
                  <th className="text-left px-4 py-3 font-medium">Risk</th>
                  <th className="text-left px-4 py-3 font-medium">Attempts</th>
                  <th className="text-left px-4 py-3 font-medium">Country</th>
                  <th className="text-left px-4 py-3 font-medium">ASN / ISP</th>
                  <th className="text-left px-4 py-3 font-medium">Services</th>
                  <th className="text-left px-4 py-3 font-medium">Last seen</th>
                </tr>
              </thead>
              <tbody>
                {data.items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-10 text-center text-muted">
                      No sources match filters.
                    </td>
                  </tr>
                ) : (
                  data.items.map((s) => (
                    <tr key={s.source_ip} className="border-t border-[var(--border)] hover:bg-surface2/30">
                      <td className="px-4 py-3 font-mono">
                        <Link to={`/app/sources/${encodeURIComponent(s.source_ip)}`} className="text-primary hover:underline">
                          {s.source_ip}
                        </Link>
                      </td>
                      <td className={`px-4 py-3 capitalize font-medium ${riskClass(s.max_risk_level)}`}>
                        {s.max_risk_level} ({s.max_risk_score})
                      </td>
                      <td className="px-4 py-3 tabular-nums">{s.total_attempts}</td>
                      <td className="px-4 py-3 text-xs">
                        {s.country_name ? (
                          <>
                            {countryFlag(s.country_code)} {s.country_name}
                          </>
                        ) : (
                          <span className="text-muted">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-muted max-w-[140px] truncate" title={s.isp || ""}>
                        {s.asn || s.isp || "—"}
                      </td>
                      <td className="px-4 py-3">{(s.services || []).join(", ") || "—"}</td>
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
