import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useState } from "react";
import PageHeader from "../components/PageHeader";
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
    <>
      <PageHeader title="Source IPs" description="Click an IP to open the investigation view with timeline, intel, and risk context." />

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
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>IP</th>
                  <th>Risk</th>
                  <th>Attempts</th>
                  <th>Country</th>
                  <th>ASN / ISP</th>
                  <th>Services</th>
                  <th>Last seen</th>
                </tr>
              </thead>
              <tbody>
                {data.items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-10 text-center text-muted">
                      No sources match filters.
                    </td>
                  </tr>
                ) : (
                  data.items.map((s) => (
                    <tr key={s.source_ip} className="hover:bg-surface2/40">
                      <td className="font-mono text-xs">
                        <Link to={`/app/sources/${encodeURIComponent(s.source_ip)}`} className="text-primary hover:underline">
                          {s.source_ip}
                        </Link>
                      </td>
                      <td className={`capitalize font-medium text-xs ${riskClass(s.max_risk_level)}`}>
                        {s.max_risk_level} ({s.max_risk_score})
                      </td>
                      <td className="tabular-nums">{s.total_attempts}</td>
                      <td className="text-xs">
                        {s.country_name ? (
                          <>
                            {countryFlag(s.country_code)} {s.country_name}
                          </>
                        ) : (
                          <span className="text-muted">—</span>
                        )}
                      </td>
                      <td className="text-xs text-muted max-w-[140px] truncate" title={s.isp || ""}>
                        {s.asn || s.isp || "—"}
                      </td>
                      <td className="text-xs">{(s.services || []).join(", ") || "—"}</td>
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
