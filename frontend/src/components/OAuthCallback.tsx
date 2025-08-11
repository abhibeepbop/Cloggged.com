import React, { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { setAuth } from '../utils/auth';

export function OAuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const ranOnceRef = useRef(false);

  useEffect(() => {
    const handleOAuthCallback = async () => {
      // Get the code and state from URL parameters
      const urlParams = new URLSearchParams(location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');

      if (code && state) {
        // One-shot guard: avoid duplicate exchanges in React Strict Mode
        const key = `exchanged:${code}:${state}`;
        if (ranOnceRef.current || sessionStorage.getItem(key) === '1') {
          return;
        }
        ranOnceRef.current = true;
        sessionStorage.setItem(key, '1');
        try {
          // Exchange code for tokens using our backend
          const response = await fetch('http://localhost:8000/exchange-code', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ code, state })
          });
          
          if (response.ok) {
            const data = await response.json();
            console.log('Backend response:', data);
            if (data.redirect_url) {
              console.log('Redirecting to:', data.redirect_url);
              // Fetch fresh user data from backend to ensure latest subscription/trial flags
              try {
                if (data.user_id) {
                  const fresh = await fetch(`http://localhost:8000/debug-user/${data.user_id}`);
                  const freshJson = await fresh.json();
                  if (freshJson && freshJson.success && freshJson.user_data) {
                    setAuth({ ...(freshJson.user_data || {}), user_id: data.user_id });
                    console.log('Stored fresh user data in localStorage');
                  } else if (data.user_data) {
                    setAuth(data.user_data);
                  }
                } else if (data.user_data) {
                  setAuth(data.user_data);
                }
              } catch (e) {
                if (data.user_data) setAuth(data.user_data);
              }
              window.location.href = data.redirect_url;
            } else {
              console.log('No redirect_url, going to pricing');
              navigate('/');
            }
          } else {
            console.error('Failed to exchange code');
            navigate('/');
          }
        } catch (error) {
          console.error('OAuth callback error:', error);
          navigate('/');
        }
      } else {
        navigate('/');
      }
    };

    handleOAuthCallback();
  }, [navigate, location]);

  return (
    <div className="min-h-screen bg-navy-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-navy-800 mx-auto mb-4"></div>
        <p className="text-navy-900">Signing you in...</p>
      </div>
    </div>
  );
} 