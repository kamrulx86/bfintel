import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useState } from "react";
import { api, AbuseReportOut } from "../lib/api";

function mailtoLink(report: AbuseReportOut) {
  const to = report.recipient_email?.trim();
  const params = new URLSearchParams();
  params.set("subject", report.subject);
  params.set("body", report.body);
  const base = to ? `mailto:${encodeURIComponent(to)}` : "mailto:";
  return `${base}?${params.toString()}`;
}

export default function AbuseReportsPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const { data: reports } = useQuery({
    queryKey: ["abuse-reports", filter],
    queryFn: () => api.abuseReports(filter || undefined),
  });

  const selected = reports?.find((r) => r.id === selectedId) ?? null;

  const selectReport = (r: AbuseReportOut) => {
    setSelectedId(r.id);
    setRecipient(r.recipient_email ?? "");
    setSubject(r.subject);
    setBody(r.body);
  };

  const save = useMutation({
    mutationFn: () =>
      api.updateAbuseReport(selectedId!, {
        recipient_email: recipient.trim() || undefined,
        subject: subject.trim(),
        body,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["abuse-reports"] }),
  });

  const submit = useMutation({
    mutationFn: () => api.submitAbuseReport(selectedId!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["abuse-reports"] }),
  });

  const copyBody = async () => {
    if (!body) return;
    await navigator.clipboard.writeText(body);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Abuse reports</h1>
        <p className="text-muted text-sm mt-1">
          Draft ISP abuse emails from investigation evidence. Send via your mail client, then mark as submitted.
        </p>
      </div>

      <div className="grid xl:grid-cols-2 gap-6">
        <div className="panel overflow-hidden">
          <div className="px-4 py-3 border-b border-[var(--border)] flex items-center gap-2">
            <span className="text-sm font-medium">Reports</span>
            <select className="input-field py-1.5 text-xs ml-auto w-auto" value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="">All statuses</option>
              <option value="draft">Draft</option>
              <option value="submitted">Submitted</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <ul className="divide-y divide-[var(--border)] max-h-[480px] overflow-y-auto">
            {!reports?.length ? (
              <li className="p-6 text-center text-muted text-sm">No abuse reports yet. Create one from a source IP investigation.</li>
            ) : (
              reports.map((r) => (
                <li key={r.id}>
                  <button
                    type="button"
                    onClick={() => selectReport(r)}
                    className={`w-full text-left px-4 py-3 hover:bg-surface2/60 transition ${selectedId === r.id ? "bg-primary/10" : ""}`}
                  >
                    <p className="text-sm font-medium truncate">{r.subject}</p>
                    <p className="text-xs text-muted mt-1 flex flex-wrap gap-2">
                      <span className="font-mono">{r.source_ip}</span>
                      <span className="capitalize">{r.status}</span>
                      {r.isp_name && <span>{r.isp_name}</span>}
                    </p>
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>

        <div className="panel p-5 space-y-4 min-h-[320px]">
          {!selected ? (
            <p className="text-muted text-sm">Select a report to edit recipient, subject, and body.</p>
          ) : (
            <>
              <div className="flex flex-wrap gap-2 text-xs">
                <Link to={`/app/sources/${encodeURIComponent(selected.source_ip)}`} className="text-primary hover:underline font-mono">
                  View investigation
                </Link>
                <span className="text-muted capitalize">· {selected.status}</span>
                {selected.submitted_at && (
                  <span className="text-muted">· Submitted {new Date(selected.submitted_at).toLocaleString()}</span>
                )}
              </div>
              <label className="block text-xs text-muted">
                ISP abuse contact (optional)
                <input className="input-field mt-1 font-mono text-sm" value={recipient} onChange={(e) => setRecipient(e.target.value)} placeholder="abuse@provider.example" />
              </label>
              <label className="block text-xs text-muted">
                Subject
                <input className="input-field mt-1 text-sm" value={subject} onChange={(e) => setSubject(e.target.value)} />
              </label>
              <label className="block text-xs text-muted">
                Body
                <textarea className="input-field mt-1 text-sm font-mono min-h-[220px] w-full" value={body} onChange={(e) => setBody(e.target.value)} />
              </label>
              <div className="flex flex-wrap gap-2">
                <button type="button" className="btn-primary text-xs" disabled={save.isPending} onClick={() => save.mutate()}>
                  Save draft
                </button>
                <a href={mailtoLink({ ...selected, recipient_email: recipient, subject, body })} className="btn-ghost text-xs inline-flex items-center">
                  Open in mail client
                </a>
                <button type="button" className="btn-ghost text-xs" onClick={() => copyBody()}>
                  Copy body
                </button>
                {selected.status === "draft" && (
                  <button type="button" className="btn-ghost text-xs text-success" disabled={submit.isPending} onClick={() => submit.mutate()}>
                    Mark submitted
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
