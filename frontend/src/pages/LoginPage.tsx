import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AuthLayout from "../layouts/AuthLayout";
import { api, setToken } from "../lib/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.login({ email, password });
      setToken(res.access_token);
      navigate("/app", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Sign in" subtitle="Use your BFIntel administrator or analyst account.">
      <form onSubmit={onSubmit} className="space-y-5">
        <label className="block">
          <span className="text-xs font-medium text-muted uppercase tracking-wide">Email</span>
          <input
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-field mt-1.5"
            placeholder="you@organization.com"
          />
        </label>
        <label className="block">
          <span className="text-xs font-medium text-muted uppercase tracking-wide">Password</span>
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field mt-1.5 font-mono text-[13px]"
            placeholder="••••••••••••"
          />
        </label>
        {error && (
          <p className="text-sm text-critical bg-critical/10 border border-critical/20 rounded-lg px-3 py-2">{error}</p>
        )}
        <button type="submit" disabled={loading} className="btn-primary w-full py-3">
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="text-center text-xs text-muted mt-6">
        Sessions are audited. Contact your SOC admin if you need access.
      </p>
    </AuthLayout>
  );
}
