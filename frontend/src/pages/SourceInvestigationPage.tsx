import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { countryFlag } from "../lib/country";
import { api } from "../lib/api";

function riskClass(level: string) {
  if (level === "critical") return "text-critical";
  if (level === "high") return "text-warning";
  if (level === "medium") return "text-primary";
  return "text-muted";
}

export default function SourceInvestigationPage() {
  const { ip = "" } = useParams();
  const decoded = decodeURIComponent(ip);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: profile, isLoading, isError } = useQuery({
    queryKey: ["ip-profile", decoded],
    queryFn: () => api.ipProfile(decoded),
    enabled: !!decoded,
  });

  const { data: timeline } = useQuery({
    queryKey: ["ip-timeline", decoded],
    queryFn: () => api.ipTimeline(decoded, { limit: 50 }),
    enabled: !!decoded,
  });

  const refresh = useMutation({
    mutationFn: () => api.refreshIpIntel(decoded),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ip-profile", decoded] });
      qc.invalidateQueries({ queryKey: ["sources"] });
    },
  });

  const watchlist = useMutation({
    mutationFn: () => api.addWatchlist({ source_ip: decoded, reason: "Added from investigation", risk_level: profile?.max_risk_level ?? "medium" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["watchlist"] }),
  });

  const blocklist = useMutation({
    mutationFn: () => api.addBlocklist({ source_ip: decoded, reason: "Added from investigation" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["blocklist"] }),
  });

  const abuseReport = useMutation({
    mutationFn: () => api.createAbuseReportFromIp(decoded),
    onSuccess: () => navigate("/app/abuse-reports"),
  });

  const openCase = useMutation({
    mutationFn: () =>
      api.createCase({
        title: `Investigation: ${decoded}`,
        source_ip: decoded,
        severity: profile?.max_risk_level === "critical" || profile?.max_risk_level === "high" ? profile.max_risk_level : "medium",
        priority: profile && profile.max_risk_score >= 70 ? "high" : "normal",
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cases"] });
      qc.invalidateQueries({ queryKey: ["dashboard-metrics"] });
      navigate("/app/cases");
    },
  });

  if (isLoading) return <p className="text-muted text-sm">Loading investigation…</p>;
  if (isError || !profile) {
    return (
      <div className="space-y-4">
        <Link to="/app/sources" className="text-xs text-primary hover:underline">
          ← Source IPs
        </Link>
        <p className="text-critical">No investigation data for this address.</p>
      </div>
    );
  }

  const geo = profile.geo;
  const flag = countryFlag(geo?.country_code);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link to="/app/sources" className="text-xs text-primary hover:underline">
            ← Source IPs
          </Link>
          <h1 className="text-2xl font-semibold tracking-tight font-mono mt-2 flex items-center gap-2">
            {flag && <span aria-hidden>{flag}</span>}
            {profile.source_ip}
          </h1>
          <p className="text-muted text-sm mt-1">
            Observed source · scope: <span className="text-text capitalize">{profile.network_scope}</span>
            {geo?.country_name && (
              <>
                {" "}
                · {geo.country_name}
                {geo.city ? `, ${geo.city}` : ""}
              </>
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn-ghost text-xs" disabled={refresh.isPending} onClick={() => refresh.mutate()}>
            {refresh.isPending ? "Refreshing…" : "Run intelligence lookup"}
          </button>
          <button type="button" className="btn-ghost text-xs" disabled={abuseReport.isPending} onClick={() => abuseReport.mutate()}>
            {abuseReport.isPending ? "Drafting…" : "Draft abuse report"}
          </button>
          <button type="button" className="btn-ghost text-xs" disabled={openCase.isPending} onClick={() => openCase.mutate()}>
            Open case
          </button>
          <button type="button" className="btn-ghost text-xs" disabled={watchlist.isPending} onClick={() => watchlist.mutate()}>
            Watchlist
          </button>
          <button type="button" className="btn-ghost text-xs" disabled={blocklist.isPending} onClick={() => blocklist.mutate()}>
            Blocklist
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          { label: "Risk", value: `${profile.max_risk_level} (${profile.max_risk_score})` },
          { label: "Events", value: profile.total_events },
          { label: "Failures / success", value: `${profile.failure_count} / ${profile.success_count}` },
          { label: "Sessions", value: profile.session_count },
        ].map((m) => (
          <div key={m.label} className="panel p-4">
            <p className="text-xs uppercase text-muted">{m.label}</p>
            <p className={`text-xl font-semibold mt-1 capitalize ${m.label === "Risk" ? riskClass(profile.max_risk_level) : ""}`}>
              {m.value}
            </p>
          </div>
        ))}
      </div>

      <div className="grid xl:grid-cols-2 gap-6">
        <div className="panel p-5 space-y-3">
          <h2 className="text-sm font-semibold">Network information</h2>
          {profile.geo_placeholder ? (
            <p className="text-muted text-sm">Enrichment pending — worker will populate Geo/ASN shortly.</p>
          ) : (
            <dl className="text-sm grid grid-cols-[120px_1fr] gap-2">
              <dt className="text-muted">ASN</dt>
              <dd className="font-mono text-xs">{geo?.asn || "—"}</dd>
              <dt className="text-muted">ISP</dt>
              <dd>{geo?.isp || "—"}</dd>
              <dt className="text-muted">Organization</dt>
              <dd>{geo?.organization_name || "—"}</dd>
              <dt className="text-muted">Reverse DNS</dt>
              <dd className="font-mono text-xs break-all">{geo?.reverse_dns || "—"}</dd>
              <dt className="text-muted">Hosting</dt>
              <dd>{geo?.is_hosting == null ? "—" : geo.is_hosting ? "Likely datacenter" : "No indicator"}</dd>
            </dl>
          )}
        </div>

        <div className="panel p-5">
          <h2 className="text-sm font-semibold mb-3">Risk explanation</h2>
          {profile.risk_reasons.length === 0 ? (
            <p className="text-muted text-sm">No elevated risk signals from correlated sessions yet.</p>
          ) : (
            <ul className="text-sm space-y-2 text-muted">
              {profile.risk_reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {profile.threat_intel.length > 0 && (
        <div className="panel p-5 space-y-4">
          <h2 className="text-sm font-semibold">Threat intelligence (by provider)</h2>
          {profile.threat_intel.map((snap) => (
            <div key={`${snap.provider}-${snap.fetched_at}`} className="border border-[var(--border)] rounded-lg p-4">
              <div className="flex justify-between gap-2 text-xs text-muted mb-2">
                <span className="uppercase tracking-wide text-text font-medium">{snap.provider}</span>
                <span>{new Date(snap.fetched_at).toLocaleString()}</span>
              </div>
              {!snap.success ? (
                <p className="text-sm text-warning">{snap.error || "Lookup failed"}</p>
              ) : snap.provider === "abuseipdb" ? (
                <dl className="text-sm grid grid-cols-2 gap-2">
                  <dt className="text-muted">Confidence score</dt>
                  <dd>{String(snap.data.abuse_confidence_score ?? "—")}</dd>
                  <dt className="text-muted">Total reports</dt>
                  <dd>{String(snap.data.total_reports ?? "—")}</dd>
                </dl>
              ) : (
                <p className="text-xs text-muted font-mono">Geo/ASN snapshot stored · see Network information</p>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="panel p-5">
        <h2 className="text-sm font-semibold mb-4">Event timeline</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs uppercase text-muted">
              <tr>
                <th className="text-left py-2 pr-4">Time</th>
                <th className="text-left py-2 pr-4">User</th>
                <th className="text-left py-2 pr-4">Service</th>
                <th className="text-left py-2 pr-4">Target</th>
                <th className="text-left py-2">Result</th>
              </tr>
            </thead>
            <tbody>
              {!timeline?.items.length ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-muted">
                    No timeline events in range.
                  </td>
                </tr>
              ) : (
                timeline.items.map((ev) => (
                  <tr key={ev.id} className="border-t border-[var(--border)]">
                    <td className="py-2 pr-4 font-mono text-xs text-muted">{new Date(ev.timestamp).toLocaleString()}</td>
                    <td className="py-2 pr-4 font-mono text-xs">{ev.username || "—"}</td>
                    <td className="py-2 pr-4">{ev.service || "—"}</td>
                    <td className="py-2 pr-4">{ev.target_host || "—"}</td>
                    <td className="py-2 capitalize">{ev.authentication_result || "—"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
