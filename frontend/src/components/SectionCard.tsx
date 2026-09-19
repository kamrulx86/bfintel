import type { ReactNode } from "react";

export default function SectionCard({
  title,
  description,
  actions,
  children,
  className = "",
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel overflow-hidden ${className}`}>
      <div className="px-4 sm:px-5 py-4 border-b border-[var(--border)] flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-text">{title}</h2>
          {description && <p className="text-xs text-muted mt-1 leading-relaxed">{description}</p>}
        </div>
        {actions && <div className="flex flex-wrap gap-2 shrink-0">{actions}</div>}
      </div>
      <div className="px-4 sm:px-5 pb-4 sm:pb-5">{children}</div>
    </section>
  );
}
