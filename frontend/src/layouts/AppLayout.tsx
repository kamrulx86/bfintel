import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Brand } from "../components/Brand";
import GlobalSearch from "../components/GlobalSearch";
import { clearToken } from "../lib/api";

const nav = [
  { to: "/app", label: "Overview", end: true },
  { to: "/app/attacks", label: "Attacks" },
  { to: "/app/sources", label: "Source IPs" },
  { to: "/app/cases", label: "Cases" },
  { to: "/app/abuse-reports", label: "Abuse reports" },
  { to: "/app/rules", label: "Rules" },
  { to: "/app/notifications", label: "Notifications" },
  { to: "/app/settings", label: "Settings" },
];

export default function AppLayout() {
  const navigate = useNavigate();

  function logout() {
    clearToken();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 border-r border-[var(--border)] bg-surface/80 backdrop-blur-md flex flex-col">
        <div className="p-5 border-b border-[var(--border)]">
          <Brand />
        </div>
        <nav className="flex-1 p-3 space-y-0.5">
          {nav.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `block px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? "bg-primary/15 text-text ring-1 ring-primary/25"
                    : "text-muted hover:text-text hover:bg-surface2/80"
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-[var(--border)] text-xs text-muted">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
            Wazuh linked
          </span>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 shrink-0 border-b border-[var(--border)] bg-surface/60 backdrop-blur-md flex items-center justify-between px-6 gap-4">
          <GlobalSearch />
          <div className="flex items-center gap-3">
            <select className="input-field py-2 text-xs w-auto" defaultValue="24h" disabled>
              <option>Last 24 hours</option>
            </select>
            <button type="button" onClick={logout} className="btn-ghost py-2 text-xs">
              Sign out
            </button>
          </div>
        </header>
        <main className="flex-1 p-6 lg:p-8 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
