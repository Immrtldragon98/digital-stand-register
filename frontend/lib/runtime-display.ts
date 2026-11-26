export function runtimeHours(value: unknown): string {
  if ((typeof value !== "number" && typeof value !== "string") || (typeof value === "string" && !value.trim())) return "Not recorded";
  const hours = Number(value);
  if (!Number.isFinite(hours) || hours < 0) return "Not recorded";
  return `${hours.toLocaleString("en-IN", {maximumFractionDigits: 1})} h`;
}
export function runtimeLabel(value: unknown, known: unknown, complete: unknown) {
  if (complete === true) return runtimeHours(value);
  if (complete === false) {
    const observed = runtimeHours(known);
    return observed !== "Not recorded"
      ? `${observed} observed · incomplete`
      : "Not recorded · runtime history missing";
  }
  return runtimeHours(value);
}
// FastAPI's legacy naive timestamps represent UTC, not the browser's timezone.
export function apiDateMs(value: unknown): number {
  if (typeof value !== "string" || !value.trim()) return NaN;
  const timestamp = value.trim();
  return Date.parse(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(timestamp) && !/(?:Z|[+-]\d{2}:?\d{2})$/i.test(timestamp) ? timestamp + "Z" : timestamp);
}
export function installationElapsedHours(stand: any, asOf: number): number | null {
  if (runtimeHours(stand?.elapsed_hours) !== "Not recorded") {
    const hours = Number(stand.elapsed_hours);
    if (Number.isFinite(hours) && hours >= 0) return hours;
  }
  const installed = apiDateMs(stand?.installed_at ?? stand?.current_installed_at);
  if (!Number.isFinite(installed) || !Number.isFinite(asOf) || installed > asOf) return null;
  return Math.round((asOf - installed) / 3600000 * 10) / 10;
}
export function currentRunLeaders(lines: any[], asOf: number) {
  const rows = (Array.isArray(lines) ? lines : []).flatMap(line =>
    (Array.isArray(line.positions) ? line.positions : []).filter((p: any) => p.current_stand).map((p: any) => {
      const stand = p.current_stand;
      const actual = stand.runtime_complete === true && runtimeHours(stand.campaign_hours) !== "Not recorded" ? Number(stand.campaign_hours) : null;
      return {stand: stand.code, line: line.name, position: p.position_number, actual_runtime_hours: actual, elapsed_hours: installationElapsedHours(stand, asOf)};
    }));
  const order = (key: "actual_runtime_hours" | "elapsed_hours") => rows.filter(row => row[key] !== null)
    .sort((a, b) => Number(b[key]) - Number(a[key]) || String(a.line).localeCompare(String(b.line), undefined, {numeric: true}) || a.position - b.position);
  const measured = order("actual_runtime_hours");
  return {installedCount: rows.length, measuredCount: measured.length, measuredLeader: measured[0] ?? null, elapsedLeader: order("elapsed_hours")[0] ?? null};
}

export function supportedComparison(measured: any[], historical: any[], direction: "better" | "weaker") {
  const supported = (rows: any[]) => (Array.isArray(rows) ? rows : []).filter(row => row.evidence === "SUFFICIENT" && typeof row.vs_peer_pct === "number" && Number.isFinite(row.vs_peer_pct) && (direction === "better" ? row.vs_peer_pct > 0 : row.vs_peer_pct < 0))
    .sort((a, b) => direction === "better" ? b.vs_peer_pct - a.vs_peer_pct : a.vs_peer_pct - b.vs_peer_pct);
  return supported(measured)[0] ?? supported(historical)[0] ?? null;
}
export function comparisonDuration(row: any, peer = false): string {
  if (!row) return "Not recorded";
  if (row.basis === "MEASURED_MILL_RUNTIME_HOURS") return runtimeHours(peer ? row.peer_median_hours : row.median_hours);
  const value = peer ? row.peer_median_days : row.median_days;
  return typeof value === "number" && Number.isFinite(value) ? `${value.toLocaleString("en-IN", {maximumFractionDigits: 1})} d elapsed` : "Not recorded";
}
