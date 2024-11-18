import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      
      if (code) {
        try {
          const response = await fetch(`/api/auth/callback?code=${code}`);
          const data = await response.json();
          
          // Store auth status in localStorage
          localStorage.setItem('isGmailAuthenticated', 'true');
          localStorage.setItem('gmailEmail', data.email);
          
          // Store email in Redis
          await fetch('/api/store_email', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: data.email }),
          });

          // Redirect back to Gmail auth tab
          navigate('/?tab=gmail-auth');
        } catch (error) {
          console.error('Auth callback error:', error);
          navigate('/?tab=gmail-auth&error=Authentication failed');
        }
      }
    };

    handleCallback();
  }, [navigate]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <p>Processing authentication...</p>
    </div>
  );
};

export default AuthCallback;