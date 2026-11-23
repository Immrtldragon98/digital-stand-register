import { fetchApi, invalidateApiCache } from "@/lib/api";

export async function saveStandChange(payload: {
  position_id: number;
  removed_stand_code: string;
  installed_stand_code: string;
  [key: string]: unknown;
}) {
  // Wake the API and verify fresh state before sending a write. Reads may retry;
  // the write must be sent once because a lost response can hide a saved change.
  invalidateApiCache();
  const [lines, stands] = await Promise.all([
    fetchApi("/dashboard/"), fetchApi("/stands/"),
  ]);
  const position = lines.flatMap((line: any) => line.positions || [])
    .find((pos: any) => pos.id === payload.position_id);
  if (position?.current_stand?.code !== payload.removed_stand_code) {
    throw new Error("The running stand has changed. Refresh current stands before submitting again.");
  }
  const replacement = stands.find((stand: any) => stand.code === payload.installed_stand_code);
  if (!replacement || replacement.current_status !== "READY" || replacement.current_position_id != null) {
    throw new Error("The replacement is no longer available in Ready. Refresh current stands and select a Ready stand.");
  }
  return fetchApi("/operations/stands/change", { method: "POST", body: JSON.stringify(payload) });
}
