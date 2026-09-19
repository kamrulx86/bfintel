import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import PageHeader from "../components/PageHeader";
import SectionCard from "../components/SectionCard";
import { api, type RuleTemplateOut } from "../lib/api";

function severityBadge(severity: string) {
  if (severity === "critical") return "badge-critical";
  if (severity === "high") return "badge-high";
  if (severity === "medium") return "badge-medium";
  return "badge-low";
}

function categoryLabel(cat: string) {
  return cat.replace(/_/g, " ");
}

export default function RulesPage() {
  const qc = useQueryClient();
  const [channelId, setChannelId] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");

  const { data: templates, isLoading: templatesLoading } = useQuery({
    queryKey: ["rule-templates"],
    queryFn: () => api.ruleTemplates(),
  });
  const { data: rules } = useQuery({ queryKey: ["rules"], queryFn: () => api.rules() });
  const { data: channels } = useQuery({ queryKey: ["channels"], queryFn: () => api.notificationChannels() });
  const { data: executions } = useQuery({ queryKey: ["rule-executions"], queryFn: () => api.ruleExecutions() });

  const categories = useMemo(() => {
    const set = new Set((templates || []).map((t) => t.category));
    return ["all", ...Array.from(set).sort()];
  }, [templates]);

  const filteredTemplates = useMemo(() => {
    if (!templates) return [];
    if (categoryFilter === "all") return templates;
    return templates.filter((t) => t.category === categoryFilter);
  }, [templates, categoryFilter]);

  const importTemplate = useMutation({
    mutationFn: (tpl: RuleTemplateOut) =>
      api.createRuleFromTemplate({
        template_id: tpl.id,
        channel_id: channelId || undefined,
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

  const channelSelect = (
    <label className="block text-xs text-muted w-full sm:max-w-xs">
      Notify channel
      <select className="input-field mt-1.5" value={channelId} onChange={(e) => setChannelId(e.target.value)}>
        <option value="">No channel (disabled rule)</option>
        {(channels || []).map((c) => (
          <option key={c.id} value={c.id}>
            {c.name} · {c.channel_type}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <>
      <PageHeader
        title="Automation rules"
        description="Import templates, attach notification channels, and manage active session triggers."
        actions={
          <button type="button" className="btn-ghost text-xs w-full sm:w-auto" onClick={() => evaluate.mutate()} disabled={evaluate.isPending}>
            Run evaluation
          </button>
        }
      />

      <SectionCard
        title="Template library"
        description="Choose a preset, then import. Add a Telegram, Slack, or webhook channel first under Notifications."
        actions={channelSelect}
      >
        <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
          {categories.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setCategoryFilter(c)}
              className={`text-xs px-3 py-2 rounded-lg border whitespace-nowrap shrink-0 transition ${
                categoryFilter === c
                  ? "border-primary/40 bg-primary/12 text-text"
                  : "border-[var(--border)] text-muted hover:text-text hover:bg-surface2"
              }`}
            >
              {c === "all" ? "All" : categoryLabel(c)}
            </button>
          ))}
        </div>

        {templatesLoading ? (
          <p className="text-muted text-sm py-6 text-center">Loading templates…</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            {filteredTemplates.map((tpl) => (
              <article key={tpl.id} className="template-card">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-sm leading-snug pr-2">{tpl.name}</h3>
                  <span className={severityBadge(tpl.severity)}>{tpl.severity}</span>
                </div>
                <p className="text-xs text-muted leading-relaxed">{tpl.description}</p>
                <p className="text-[11px] font-mono text-muted bg-bg rounded-lg px-2.5 py-2 border border-[var(--border)] break-words">
                  {tpl.conditions_summary}
                </p>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mt-auto pt-1">
                  <span className="text-[10px] uppercase tracking-wide text-muted">{categoryLabel(tpl.category)}</span>
                  <button
                    type="button"
                    className="btn-primary text-xs py-2 w-full sm:w-auto"
                    disabled={importTemplate.isPending}
                    onClick={() => importTemplate.mutate(tpl)}
                  >
                    Import template
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </SectionCard>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <section className="panel overflow-hidden">
          <div className="px-4 sm:px-5 py-4 border-b border-[var(--border)] flex justify-between items-center gap-2">
            <h2 className="text-sm font-semibold">Active rules</h2>
            <span className="text-xs text-muted shrink-0">{rules?.length ?? 0} total</span>
          </div>
          {!rules?.length ? (
            <p className="p-6 text-muted text-sm text-center">Import a template to create your first rule.</p>
          ) : (
            <ul className="divide-y divide-[var(--border)]">
              {rules.map((r) => (
                <li key={r.id} className="px-4 sm:px-5 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-medium text-sm">{r.name}</p>
                    <p className="text-xs text-muted mt-0.5">
                      Cooldown {r.cooldown_minutes}m · {Array.isArray(r.actions) ? r.actions.length : 0} action(s)
                    </p>
                  </div>
                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <span className={r.enabled ? "badge-success" : "badge-low"}>{r.enabled ? "On" : "Off"}</span>
                    <button type="button" className="btn-ghost text-xs py-2 flex-1 sm:flex-none" onClick={() => toggle.mutate(r.id)}>
                      {r.enabled ? "Disable" : "Enable"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel overflow-hidden">
          <div className="px-4 sm:px-5 py-4 border-b border-[var(--border)]">
            <h2 className="text-sm font-semibold">Recent executions</h2>
          </div>
          {!executions?.length ? (
            <p className="p-6 text-muted text-sm text-center">No rule runs yet.</p>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Source IP</th>
                    <th>Result</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {executions.slice(0, 15).map((e) => (
                    <tr key={e.id}>
                      <td className="font-mono text-xs">{e.source_ip ?? "—"}</td>
                      <td className="text-xs">{e.result}</td>
                      <td className="text-xs text-muted">{new Date(e.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </>
  );
}
