import { Brand } from "../components/Brand";

export default function AuthLayout({
  title,
  subtitle,
  children,
  wide,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  wide?: boolean;
}) {
  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      <aside className="hidden lg:flex lg:w-[42%] xl:w-[44%] flex-col justify-between p-10 border-r border-[var(--border)] bg-surface/40">
        <Brand />
        <div className="space-y-6 max-w-md">
          <h1 className="text-3xl font-semibold tracking-tight leading-tight">
            Brute-force intelligence for modern SOCs
          </h1>
          <p className="text-muted text-sm leading-relaxed">
            Correlate authentication events, score risk with evidence, and respond — without replacing Wazuh.
          </p>
          <ul className="space-y-3 text-sm text-muted">
            {["Attack session correlation", "Source IP investigation", "Auditable automation"].map((t) => (
              <li key={t} className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                {t}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-muted font-mono">TTP · Team Phoenix</p>
      </aside>

      <main className="flex-1 flex items-center justify-center p-6 sm:p-10">
        <div className={`w-full ${wide ? "max-w-xl" : "max-w-md"}`}>
          <div className="lg:hidden mb-8">
            <Brand />
          </div>
          <div className="panel p-8 sm:p-9">
            <p className="text-xs uppercase tracking-widest text-primary font-medium mb-2">Secure access</p>
            <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
            {subtitle && <p className="text-muted text-sm mt-2 mb-6">{subtitle}</p>}
            {!subtitle && <div className="mb-6" />}
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
