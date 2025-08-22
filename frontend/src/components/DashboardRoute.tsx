import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { API_BASE } from '../utils/api';
import { setAuth, getStoredUser, canAccessDashboard } from '../utils/auth';

export function DashboardRoute({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<'checking' | 'allowed' | 'denied'>('checking');

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/session/me`, { credentials: 'include' });
        if (!res.ok) throw new Error('no session');
        const data = await res.json();
        if (data && data.user_id && data.user_data) {
          setAuth({ ...data.user_data, user_id: data.user_id });
          const allowed = canAccessDashboard(getStoredUser());
          if (mounted) setStatus(allowed ? 'allowed' : 'denied');
          return;
        }
      } catch {}
      if (mounted) setStatus('denied');
    })();
    return () => { mounted = false; };
  }, []);

  if (status === 'checking') return <div />; // minimal splash
  if (status === 'allowed') return <>{children}</>;
  return <Navigate to="/" replace />;
}


