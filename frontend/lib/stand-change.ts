import { ApiError, fetchApi, invalidateApiCache } from "@/lib/api";

const pending = new Map<string,string>();

export async function saveStandChange(payload: {
  position_id: number;
  removed_stand_code: string;
  installed_stand_code: string;
  [key: string]: unknown;
}) {
  // Wake the API and verify fresh state before sending a write. Reads may retry;
  // the write must be sent once because a lost response can hide a saved change.
  const body=JSON.stringify(payload);
  const previous=pending.get(body);
  const key=previous||`change-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
  invalidateApiCache();
  if(previous){
    try {const result=await fetchApi(`/operations/commands/${previous}`);pending.delete(body);return result;}
    catch(error){if(!(error instanceof ApiError)||error.status!==404)throw error;}
  }
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
  pending.set(body,key);
  const result=await fetchApi("/operations/stands/change", {method:"POST",body,headers:{"Idempotency-Key":key}});
  pending.delete(body);
  return result;
}
