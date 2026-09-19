type Props = {
  hours: string;
  onHoursChange: (v: string) => void;
  riskLevel: string;
  onRiskLevelChange: (v: string) => void;
  service: string;
  onServiceChange: (v: string) => void;
  query: string;
  onQueryChange: (v: string) => void;
  country?: string;
  onCountryChange?: (v: string) => void;
  showQuery?: boolean;
};

export default function TableFilters({
  hours,
  onHoursChange,
  riskLevel,
  onRiskLevelChange,
  service,
  onServiceChange,
  query,
  onQueryChange,
  country = "",
  onCountryChange,
  showQuery = true,
}: Props) {
  return (
    <div className="panel p-4">
      <p className="text-xs font-medium text-muted mb-3">Filters</p>
      <div className="filter-grid">
        <label className="text-xs text-muted flex flex-col gap-1.5 min-w-0">
          Time range
          <select className="input-field py-2 text-sm" value={hours} onChange={(e) => onHoursChange(e.target.value)}>
            <option value="">All time</option>
            <option value="24">Last 24h</option>
            <option value="168">Last 7d</option>
            <option value="720">Last 30d</option>
          </select>
        </label>
        <label className="text-xs text-muted flex flex-col gap-1.5 min-w-0">
          Risk level
          <select className="input-field py-2 text-sm" value={riskLevel} onChange={(e) => onRiskLevelChange(e.target.value)}>
            <option value="">Any</option>
            <option value="low">Low+</option>
            <option value="medium">Medium+</option>
            <option value="high">High+</option>
            <option value="critical">Critical</option>
          </select>
        </label>
        <label className="text-xs text-muted flex flex-col gap-1.5 min-w-0">
          Service
          <select className="input-field py-2 text-sm" value={service} onChange={(e) => onServiceChange(e.target.value)}>
            <option value="">Any</option>
            <option value="ssh">SSH</option>
            <option value="rdp">RDP</option>
            <option value="ftp">FTP</option>
            <option value="web">Web</option>
            <option value="smtp">SMTP</option>
          </select>
        </label>
        {onCountryChange && (
          <label className="text-xs text-muted flex flex-col gap-1.5 min-w-0">
            Country
            <input
              className="input-field py-2 text-sm"
              value={country}
              onChange={(e) => onCountryChange(e.target.value)}
              placeholder="BD, Bangladesh"
            />
          </label>
        )}
        {showQuery && (
          <label className="text-xs text-muted flex flex-col gap-1.5 min-w-0 xl:col-span-2">
            IP contains
            <input
              className="input-field py-2 text-sm font-mono"
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              placeholder="203.0.113"
            />
          </label>
        )}
      </div>
    </div>
  );
}
