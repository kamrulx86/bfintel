import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";

const defaultConditions = {
  all: [
    { field: "risk_score", op: "gte", value: 60 },
    { field: "attempt_count", op: "gte", value: 5 },
  ],
};

export default function RulesPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("High-risk brute force");
  const [channelId, setChannelId] = useState("");

  const { data: rules } = useQuery({ queryKey: ["rules"], queryFn: () => api.rules() });
  const { data: channels } = useQuery({ queryKey: ["channels"], queryFn: () => api.notificationChannels() });
  const { data: executions } = useQuery({ queryKey: ["rule-executions"], queryFn: () => api.ruleExecutions() });

  const createRule = useMutation({
    mutationFn: () =>
      api.createRule({
        name,
        conditions: defaultConditions,
        actions: channelId ? [{ type: "notify", channel_id: channelId }] : [],
        cooldown_minutes: 15,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });

  const toggle = useMutation({
    mutationFn: (id: string) => api.toggleRule(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });

  const evaluate = useMutation({
    mutationFn: () => api.evaluateRules(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rule-executions"] }),
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Automation rules</h1>
        <p className="text-muted text-sm mt-1">WHEN conditions match an attack session THEN notify configured channels.</p>
      </div>

      <div className="panel p-5 space-y-4 max-w-xl">
        <h2 className="text-sm font-semibold">Create rule (template)</h2>
        <label className="block text-xs text-muted">
          Name
          <input className="input-field mt-1" value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label className="block text-xs text-muted">
          Notify channel
          <select className="input-field mt-1" value={channelId} onChange={(e) => setChannelId(e.target.value)}>
            <option value="">Select channel…</option>
            {(channels || []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.channel_type})
              </option>
            ))}
          </select>
        </label>
        <p className="text-[11px] text-muted font-mono">
          Conditions: risk_score ≥ 60 AND attempt_count ≥ 5 (active sessions)
        </p>
        <button type="button" className="btn-primary" disabled={!channelId || createRule.isPending} onClick={() => createRule.mutate()}>
          Create rule
        </button>
      </div>

      <div className="panel overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--border)] flex justify-between items-center">
          <span className="text-sm font-medium">Rules</span>
          <button type="button" className="btn-ghost text-xs py-1.5" onClick={() => evaluate.mutate()} disabled={evaluate.isPending}>
            Run evaluation now
          </button>
        </div>
        <ul className="divide-y divide-[var(--border)]">
          {!rules?.length ? (
            <li className="p-6 text-muted text-sm">No rules yet.</li>
          ) : (
            rules.map((r) => (
              <li key={r.id} className="px-4 py-3 flex flex-wrap items-center justify-between gap-2 text-sm">
                <div>
                  <p className="font-medium">{r.name}</p>
                  <p className="text-xs text-muted font-mono">{r.enabled ? "Enabled" : "Disabled"} · cooldown {r.cooldown_minutes}m</p>
                </div>
                <button type="button" className="btn-ghost text-xs py-1.5" onClick={() => toggle.mutate(r.id)}>
                  {r.enabled ? "Disable" : "Enable"}
                </button>
              </li>
            ))
          )}
        </ul>
      </div>

      <div className="panel overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--border)] text-sm font-medium">Recent executions</div>
        <ul className="divide-y divide-[var(--border)] text-sm">
          {!executions?.length ? (
            <li className="p-6 text-muted">No executions yet.</li>
          ) : (
            executions.slice(0, 20).map((e) => (
              <li key={e.id} className="px-4 py-2 flex justify-between gap-2 font-mono text-xs">
                <span>{e.source_ip}</span>
                <span className="text-muted">{e.result}</span>
                <span className="text-muted">{new Date(e.created_at).toLocaleString()}</span>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}
