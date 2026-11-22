import { getToken } from "@/lib/auth";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

type CacheEntry = { expires: number; value: unknown };
const responseCache = new Map<string, CacheEntry>();
const inflight = new Map<string, Promise<unknown>>();
const GET_TTL_MS = 30_000;

function cacheKey(endpoint: string) {
  // Read endpoints are public in DSR; endpoint is enough for a short UI cache.
  return endpoint;
}

function clearReadCache() {
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
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      signal: controller.signal,
      headers: {
        ...(isFormData ? {} : { "Content-Type": "application/json" }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
      cache: "no-store",
    });
  } catch (error) {
    if (controller.signal.aborted && !options.signal?.aborted) {
      throw new Error("The connection timed out. The service may still be starting; please retry.");
    }
    throw error;
  } finally {
    if (timeout !== undefined) clearTimeout(timeout);
    options.signal?.removeEventListener("abort", onAbort);
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API request failed with status ${response.status}`);
  }

  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) return response;
  return response.json();
}

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const method = (options.method || "GET").toUpperCase();

  if (method !== "GET") {
    const result = await request(endpoint, options);
    // Any write can change dashboard/planning/history, so invalidate all short-lived reads.
    clearReadCache();
    return result;
  }

  const key = cacheKey(endpoint);
  const now = Date.now();
  const cached = responseCache.get(key);
  if (cached && cached.expires > now) return cached.value;

  const existing = inflight.get(key);
  if (existing) return existing;

  const promise = request(endpoint, options)
    .then((value) => {
      // Do not cache Response objects such as file downloads.
      if (!(typeof Response !== "undefined" && value instanceof Response)) {
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
