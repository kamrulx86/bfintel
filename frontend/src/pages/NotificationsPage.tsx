import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";

export default function NotificationsPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("SOC Telegram");
  const [type, setType] = useState<"telegram" | "slack" | "webhook">("telegram");
  const [botToken, setBotToken] = useState("");
  const [chatId, setChatId] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");

  const { data: channels } = useQuery({ queryKey: ["channels"], queryFn: () => api.notificationChannels() });

  const create = useMutation({
    mutationFn: () => {
      let config: Record<string, string> = {};
      if (type === "telegram") config = { bot_token: botToken, chat_id: chatId };
      if (type === "slack") config = { webhook_url: webhookUrl };
      if (type === "webhook") config = { url: webhookUrl };
      return api.createNotificationChannel({ name, channel_type: type, config });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["channels"] });
      setBotToken("");
      setWebhookUrl("");
    },
  });

  const test = useMutation({
    mutationFn: (id: string) => api.testNotificationChannel(id),
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Notifications</h1>
        <p className="text-muted text-sm mt-1">Telegram, Slack, and generic webhooks. Secrets are encrypted at rest.</p>
      </div>

      <div className="panel p-5 space-y-4 max-w-lg">
        <h2 className="text-sm font-semibold">Add channel</h2>
        <label className="block text-xs text-muted">
          Name
          <input className="input-field mt-1" value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label className="block text-xs text-muted">
          Type
          <select className="input-field mt-1" value={type} onChange={(e) => setType(e.target.value as typeof type)}>
            <option value="telegram">Telegram</option>
            <option value="slack">Slack (incoming webhook)</option>
            <option value="webhook">Generic webhook</option>
          </select>
        </label>
        {type === "telegram" && (
          <>
            <label className="block text-xs text-muted">
              Bot token
              <input className="input-field mt-1 font-mono text-xs" value={botToken} onChange={(e) => setBotToken(e.target.value)} />
            </label>
            <label className="block text-xs text-muted">
              Chat ID
              <input className="input-field mt-1 font-mono text-xs" value={chatId} onChange={(e) => setChatId(e.target.value)} />
            </label>
          </>
        )}
        {(type === "slack" || type === "webhook") && (
          <label className="block text-xs text-muted">
            Webhook URL
            <input className="input-field mt-1 font-mono text-xs" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
          </label>
        )}
        <button type="button" className="btn-primary" disabled={create.isPending} onClick={() => create.mutate()}>
          Save channel
        </button>
      </div>

      <div className="panel overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--border)] text-sm font-medium">Configured channels</div>
        <ul className="divide-y divide-[var(--border)]">
          {!channels?.length ? (
            <li className="p-6 text-muted text-sm">No channels configured.</li>
          ) : (
            channels.map((c) => (
              <li key={c.id} className="px-4 py-3 flex items-center justify-between gap-2 text-sm">
                <div>
                  <p className="font-medium">{c.name}</p>
                  <p className="text-xs text-muted capitalize">{c.channel_type}</p>
                </div>
                <button type="button" className="btn-ghost text-xs py-1.5" onClick={() => test.mutate(c.id)} disabled={test.isPending}>
                  Test
                </button>
              </li>
            ))
          )}
        </ul>
        {test.isSuccess && <p className="px-4 py-2 text-xs text-success">Test sent.</p>}
        {test.isError && <p className="px-4 py-2 text-xs text-critical">{(test.error as Error).message}</p>}
      </div>
    </div>
  );
}
