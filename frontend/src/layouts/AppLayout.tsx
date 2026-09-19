import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { Brand } from "../components/Brand";
import GlobalSearch from "../components/GlobalSearch";
import { allNavItems, mobilePrimaryNav, navSections } from "../config/navigation";
import { api, clearToken } from "../lib/api";

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="space-y-6">
      {navSections.map((section) => (
        <div key={section.label}>
          <p className="px-3 mb-2 text-[10px] uppercase tracking-wider text-muted font-medium">{section.label}</p>
          <div className="space-y-0.5">
            {section.items.map(({ to, label, end, Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                onClick={onNavigate}
                className={({ isActive }) => (isActive ? "nav-item-active" : "nav-item-idle")}
              >
                <Icon className="h-4 w-4 shrink-0 opacity-90" />
                <span className="truncate">{label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      ))}
    </nav>
  );
}

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const { data: me } = useQuery({ queryKey: ["me-header"], queryFn: () => api.me() });

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  function logout() {
    clearToken();
    navigate("/login", { replace: true });
  }

  const pageTitle = [...allNavItems]
    .sort((a, b) => b.to.length - a.to.length)
    .find((item) => (item.end ? location.pathname === item.to : location.pathname.startsWith(item.to)))?.label;

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* Desktop sidebar */}
      <aside className="sidebar-rail hidden lg:flex">
        <div className="p-4 border-b border-[var(--border)]">
          <Brand />
        </div>
        <div className="flex-1 p-3 overflow-y-auto">
          <NavLinks />
        </div>
        <div className="p-4 border-t border-[var(--border)]">
          <div className="rounded-xl border border-[var(--border)] bg-surface2/40 px-3 py-2.5 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-success shrink-0" />
            <div className="min-w-0 text-xs">
              <p className="font-medium truncate">Wazuh connected</p>
              <p className="text-muted text-[10px]">Ingestion active</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile drawer */}
      {menuOpen && (
        <button type="button" className="fixed inset-0 z-40 bg-black/60 lg:hidden" aria-label="Close menu" onClick={() => setMenuOpen(false)} />
      )}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-[min(100%,280px)] sidebar-rail transform transition-transform duration-200 lg:hidden ${
          menuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-4 border-b border-[var(--border)] flex items-center justify-between gap-2">
          <Brand compact />
          <button type="button" className="btn-ghost py-2 px-3 text-xs" onClick={() => setMenuOpen(false)}>
            Close
          </button>
        </div>
        <div className="p-3 overflow-y-auto max-h-[calc(100%-8rem)]">
          <NavLinks onNavigate={() => setMenuOpen(false)} />
        </div>
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[var(--border)] bg-surface">
          <button type="button" className="btn-ghost w-full text-sm" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 min-h-screen lg:min-h-0">
        <header className="shell-header flex-col sm:flex-row sm:h-auto sm:min-h-[3.5rem] py-3 sm:py-0 gap-3">
          <div className="flex items-center gap-3 w-full sm:flex-1 min-w-0">
            <button
              type="button"
              className="lg:hidden btn-ghost py-2 px-3 shrink-0"
              aria-label="Open menu"
              onClick={() => setMenuOpen(true)}
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                <path d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            </button>
            <div className="lg:hidden min-w-0 flex-1">
              <p className="text-[10px] uppercase tracking-wide text-muted">BFIntel</p>
              <p className="text-sm font-semibold truncate">{pageTitle ?? "Dashboard"}</p>
            </div>
            <div className="hidden lg:block flex-1 min-w-0">
              <GlobalSearch />
            </div>
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto justify-between sm:justify-end">
            <div className="lg:hidden flex-1 min-w-0">
              <GlobalSearch />
            </div>
            {me && (
              <div className="hidden md:flex items-center gap-2 pl-2 border-l border-[var(--border)] shrink-0">
                <div className="h-8 w-8 rounded-full bg-surface2 ring-1 ring-[var(--border)] grid place-items-center text-xs font-semibold">
                  {me.full_name.charAt(0).toUpperCase()}
                </div>
                <div className="leading-tight hidden xl:block">
                  <p className="text-xs font-medium max-w-[120px] truncate">{me.full_name}</p>
                  <p className="text-[10px] text-muted capitalize">{me.role}</p>
                </div>
              </div>
            )}
            <button type="button" onClick={logout} className="btn-ghost py-2 text-xs shrink-0 hidden sm:inline-flex">
              Sign out
            </button>
          </div>
        </header>

        <main className="flex-1 px-4 py-5 sm:px-6 lg:px-8 pb-24 lg:pb-8 overflow-x-hidden overflow-y-auto">
          <div className="max-w-6xl mx-auto page-stack">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile bottom nav */}
      <nav
        className="fixed bottom-0 inset-x-0 z-30 lg:hidden border-t border-[var(--border)] bg-surface/95 backdrop-blur-lg safe-bottom"
        aria-label="Primary"
      >
        <div className="grid grid-cols-5 max-w-lg mx-auto">
          {mobilePrimaryNav.map(({ to, label, shortLabel, end, Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-0.5 py-2.5 px-1 text-[10px] font-medium transition ${
                  isActive ? "text-primary" : "text-muted"
                }`
              }
            >
              <Icon className="h-5 w-5" />
              <span className="truncate max-w-full">{shortLabel ?? label}</span>
            </NavLink>
          ))}
          <button
            type="button"
            onClick={() => setMenuOpen(true)}
            className="flex flex-col items-center justify-center gap-0.5 py-2.5 px-1 text-[10px] font-medium text-muted"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
              <circle cx="5" cy="12" r="1.5" fill="currentColor" stroke="none" />
              <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
              <circle cx="19" cy="12" r="1.5" fill="currentColor" stroke="none" />
            </svg>
            More
          </button>
        </div>
      </nav>
    </div>
  );
}
