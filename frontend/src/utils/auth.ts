import { API_BASE } from './api';
export type UserData = {
  subscription_status?: string;
  payment_completed?: boolean;
  subscribed?: boolean;
  free_trial?: boolean;
  trial_end?: number; // unix seconds
  [key: string]: any;
};

const AUTH_KEY = 'isAuthenticated';
const USER_KEY = 'userData';

export function getStoredUser(): UserData | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  return localStorage.getItem(AUTH_KEY) === 'true' && !!getStoredUser();
}

export function setAuth(userData: UserData): void {
  localStorage.setItem(AUTH_KEY, 'true');
  localStorage.setItem(USER_KEY, JSON.stringify(userData));
}

export function clearAuth(): void {
  localStorage.removeItem(AUTH_KEY);
  localStorage.removeItem(USER_KEY);
}

// Attempt to populate local auth from server session (httpOnly cookie)
export async function syncAuthFromSession(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/session/me`, { credentials: 'include' });
    if (!res.ok) {
      clearAuth();
      return false;
    }
    const data = await res.json();
    if (data && data.user_id && data.user_data) {
      setAuth({ ...data.user_data, user_id: data.user_id });
      return true;
    }
    clearAuth();
    return false;
  } catch {
    return false;
  }
}

export function canAccessDashboard(user: UserData | null): boolean {
  if (!user) return false;
  const nowSec = Math.floor(Date.now() / 1000);
  const toBool = (v: any) => {
    if (typeof v === 'boolean') return v;
    if (typeof v === 'number') return v === 1;
    if (typeof v === 'string') return ['true', '1', 'yes', 'y'].includes(v.trim().toLowerCase());
    return false;
  };
  const hasActiveSubscription =
    toBool(user.subscribed) ||
    (user.subscription_status === 'active' && toBool(user.payment_completed));
  const inFreeTrial =
    toBool(user.free_trial) || (typeof user.trial_end === 'number' && user.trial_end > nowSec);
  return !!(hasActiveSubscription || inFreeTrial);
}

