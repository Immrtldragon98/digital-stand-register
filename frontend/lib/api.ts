import { getToken } from "@/lib/auth";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "/api/v1";

type CacheEntry = { expires: number; value: unknown };
const responseCache = new Map<string, CacheEntry>();
const inflight = new Map<string, Promise<unknown>>();
const GET_TTL_MS = 30_000;
let generation = 0;
export class ApiError extends Error { constructor(message:string, public status:number){super(message);this.name="ApiError";} }

function cacheKey(endpoint: string) {
  // Read endpoints are public in DSR; endpoint is enough for a short UI cache.
  return `${generation}:${getToken()||"public"}:${endpoint}`;
}

function clearReadCache() {
  generation++;
  responseCache.clear();
}

async function request(endpoint: string, options: RequestInit) {
  const token = getToken();
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  // Cold starts may take tens of seconds; bound reads so the UI can offer Retry.
  // Never automatically retry writes: a timed-out stand change may already be saved.
  const controller = new AbortController();
  const onAbort = () => controller.abort();
  if (options.signal?.aborted) controller.abort();
  else options.signal?.addEventListener("abort", onAbort, { once: true });
  const timeout = (options.method || "GET").toUpperCase() === "GET"
    ? setTimeout(() => controller.abort(), 60_000) : undefined;
  const read = (options.method || "GET").toUpperCase() === "GET";
  try {
    for (let attempt = 0; ; attempt++) {
      let response: Response | undefined;
      try {
        response = await fetch(`${API_BASE_URL}${endpoint}`, {
          ...options, signal: controller.signal,
          headers: {
            ...(isFormData ? {} : { "Content-Type": "application/json" }),
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers,
          }, cache: "no-store",
        });
      } catch (error) {
        if (!read || controller.signal.aborted || attempt >= 3) throw error;
      }
      const html = response?.headers.get("content-type")?.includes("text/html");
      const unavailable = !response || html || [502, 503, 504].includes(response.status);
      if (read && unavailable && attempt < 3) {
        await response?.body?.cancel();
        await new Promise<void>((resolve, reject) => {
          const abort = () => { clearTimeout(delay); reject(new Error("aborted")); };
          const delay = setTimeout(() => {
            controller.signal.removeEventListener("abort", abort);
            resolve();
          }, 2000);
          if (controller.signal.aborted) abort();
          else controller.signal.addEventListener("abort", abort, { once: true });
        });
        continue;
      }
      if (!response) throw new Error("Cannot connect to the server. Check your connection; automatic reconnection will continue.");
      if (html || !response.ok) {
        const errorData = html ? {} : await response.json().catch(() => ({}));
        throw new ApiError((typeof errorData.detail === "string" ? errorData.detail : null) || (unavailable
          ? (read ? "The server is starting or unavailable. Reconnecting automatically."
            : "Could not confirm whether the change was saved. Refresh current stands and check the running stand before trying again.")
          : `API request failed with status ${response.status}`), response.status);
      }
      const contentType = response.headers.get("content-type") || "";
      if (!contentType.includes("application/json")) return response;
      // Keep the deadline active while reading the body, too.
      return await response.json();
    }
  } catch (error) {
    if (controller.signal.aborted && !options.signal?.aborted) {
      throw new Error("The connection timed out. The service may still be starting; please retry.");
    }
    throw error;
  } finally {
    if (timeout !== undefined) clearTimeout(timeout);
    options.signal?.removeEventListener("abort", onAbort);
  }
}

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const method = (options.method || "GET").toUpperCase();

  if (method !== "GET") {
    const result = await request(endpoint, options);
    // Any write can change dashboard/planning/history, so invalidate all short-lived reads.
    clearReadCache();
    return result;
  }

  if(options.signal) return request(endpoint,options);
  const readGeneration = generation;
  const key = cacheKey(endpoint);
  const now = Date.now();
  const cached = responseCache.get(key);
  if (cached && cached.expires > now) return cached.value;

  const existing = inflight.get(key);
  if (existing) return existing;

  const promise = request(endpoint, options)
    .then((value) => {
      // Do not cache Response objects such as file downloads.
      if (readGeneration===generation && !(typeof Response !== "undefined" && value instanceof Response)) {
        responseCache.set(key, { expires: Date.now() + GET_TTL_MS, value });
      }
      return value;
    })
    .finally(() => inflight.delete(key));

  inflight.set(key, promise);
  return promise;
}

export function invalidateApiCache() {
  clearReadCache();
}
