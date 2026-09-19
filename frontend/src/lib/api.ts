// Empty = same origin (nginx proxies /api → backend). Set VITE_API_BASE_URL only for local Vite dev.
function resolveApiBase(): string {
  const configured = (import.meta.env.VITE_API_BASE_URL ?? "").trim().replace(/\/$/, "");
  if (!configured) return "";
  if (typeof window === "undefined") return configured;
  try {
    const apiHost = new URL(configured.startsWith("http") ? configured : `http://${configured}`).hostname;
    const pageHost = window.location.hostname;
    const apiIsLocal = apiHost === "localhost" || apiHost === "127.0.0.1";
    const pageIsLocal = pageHost === "localhost" || pageHost === "127.0.0.1";
    if (apiIsLocal && !pageIsLocal) return "";
  } catch {
    return configured;
  }
  return configured;
}

const API_BASE = resolveApiBase();

export function getToken(): string | null {
  return localStorage.getItem("bfintel_token");
}

export function setToken(token: string) {
  localStorage.setItem("bfintel_token", token);
}

export function clearToken() {
  localStorage.removeItem("bfintel_token");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail ?? res.statusText;
    throw new Error(res.status >= 500 ? `${res.status} ${detail}` : detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  setupStatus: () => request<{ setup_required: boolean; has_wazuh_connection: boolean }>("/api/setup/status"),
  createAdmin: (body: object) =>
    request<{ access_token: string }>("/api/setup/admin", { method: "POST", body: JSON.stringify(body) }),
  testWazuh: (body: object) => request<object>("/api/setup/wazuh/test", { method: "POST", body: JSON.stringify(body) }),
  saveWazuh: (body: object) => request<object>("/api/setup/wazuh", { method: "POST", body: JSON.stringify(body) }),
  health: () => request<{ status: string; components: Record<string, string> }>("/api/health"),
  login: (body: { email: string; password: string }) =>
    request<{ access_token: string }>("/api/auth/login", { method: "POST", body: JSON.stringify(body) }),
  me: () => request<{ id: string; email: string; full_name: string; role: string }>("/api/auth/me"),
  dashboardMetrics: () =>
    request<{
      active_attacks: number;
      suspicious_ips: number;
      events_last_24h: number;
      high_risk_sources: number;
      open_cases: number;
      last_ingestion_at: string | null;
    }>("/api/dashboard/metrics"),
  dashboardCharts: (hours = 24) => request<DashboardCharts>(`/api/dashboard/charts?hours=${hours}`),
  attacks: (params?: AttackListParams) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    if (params?.status) q.set("status", params.status);
    if (params?.risk_level) q.set("risk_level", params.risk_level);
    if (params?.service) q.set("service", params.service);
    if (params?.source_ip) q.set("source_ip", params.source_ip);
    if (params?.host) q.set("host", params.host);
    if (params?.username) q.set("username", params.username);
    if (params?.hours) q.set("hours", String(params.hours));
    const qs = q.toString();
    return request<{ items: AttackSession[]; total: number }>(`/api/attacks${qs ? `?${qs}` : ""}`);
  },
  sources: (params?: SourceListParams) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    if (params?.hours) q.set("hours", String(params.hours));
    if (params?.risk_level) q.set("risk_level", params.risk_level);
    if (params?.service) q.set("service", params.service);
    if (params?.q) q.set("q", params.q);
    if (params?.country) q.set("country", params.country);
    const qs = q.toString();
    return request<{ items: SourceIntel[]; total: number }>(`/api/sources${qs ? `?${qs}` : ""}`);
  },
  refreshIpIntel: (ip: string) =>
    request<{ status: string }>(`/api/intel/${encodeURIComponent(ip)}/refresh`, { method: "POST" }),
  runIntelEnrichment: (limit = 25) =>
    request<{ status: string; enriched: number }>(`/api/intel/enrich?limit=${limit}`, { method: "POST" }),
  intelProviders: () => request<IntelProviderStatus[]>("/api/intel/providers"),
  ipProfile: (ip: string) => request<IpProfile>(`/api/ip-intelligence/${encodeURIComponent(ip)}`),
  ipTimeline: (ip: string, params?: { hours?: number; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.hours) q.set("hours", String(params.hours));
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return request<{ items: TimelineEvent[]; total: number }>(
      `/api/ip-intelligence/${encodeURIComponent(ip)}/timeline${qs ? `?${qs}` : ""}`,
    );
  },
  search: (q: string) =>
    request<{ query: string; results: SearchHit[] }>(`/api/search?q=${encodeURIComponent(q)}`),
  notificationChannels: () => request<NotificationChannelOut[]>("/api/notifications/channels"),
  createNotificationChannel: (body: { name: string; channel_type: string; config: Record<string, string> }) =>
    request<NotificationChannelOut>("/api/notifications/channels", { method: "POST", body: JSON.stringify(body) }),
  testNotificationChannel: (id: string) =>
    request<{ status: string }>(`/api/notifications/channels/${id}/test`, { method: "POST" }),
  rules: () => request<AutomationRuleOut[]>("/api/rules"),
  ruleTemplates: () => request<RuleTemplateOut[]>("/api/rules/templates"),
  createRuleFromTemplate: (body: { template_id: string; channel_id?: string; name_override?: string; enabled?: boolean }) =>
    request<AutomationRuleOut>("/api/rules/from-template", { method: "POST", body: JSON.stringify(body) }),
  createRule: (body: object) => request<AutomationRuleOut>("/api/rules", { method: "POST", body: JSON.stringify(body) }),
  toggleRule: (id: string) => request<AutomationRuleOut>(`/api/rules/${id}/toggle`, { method: "PATCH" }),
  ruleExecutions: () => request<RuleExecutionOut[]>("/api/rules/executions"),
  evaluateRules: () => request<{ status: string; triggered: number }>("/api/rules/evaluate", { method: "POST" }),
  cases: (status?: string) => {
    const q = status ? `?status=${encodeURIComponent(status)}` : "";
    return request<CaseOut[]>(`/api/cases${q}`);
  },
  createCase: (body: { title: string; severity?: string; priority?: string; source_ip?: string; attack_session_id?: string }) =>
    request<CaseOut>("/api/cases", { method: "POST", body: JSON.stringify(body) }),
  updateCase: (id: string, body: { status?: string; assignee?: string; severity?: string; priority?: string }) =>
    request<CaseOut>(`/api/cases/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  caseNotes: (caseId: string) => request<CaseNoteOut[]>(`/api/cases/${caseId}/notes`),
  addCaseNote: (caseId: string, body: string) =>
    request<CaseNoteOut>(`/api/cases/${caseId}/notes`, { method: "POST", body: JSON.stringify({ body }) }),
  watchlist: () => request<WatchlistOut[]>("/api/watchlist"),
  addWatchlist: (body: { source_ip: string; reason?: string; risk_level?: string; notes?: string }) =>
    request<WatchlistOut>("/api/watchlist", { method: "POST", body: JSON.stringify(body) }),
  removeWatchlist: (id: string) => request<{ status: string }>(`/api/watchlist/${id}`, { method: "DELETE" }),
  allowlist: () => request<AllowlistOut[]>("/api/allowlist"),
  addAllowlist: (body: { value: string; entry_type?: string; description?: string }) =>
    request<AllowlistOut>("/api/allowlist", { method: "POST", body: JSON.stringify(body) }),
  removeAllowlist: (id: string) => request<{ status: string }>(`/api/allowlist/${id}`, { method: "DELETE" }),
  blocklist: () => request<BlocklistOut[]>("/api/blocklist"),
  addBlocklist: (body: { source_ip: string; reason?: string; enforcement_status?: string }) =>
    request<BlocklistOut>("/api/blocklist", { method: "POST", body: JSON.stringify(body) }),
  removeBlocklist: (id: string) => request<{ status: string }>(`/api/blocklist/${id}`, { method: "DELETE" }),
  auditLogs: (limit = 100) => request<AuditLogOut[]>(`/api/audit?limit=${limit}`),
  abuseReports: (status?: string, source_ip?: string) => {
    const q = new URLSearchParams();
    if (status) q.set("status", status);
    if (source_ip) q.set("source_ip", source_ip);
    const qs = q.toString();
    return request<AbuseReportOut[]>(`/api/abuse-reports${qs ? `?${qs}` : ""}`);
  },
  createAbuseReportFromIp: (ip: string, case_id?: string) =>
    request<AbuseReportOut>(`/api/abuse-reports/from-ip/${encodeURIComponent(ip)}`, {
      method: "POST",
      body: JSON.stringify(case_id ? { case_id } : {}),
    }),
  updateAbuseReport: (id: string, body: { status?: string; subject?: string; body?: string; recipient_email?: string }) =>
    request<AbuseReportOut>(`/api/abuse-reports/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  submitAbuseReport: (id: string) => request<AbuseReportOut>(`/api/abuse-reports/${id}/submit`, { method: "POST" }),
};

export type NotificationChannelOut = {
  id: string;
  name: string;
  channel_type: string;
  is_active: boolean;
  created_at: string;
};

export type RuleTemplateOut = {
  id: string;
  name: string;
  description: string;
  category: string;
  severity: string;
  cooldown_minutes: number;
  conditions_summary: string;
  conditions: Record<string, unknown>;
  note?: string | null;
};

export type AutomationRuleOut = {
  id: string;
  name: string;
  enabled: boolean;
  conditions: Record<string, unknown>;
  actions: Record<string, unknown>[];
  cooldown_minutes: number;
  last_triggered_at: string | null;
  created_at: string;
};

export type CaseOut = {
  id: string;
  title: string;
  severity: string;
  priority: string;
  status: string;
  assignee: string | null;
  source_ip: string | null;
  attack_session_id: string | null;
  created_at: string;
  updated_at: string;
};

export type CaseNoteOut = {
  id: string;
  body: string;
  created_at: string;
};

export type WatchlistOut = {
  id: string;
  source_ip: string;
  reason: string | null;
  risk_level: string;
  notes: string | null;
  expires_at: string | null;
  created_at: string;
};

export type AllowlistOut = {
  id: string;
  value: string;
  entry_type: string;
  description: string | null;
  created_at: string;
};

export type BlocklistOut = {
  id: string;
  source_ip: string;
  reason: string | null;
  enforcement_status: string;
  expires_at: string | null;
  created_at: string;
};

export type AbuseReportOut = {
  id: string;
  source_ip: string;
  case_id: string | null;
  status: string;
  subject: string;
  body: string;
  recipient_email: string | null;
  isp_name: string | null;
  asn: string | null;
  template_key: string;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AuditLogOut = {
  id: string;
  action: string;
  target: string | null;
  result: string;
  ip_address: string | null;
  created_at: string;
};

export type RuleExecutionOut = {
  id: string;
  rule_id: string;
  source_ip: string | null;
  result: string;
  detail: string | null;
  created_at: string;
};

export type AttackListParams = {
  limit?: number;
  offset?: number;
  status?: string;
  risk_level?: string;
  service?: string;
  source_ip?: string;
  host?: string;
  username?: string;
  hours?: number;
};

export type SourceListParams = {
  limit?: number;
  offset?: number;
  hours?: number;
  risk_level?: string;
  service?: string;
  q?: string;
  country?: string;
};

export type IntelProviderStatus = {
  name: string;
  enabled: boolean;
  configured: boolean;
  description: string;
};

export type DashboardCharts = {
  hours: number;
  auth_failures_timeline: { bucket: string; count: number }[];
  by_service: { name: string; count: number }[];
  by_country: { name: string; count: number }[];
  top_target_hosts: { name: string; count: number }[];
  top_usernames: { name: string; count: number }[];
  unique_source_ips: number;
};

export type GeoIntel = {
  country_code: string | null;
  country_name: string | null;
  region: string | null;
  city: string | null;
  latitude: number | null;
  longitude: number | null;
  asn: string | null;
  isp: string | null;
  organization_name: string | null;
  reverse_dns: string | null;
  is_hosting: boolean | null;
  network_scope: string | null;
  last_enriched_at: string | null;
  enrichment_status: string | null;
};

export type ProviderSnapshot = {
  provider: string;
  success: boolean;
  fetched_at: string;
  data: Record<string, unknown>;
  error: string | null;
};

export type TimelineEvent = {
  id: string;
  timestamp: string;
  username: string | null;
  service: string | null;
  target_host: string | null;
  authentication_result: string | null;
  rule_id: string | null;
  rule_description: string | null;
  wazuh_event_id: string;
};

export type IpProfile = {
  source_ip: string;
  network_scope: string;
  first_seen: string | null;
  last_seen: string | null;
  total_events: number;
  failure_count: number;
  success_count: number;
  session_count: number;
  max_risk_score: number;
  max_risk_level: string;
  target_hosts: string[];
  services: string[];
  usernames: string[];
  risk_reasons: string[];
  sessions: AttackSession[];
  geo: GeoIntel | null;
  threat_intel: ProviderSnapshot[];
  geo_placeholder: boolean;
};

export type SearchHit = {
  type: string;
  label: string;
  href: string;
  meta: string | null;
};

export type AttackSession = {
  id: string;
  source_ip: string;
  first_seen: string;
  last_seen: string;
  attempt_count: number;
  successful_attempt_count: number;
  target_count: number;
  target_hosts: string[];
  services: string[];
  usernames: string[];
  risk_score: number;
  risk_level: string;
  status: string;
  attack_type: string;
};

export type SourceIntel = {
  source_ip: string;
  session_count: number;
  total_attempts: number;
  max_risk_score: number;
  max_risk_level: string;
  last_seen: string;
  services: string[];
  country_code?: string | null;
  country_name?: string | null;
  asn?: string | null;
  isp?: string | null;
};
