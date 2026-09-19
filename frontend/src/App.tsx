import { useQuery } from "@tanstack/react-query";
import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import { api, getToken } from "./lib/api";
import LoginPage from "./pages/LoginPage";
import AttacksPage from "./pages/AttacksPage";
import OverviewPage from "./pages/OverviewPage";
import NotificationsPage from "./pages/NotificationsPage";
import AbuseReportsPage from "./pages/AbuseReportsPage";
import CasesPage from "./pages/CasesPage";
import SettingsPage from "./pages/SettingsPage";
import RulesPage from "./pages/RulesPage";
import SourceInvestigationPage from "./pages/SourceInvestigationPage";
import SourcesPage from "./pages/SourcesPage";
import SetupWizard from "./pages/SetupWizard";

function LoadingScreen() {
  return (
    <div className="min-h-screen grid place-items-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
        <p className="text-muted text-sm">Loading BFIntel…</p>
      </div>
    </div>
  );
}

function ApiError({ onRetry, hint }: { onRetry: () => void; hint?: string }) {
  return (
    <div className="min-h-screen grid place-items-center p-6">
      <div className="panel p-8 max-w-md text-center">
        <p className="text-critical font-medium">Cannot reach BFIntel API</p>
        <p className="text-muted text-sm mt-2">
          Open BFIntel through the <span className="font-mono">nginx</span> entrypoint (same host/port you use in the browser).
          The Vite dev port <span className="font-mono">5173</span> does not proxy <span className="font-mono">/api</span> unless configured.
        </p>
        {hint && <p className="text-xs text-warning mt-3">{hint}</p>}
        <button type="button" onClick={onRetry} className="btn-primary mt-5">
          Retry
        </button>
      </div>
    </div>
  );
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = getToken();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["me", token],
    queryFn: () => api.me(),
    enabled: !!token,
    retry: false,
  });

  if (!token) return <Navigate to="/login" replace />;
  if (isLoading) return <LoadingScreen />;
  if (isError || !data) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  const { data: setup, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["setup-status"],
    queryFn: () => api.setupStatus(),
    retry: 3,
    retryDelay: (n) => Math.min(2000 * (n + 1), 8000),
  });

  if (isLoading) return <LoadingScreen />;
  if (isError || !setup) {
    const msg = error instanceof Error ? error.message : "";
    const hint =
      msg.includes("500") || msg.includes("Internal")
        ? "Server error — often the lab disk or database was full. Free disk space on the host and retry."
        : undefined;
    return <ApiError onRetry={() => refetch()} hint={hint} />;
  }

  const needsSetup = setup.setup_required || !setup.has_wazuh_connection;

  return (
    <Routes>
      <Route
        path="/setup"
        element={
          needsSetup ? (
            <SetupWizard
              initialStep={setup.setup_required ? 1 : 2}
              onComplete={() => refetch()}
            />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/login"
        element={needsSetup ? <Navigate to="/setup" replace /> : <LoginPage />}
      />
      <Route
        path="/app"
        element={
          needsSetup ? (
            <Navigate to="/setup" replace />
          ) : (
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          )
        }
      >
        <Route index element={<OverviewPage />} />
        <Route path="attacks" element={<AttacksPage />} />
        <Route path="sources" element={<SourcesPage />} />
        <Route path="sources/:ip" element={<SourceInvestigationPage />} />
        <Route path="cases" element={<CasesPage />} />
        <Route path="abuse-reports" element={<AbuseReportsPage />} />
        <Route path="rules" element={<RulesPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to={needsSetup ? "/setup" : getToken() ? "/app" : "/login"} replace />} />
    </Routes>
  );
}
