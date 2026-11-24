export type AuthUser = {
  id: number;
  username: string;
  role_id: number;
  role: "ADMIN" | "OPERATOR";
};

const TOKEN_KEY = "dsr_access_token";
const USER_KEY = "dsr_user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try { return window.localStorage.getItem(TOKEN_KEY); } catch { return null; }
}

export function getUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try { const raw = window.localStorage.getItem(USER_KEY); return raw ? JSON.parse(raw) as AuthUser : null; } catch { return null; }
}

export function setSession(token: string, user: AuthUser) {
  try { window.localStorage.setItem(TOKEN_KEY, token); window.localStorage.setItem(USER_KEY, JSON.stringify(user)); } catch { throw new Error("Browser storage is unavailable. Enable local storage to sign in."); }
  window.dispatchEvent(new Event("dsr-auth-change"));
}

export function clearSession() {
  if (typeof window === "undefined") return;
  try { window.localStorage.removeItem(TOKEN_KEY); window.localStorage.removeItem(USER_KEY); } catch { /* Storage may have been revoked. */ }
  window.dispatchEvent(new Event("dsr-auth-change"));
}

export function canEdit(user: AuthUser | null) {
  return !!user && (user.role === "ADMIN" || user.role === "OPERATOR");
}

export function isAdmin(user: AuthUser | null) {
  return user?.role === "ADMIN";
}
