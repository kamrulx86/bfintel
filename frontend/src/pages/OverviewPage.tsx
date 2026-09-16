import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Area, AreaChart } from "recharts";
import { api } from "../lib/api";

const chartTick = { fill: "#8993a3", fontSize: 11 };
const gridStroke = "#252f3d";

export default function OverviewPage() {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ["dashboard-metrics"],
    queryFn: () => api.dashboardMetrics(),
    refetchInterval: 60_000,
  });

  const { data: charts } = useQuery({
    queryKey: ["dashboard-charts", 24],
    queryFn: () => api.dashboardCharts(24),
    refetchInterval: 60_000,
  });

  const { data: attacks } = useQuery({
    queryKey: ["attacks-preview"],
    queryFn: () => api.attacks({ limit: 5 }),
  });

  const timelineData =
    charts?.auth_failures_timeline.map((p) => ({
      label: p.bucket ? new Date(p.bucket).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "",
      count: p.count,
    })) ?? [];

  const cards = [
    { label: "Active attacks", value: metrics?.active_attacks ?? "—" },
    { label: "Open cases", value: metrics?.open_cases ?? "—", href: "/app/cases" },
    { label: "Suspicious IPs", value: metrics?.suspicious_ips ?? "—" },
    { label: "Events (24h)", value: metrics?.events_last_24h ?? "—" },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Security overview</h1>
        <p className="text-muted text-sm mt-1">Brute-force and authentication abuse across connected Wazuh managers.</p>
        {metrics?.last_ingestion_at && (
          <p className="text-[11px] text-muted mt-2 font-mono">
            Last ingestion: {new Date(metrics.last_ingestion_at).toLocaleString()}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {cards.map((m) => (
          <div key={m.label} className="panel p-5">
            <p className="text-xs uppercase tracking-wide text-muted">
              {"href" in m && m.href ? (
                <Link to={m.href} className="hover:text-primary transition">
                  {m.label}
                </Link>
              ) : (
                m.label
              )}
            </p>
            <p className="text-3xl font-semibold mt-2 tabular-nums">{isLoading ? "…" : m.value}</p>
          </div>
        ))}
      </div>

      <div className="grid xl:grid-cols-2 gap-6">
        <div className="panel p-5 min-h-[260px]">
          <h2 className="text-sm font-semibold mb-4">Authentication events (24h)</h2>
          {timelineData.length === 0 ? (
            <p className="text-muted text-sm">No events in the selected window.</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={timelineData}>
                <CartesianGrid stroke={gridStroke} strokeDasharray="3 3" />
                <XAxis dataKey="label" tick={chartTick} interval="preserveStartEnd" />
                <YAxis tick={chartTick} width={32} />
                <Tooltip
                  contentStyle={{ background: "#11161d", border: "1px solid #252f3d", borderRadius: 8 }}
                  labelStyle={{ color: "#8993a3" }}
                />
                <Area type="monotone" dataKey="count" stroke="#5b7cfa" fill="#5b7cfa33" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="panel p-5 min-h-[260px]">
          <h2 className="text-sm font-semibold mb-4">By service</h2>
          {!charts?.by_service.length ? (
            <p className="text-muted text-sm">No service breakdown yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={charts.by_service} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid stroke={gridStroke} strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={chartTick} />
                <YAxis type="category" dataKey="name" tick={chartTick} width={56} />
                <Tooltip contentStyle={{ background: "#11161d", border: "1px solid #252f3d", borderRadius: 8 }} />
                <Bar dataKey="count" fill="#5b7cfa" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="panel p-5">
          <h2 className="text-sm font-semibold mb-3">Sources by country</h2>
          <ul className="text-sm space-y-2">
            {(charts?.by_country ?? []).slice(0, 6).map((c) => (
              <li key={c.name} className="flex justify-between gap-2">
                <Link to={`/app/sources?country=${encodeURIComponent(c.name)}`} className="text-primary hover:underline truncate">
                  {c.name}
                </Link>
                <span className="text-muted tabular-nums">{c.count}</span>
              </li>
            ))}
            {!charts?.by_country?.length && <li className="text-muted text-sm">Run enrichment for country breakdown.</li>}
          </ul>
        </div>
        <div className="panel p-5">
          <h2 className="text-sm font-semibold mb-3">Top targeted hosts</h2>
          <ul className="text-sm space-y-2">
            {(charts?.top_target_hosts ?? []).slice(0, 6).map((h) => (
              <li key={h.name} className="flex justify-between gap-2">
                <Link to={`/app/attacks?host=${encodeURIComponent(h.name)}`} className="truncate text-primary hover:underline">
                  {h.name}
                </Link>
                <span className="text-muted tabular-nums">{h.count}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel p-5">
          <h2 className="text-sm font-semibold mb-3">Top usernames</h2>
          <ul className="text-sm space-y-2 font-mono text-xs">
            {(charts?.top_usernames ?? []).slice(0, 6).map((u) => (
              <li key={u.name} className="flex justify-between gap-2">
                <Link to={`/app/attacks?username=${encodeURIComponent(u.name)}`} className="truncate text-primary hover:underline">
                  {u.name}
                </Link>
                <span className="text-muted tabular-nums">{u.count}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="panel p-6">
        <div className="flex items-center justify-between gap-4 mb-4">
          <h2 className="text-sm font-semibold">Recent attack sessions</h2>
          <Link to="/app/attacks" className="text-xs text-primary hover:underline">
            View all
          </Link>
        </div>
        {!attacks?.items.length ? (
          <p className="text-muted text-sm">No correlated sessions yet.</p>
        ) : (
          <ul className="divide-y divide-[var(--border)] text-sm">
            {attacks.items.map((s) => (
              <li key={s.id} className="py-3 flex flex-wrap items-center justify-between gap-2">
                <Link to={`/app/sources/${encodeURIComponent(s.source_ip)}`} className="font-mono text-primary hover:underline">
                  {s.source_ip}
                </Link>
                <span className="text-muted">{s.attempt_count} attempts</span>
                <span className="capitalize text-xs">{s.risk_level}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
