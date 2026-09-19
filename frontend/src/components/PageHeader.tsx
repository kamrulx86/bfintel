import type { ReactNode } from "react";

export default function PageHeader({
  title,
  description,
  meta,
  actions,
}: {
  title: string;
  description?: string;
  meta?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div className="min-w-0 flex-1">
        <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-text">{title}</h1>
        {description && <p className="text-muted text-sm mt-1.5 max-w-3xl leading-relaxed">{description}</p>}
        {meta && <div className="mt-2.5 flex flex-wrap gap-2">{meta}</div>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto sm:justify-end">{actions}</div>}
    </header>
  );
}
