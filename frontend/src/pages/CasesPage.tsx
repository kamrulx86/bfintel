import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useState } from "react";
import { api, CaseOut } from "../lib/api";

const statuses = ["new", "investigating", "contained", "resolved", "closed"];

function statusBadge(status: string) {
  if (status === "closed" || status === "resolved") return "text-success";
  if (status === "investigating") return "text-warning";
  return "text-primary";
}

export default function CasesPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<string>("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [sourceIp, setSourceIp] = useState("");
  const [noteBody, setNoteBody] = useState("");

  const { data: cases } = useQuery({
    queryKey: ["cases", filter],
    queryFn: () => api.cases(filter || undefined),
  });

  const selected = cases?.find((c) => c.id === selectedId) ?? null;

  const { data: notes } = useQuery({
    queryKey: ["case-notes", selectedId],
    queryFn: () => api.caseNotes(selectedId!),
    enabled: !!selectedId,
  });

  const createCase = useMutation({
    mutationFn: () =>
      api.createCase({
        title: title.trim(),
        source_ip: sourceIp.trim() || undefined,
        severity: "medium",
        priority: "normal",
      }),
    onSuccess: (c) => {
      setTitle("");
      setSourceIp("");
      qc.invalidateQueries({ queryKey: ["cases"] });
      qc.invalidateQueries({ queryKey: ["dashboard-metrics"] });
      setSelectedId(c.id);
    },
  });

  const updateCase = useMutation({
    mutationFn: (patch: { id: string; status?: string; assignee?: string }) =>
      api.updateCase(patch.id, { status: patch.status, assignee: patch.assignee }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cases"] });
      qc.invalidateQueries({ queryKey: ["dashboard-metrics"] });
    },
  });

  const addNote = useMutation({
    mutationFn: () => api.addCaseNote(selectedId!, noteBody.trim()),
    onSuccess: () => {
      setNoteBody("");
      qc.invalidateQueries({ queryKey: ["case-notes", selectedId] });
    },
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Cases</h1>
        <p className="text-muted text-sm mt-1">Track investigations from brute-force signals to resolution.</p>
      </div>

      <div className="panel p-5 max-w-xl space-y-3">
        <h2 className="text-sm font-semibold">Open case</h2>
        <label className="block text-xs text-muted">
          Title
          <input className="input-field mt-1" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="SSH brute force — prod bastion" />
        </label>
        <label className="block text-xs text-muted">
          Source IP (optional)
          <input className="input-field mt-1 font-mono" value={sourceIp} onChange={(e) => setSourceIp(e.target.value)} placeholder="203.0.113.10" />
        </label>
        <button type="button" className="btn-primary" disabled={!title.trim() || createCase.isPending} onClick={() => createCase.mutate()}>
          Create case
        </button>
      </div>

      <div className="grid xl:grid-cols-2 gap-6">
        <div className="panel overflow-hidden">
          <div className="px-4 py-3 border-b border-[var(--border)] flex flex-wrap gap-2 items-center">
            <span className="text-sm font-medium">All cases</span>
            <select className="input-field py-1.5 text-xs ml-auto w-auto" value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="">Any status</option>
              {statuses.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <ul className="divide-y divide-[var(--border)] max-h-[420px] overflow-y-auto">
            {!cases?.length ? (
              <li className="p-6 text-center text-muted text-sm">No cases yet.</li>
            ) : (
              cases.map((c: CaseOut) => (
                <li key={c.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(c.id)}
                    className={`w-full text-left px-4 py-3 hover:bg-surface2/60 transition ${selectedId === c.id ? "bg-primary/10" : ""}`}
                  >
                    <p className="font-medium text-sm truncate">{c.title}</p>
                    <p className="text-xs text-muted mt-1 flex flex-wrap gap-2">
                      <span className={statusBadge(c.status)}>{c.status}</span>
                      {c.source_ip && (
                        <Link to={`/app/sources/${encodeURIComponent(c.source_ip)}`} className="font-mono text-primary hover:underline" onClick={(e) => e.stopPropagation()}>
                          {c.source_ip}
                        </Link>
                      )}
                      <span>{new Date(c.updated_at).toLocaleString()}</span>
                    </p>
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>

        <div className="panel p-5 min-h-[320px]">
          {!selected ? (
            <p className="text-muted text-sm">Select a case to view details and notes.</p>
          ) : (
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-semibold">{selected.title}</h2>
                <p className="text-xs text-muted mt-1">Created {new Date(selected.created_at).toLocaleString()}</p>
              </div>
              <div className="flex flex-wrap gap-3 text-sm">
                <label className="text-xs text-muted">
                  Status
                  <select
                    className="input-field mt-1 block"
                    value={selected.status}
                    onChange={(e) => updateCase.mutate({ id: selected.id, status: e.target.value })}
                  >
                    {statuses.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs text-muted flex-1 min-w-[160px]">
                  Assignee
                  <input
                    className="input-field mt-1"
                    defaultValue={selected.assignee ?? ""}
                    placeholder="analyst@org"
                    onBlur={(e) => {
                      const v = e.target.value.trim();
                      if (v !== (selected.assignee ?? "")) updateCase.mutate({ id: selected.id, assignee: v || undefined });
                    }}
                  />
                </label>
              </div>
              <div>
                <h3 className="text-sm font-semibold mb-2">Notes</h3>
                <ul className="space-y-2 text-sm max-h-40 overflow-y-auto mb-3">
                  {!notes?.length ? (
                    <li className="text-muted">No notes yet.</li>
                  ) : (
                    notes.map((n) => (
                      <li key={n.id} className="border border-[var(--border)] rounded-lg p-3">
                        <p className="text-xs text-muted mb-1">{new Date(n.created_at).toLocaleString()}</p>
                        <p className="whitespace-pre-wrap">{n.body}</p>
                      </li>
                    ))
                  )}
                </ul>
                <textarea
                  className="input-field min-h-[80px] text-sm w-full"
                  value={noteBody}
                  onChange={(e) => setNoteBody(e.target.value)}
                  placeholder="Investigation update…"
                />
                <button type="button" className="btn-ghost text-xs mt-2" disabled={!noteBody.trim() || addNote.isPending} onClick={() => addNote.mutate()}>
                  Add note
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
