import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";

type Tab = "watchlist" | "allowlist" | "blocklist" | "audit";

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("watchlist");
  const qc = useQueryClient();

  const { data: watchlist } = useQuery({ queryKey: ["watchlist"], queryFn: () => api.watchlist(), enabled: tab === "watchlist" });
  const { data: allowlist } = useQuery({ queryKey: ["allowlist"], queryFn: () => api.allowlist(), enabled: tab === "allowlist" });
  const { data: blocklist } = useQuery({ queryKey: ["blocklist"], queryFn: () => api.blocklist(), enabled: tab === "blocklist" });
  const { data: audit } = useQuery({ queryKey: ["audit"], queryFn: () => api.auditLogs(), enabled: tab === "audit" });

  const [watchIp, setWatchIp] = useState("");
  const [watchReason, setWatchReason] = useState("");
  const [allowValue, setAllowValue] = useState("");
  const [allowType, setAllowType] = useState<"ip" | "cidr">("ip");
  const [blockIp, setBlockIp] = useState("");
  const [blockReason, setBlockReason] = useState("");

  const addWatch = useMutation({
    mutationFn: () => api.addWatchlist({ source_ip: watchIp.trim(), reason: watchReason.trim() || undefined }),
    onSuccess: () => {
      setWatchIp("");
      setWatchReason("");
      qc.invalidateQueries({ queryKey: ["watchlist"] });
    },
  });

  const addAllow = useMutation({
    mutationFn: () => api.addAllowlist({ value: allowValue.trim(), entry_type: allowType }),
    onSuccess: () => {
      setAllowValue("");
      qc.invalidateQueries({ queryKey: ["allowlist"] });
    },
  });

  const addBlock = useMutation({
    mutationFn: () => api.addBlocklist({ source_ip: blockIp.trim(), reason: blockReason.trim() || undefined }),
    onSuccess: () => {
      setBlockIp("");
      setBlockReason("");
      qc.invalidateQueries({ queryKey: ["blocklist"] });
    },
  });

  const removeWatch = useMutation({
    mutationFn: (id: string) => api.removeWatchlist(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["watchlist"] }),
  });

  const removeAllow = useMutation({
    mutationFn: (id: string) => api.removeAllowlist(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["allowlist"] }),
  });

  const removeBlock = useMutation({
    mutationFn: (id: string) => api.removeBlocklist(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["blocklist"] }),
  });

  const tabs: { id: Tab; label: string }[] = [
    { id: "watchlist", label: "Watchlist" },
    { id: "allowlist", label: "Allowlist" },
    { id: "blocklist", label: "Blocklist" },
    { id: "audit", label: "Audit log" },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-muted text-sm mt-1">SOC lists and audit trail. Allowlisted IPs skip automation rule notifications.</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
              tab === t.id ? "bg-primary/15 text-text ring-1 ring-primary/25" : "text-muted hover:text-text hover:bg-surface2/80"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "watchlist" && (
        <div className="space-y-4">
          <div className="panel p-5 max-w-xl space-y-3">
            <h2 className="text-sm font-semibold">Add to watchlist</h2>
            <input className="input-field font-mono" placeholder="Source IP" value={watchIp} onChange={(e) => setWatchIp(e.target.value)} />
            <input className="input-field" placeholder="Reason (optional)" value={watchReason} onChange={(e) => setWatchReason(e.target.value)} />
            <button type="button" className="btn-primary" disabled={!watchIp.trim() || addWatch.isPending} onClick={() => addWatch.mutate()}>
              Add
            </button>
          </div>
          <ListTable
            headers={["IP", "Risk", "Reason", ""]}
            rows={(watchlist ?? []).map((e) => [
              e.source_ip,
              e.risk_level,
              e.reason || "—",
              <button key={e.id} type="button" className="text-xs text-critical hover:underline" onClick={() => removeWatch.mutate(e.id)}>
                Remove
              </button>,
            ])}
          />
        </div>
      )}

      {tab === "allowlist" && (
        <div className="space-y-4">
          <div className="panel p-5 max-w-xl space-y-3">
            <h2 className="text-sm font-semibold">Add to allowlist (admin)</h2>
            <select className="input-field" value={allowType} onChange={(e) => setAllowType(e.target.value as "ip" | "cidr")}>
              <option value="ip">Single IP</option>
              <option value="cidr">CIDR</option>
            </select>
            <input className="input-field font-mono" placeholder={allowType === "cidr" ? "10.0.0.0/8" : "203.0.113.1"} value={allowValue} onChange={(e) => setAllowValue(e.target.value)} />
            <button type="button" className="btn-primary" disabled={!allowValue.trim() || addAllow.isPending} onClick={() => addAllow.mutate()}>
              Add
            </button>
          </div>
          <ListTable
            headers={["Value", "Type", ""]}
            rows={(allowlist ?? []).map((e) => [
              e.value,
              e.entry_type,
              <button key={e.id} type="button" className="text-xs text-critical hover:underline" onClick={() => removeAllow.mutate(e.id)}>
                Remove
              </button>,
            ])}
          />
        </div>
      )}

      {tab === "blocklist" && (
        <div className="space-y-4">
          <div className="panel p-5 max-w-xl space-y-3">
            <h2 className="text-sm font-semibold">Add to blocklist</h2>
            <p className="text-[11px] text-muted">Stored for response workflow; enforcement is internal-only until integrated with your edge firewall.</p>
            <input className="input-field font-mono" placeholder="Source IP" value={blockIp} onChange={(e) => setBlockIp(e.target.value)} />
            <input className="input-field" placeholder="Reason" value={blockReason} onChange={(e) => setBlockReason(e.target.value)} />
            <button type="button" className="btn-primary" disabled={!blockIp.trim() || addBlock.isPending} onClick={() => addBlock.mutate()}>
              Add
            </button>
          </div>
          <ListTable
            headers={["IP", "Status", "Reason", ""]}
            rows={(blocklist ?? []).map((e) => [
              e.source_ip,
              e.enforcement_status,
              e.reason || "—",
              <button key={e.id} type="button" className="text-xs text-critical hover:underline" onClick={() => removeBlock.mutate(e.id)}>
                Remove
              </button>,
            ])}
          />
        </div>
      )}

      {tab === "audit" && (
        <div className="panel overflow-hidden">
          <table className="w-full text-sm">
            <thead className="text-xs uppercase text-muted bg-surface2/50">
              <tr>
                <th className="text-left py-3 px-4">Time</th>
                <th className="text-left py-3 px-4">Action</th>
                <th className="text-left py-3 px-4">Target</th>
                <th className="text-left py-3 px-4">Result</th>
              </tr>
            </thead>
            <tbody>
              {!audit?.length ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-muted">
                    No audit entries.
                  </td>
                </tr>
              ) : (
                audit.map((row) => (
                  <tr key={row.id} className="border-t border-[var(--border)]">
                    <td className="py-2 px-4 font-mono text-xs text-muted">{new Date(row.created_at).toLocaleString()}</td>
                    <td className="py-2 px-4">{row.action}</td>
                    <td className="py-2 px-4 font-mono text-xs">{row.target || "—"}</td>
                    <td className="py-2 px-4 capitalize">{row.result}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function ListTable({ headers, rows }: { headers: string[]; rows: (string | ReactNode)[][] }) {
  return (
    <div className="panel overflow-hidden">
      <table className="w-full text-sm">
        <thead className="text-xs uppercase text-muted bg-surface2/50">
          <tr>
            {headers.map((h) => (
              <th key={h || "action"} className="text-left py-3 px-4">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={headers.length} className="py-8 text-center text-muted">
                No entries.
              </td>
            </tr>
          ) : (
            rows.map((cells, i) => (
              <tr key={i} className="border-t border-[var(--border)]">
                {cells.map((cell, j) => (
                  <td key={j} className={`py-2 px-4 ${j === 0 ? "font-mono text-xs" : ""}`}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
