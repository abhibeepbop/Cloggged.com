import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export function OAuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleOAuthCallback = async () => {
      // Get the code and state from URL parameters
      const urlParams = new URLSearchParams(location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');

      if (code && state) {
        try {
          // Exchange code for tokens using our backend
          const response = await fetch('http://localhost:8000/exchange-code', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code, state })
          });
          
          if (response.ok) {
            const data = await response.json();
            console.log('Backend response:', data);
            if (data.redirect_url) {
              // Backend determined where to redirect
              console.log('Redirecting to:', data.redirect_url);
              
              // If going to dashboard, store user data
              if (data.redirect_url.includes('/dashboard') && data.user_data) {
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('userData', JSON.stringify(data.user_data));
                console.log('Stored user data in localStorage');
              }
              
              window.location.href = data.redirect_url;
            } else {
              // Fallback
              console.log('No redirect_url, going to pricing');
              navigate('/pricing');
            }
          } else {
            console.error('Failed to exchange code');
            navigate('/pricing');
          }
        } catch (error) {
          console.error('OAuth callback error:', error);
          navigate('/pricing');
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