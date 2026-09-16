import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AuthLayout from "../layouts/AuthLayout";
import { api, clearToken, setToken } from "../lib/api";

type TestResult = {
  success: boolean;
  details: string[];
  api_version?: string;
};

export default function SetupWizard({
  onComplete,
  initialStep = 1,
}: {
  onComplete: () => void;
  initialStep?: number;
}) {
  const navigate = useNavigate();
  const [step, setStep] = useState(initialStep);
  const [error, setError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [admin, setAdmin] = useState({
    organization_name: "The Team Phoenix",
    full_name: "",
    email: "",
    password: "",
  });
  const [wazuh, setWazuh] = useState({
    api_url: "https://192.168.122.186:55000",
    api_username: "",
    api_password: "",
    indexer_url: "",
    verify_tls: false,
  });

  async function submitAdmin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const res = await api.createAdmin(admin);
      setToken(res.access_token);
      setStep(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    }
  }

  async function runTest() {
    setError(null);
    setTestResult(null);
    try {
      const res = (await api.testWazuh(wazuh)) as TestResult;
      setTestResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Test failed");
    }
  }

  async function saveWazuh(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.saveWazuh({ ...wazuh, name: "Primary" });
      clearToken();
      onComplete();
      navigate("/login", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  }

  const title = step === 1 ? "Initial setup" : "Connect Wazuh";
  const subtitle =
    step === 1
      ? "Step 1 of 2 — Create the first administrator account."
      : "Step 2 of 2 — Link your Wazuh manager and test connectivity.";

  return (
    <AuthLayout title={title} subtitle={subtitle} wide>
      <div className="flex gap-2 mb-6">
        {[1, 2].map((s) => (
          <div
            key={s}
            className={`h-1 flex-1 rounded-full ${s <= step ? "bg-primary" : "bg-surface2"}`}
          />
        ))}
      </div>

      {step === 1 && (
        <form onSubmit={submitAdmin} className="space-y-4">
          <Field label="Organization" value={admin.organization_name} onChange={(v) => setAdmin({ ...admin, organization_name: v })} />
          <Field label="Full name" value={admin.full_name} onChange={(v) => setAdmin({ ...admin, full_name: v })} />
          <Field label="Email" type="email" value={admin.email} onChange={(v) => setAdmin({ ...admin, email: v })} />
          <Field label="Password (min 12 characters)" type="password" value={admin.password} onChange={(v) => setAdmin({ ...admin, password: v })} />
          <button type="submit" className="btn-primary w-full py-3">
            Continue
          </button>
        </form>
      )}

      {step === 2 && (
        <form onSubmit={saveWazuh} className="space-y-4">
          <Field label="Wazuh API URL" value={wazuh.api_url} onChange={(v) => setWazuh({ ...wazuh, api_url: v })} mono />
          <Field label="API username" value={wazuh.api_username} onChange={(v) => setWazuh({ ...wazuh, api_username: v })} />
          <Field label="API password" type="password" value={wazuh.api_password} onChange={(v) => setWazuh({ ...wazuh, api_password: v })} />
          <Field label="Indexer URL (optional)" value={wazuh.indexer_url} onChange={(v) => setWazuh({ ...wazuh, indexer_url: v })} mono />
          <label className="flex items-center gap-2 text-sm text-muted">
            <input type="checkbox" className="rounded border-[var(--border)]" checked={wazuh.verify_tls} onChange={(e) => setWazuh({ ...wazuh, verify_tls: e.target.checked })} />
            Verify TLS certificates
          </label>
          <button type="button" onClick={runTest} className="btn-ghost w-full">
            Test connection
          </button>
          {testResult && (
            <div className={`text-sm rounded-lg p-3 border ${testResult.success ? "bg-success/10 border-success/30 text-success" : "bg-critical/10 border-critical/30 text-critical"}`}>
              <p className="font-medium mb-1">{testResult.success ? "Connection successful" : "Connection failed"}</p>
              <ul className="list-disc pl-5 space-y-0.5 font-mono text-xs opacity-90">
                {testResult.details?.map((d) => (
                  <li key={d}>{d}</li>
                ))}
              </ul>
            </div>
          )}
          <button type="submit" className="btn-primary w-full py-3">
            Save & finish setup
          </button>
        </form>
      )}

      {error && <p className="mt-4 text-sm text-critical">{error}</p>}
    </AuthLayout>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  mono,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  mono?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-muted uppercase tracking-wide">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`input-field mt-1.5 ${mono ? "font-mono text-[13px]" : ""}`}
      />
    </label>
  );
}
