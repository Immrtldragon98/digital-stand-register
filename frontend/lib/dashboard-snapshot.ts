// Read-only continuity. Never use this snapshot to validate a stand change.
export type DashboardLine = { id: number; name: string; positions: {
  id: number; position_number: number; current_stand: null | { id: number; code: string; [key: string]: unknown };
  [key: string]: unknown;
}[] };
export type DashboardSnapshot = { savedAt: number; lines: DashboardLine[] };
type StorageLike = Pick<Storage, "getItem" | "setItem">;

export function isDashboard(value: unknown): value is DashboardLine[] {
  return Array.isArray(value) && value.every(line => line && Number.isInteger(line.id)
    && typeof line.name === "string" && Array.isArray(line.positions)
    && line.positions.every((p: any) => p && Number.isInteger(p.id) && Number.isInteger(p.position_number)
      && (p.current_stand === null || (p.current_stand && Number.isInteger(p.current_stand.id)
        && typeof p.current_stand.code === "string"))));
}
function key(api: string) { return `dsr:dashboard:v1:${api}`; }
export function readSnapshot(storage: StorageLike, api: string): DashboardSnapshot | null {
  try {
    const value = JSON.parse(storage.getItem(key(api)) || "null");
    return value && Number.isFinite(value.savedAt) && value.savedAt > 0
      && value.savedAt <= Date.now() + 60_000 && isDashboard(value.lines) ? value : null;
  } catch { return null; }
}
export function saveSnapshot(storage: StorageLike, api: string, snapshot: DashboardSnapshot) {
  if (!isDashboard(snapshot.lines)) return;
  try { storage.setItem(key(api), JSON.stringify(snapshot)); } catch { /* Storage may be full or blocked. */ }
}
