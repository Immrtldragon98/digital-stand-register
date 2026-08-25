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
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw) as AuthUser; } catch { return null; }
}

export function setSession(token: string, user: AuthUser) {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  window.dispatchEvent(new Event("dsr-auth-change"));
}

export function clearSession() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  window.dispatchEvent(new Event("dsr-auth-change"));
}

export function canEdit(user: AuthUser | null) {
  return !!user && (user.role === "ADMIN" || user.role === "OPERATOR");
}

export function isAdmin(user: AuthUser | null) {
  return user?.role === "ADMIN";
}
