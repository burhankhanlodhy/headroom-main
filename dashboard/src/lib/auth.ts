/**
 * Mock client-side auth. Stores the signed-in user in localStorage so the
 * login → dashboard → signout loop works end-to-end today; swap the two
 * action functions for real API calls when the backend lands.
 */

export interface SessionUser {
  name: string;
  email: string;
}

const KEY = "cs_session_user";

export function getUser(): SessionUser | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as SessionUser) : null;
  } catch {
    return null;
  }
}

export function signIn(user: SessionUser): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(user));
  } catch {
    /* storage unavailable — session stays in-memory */
  }
}

export function signOut(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
