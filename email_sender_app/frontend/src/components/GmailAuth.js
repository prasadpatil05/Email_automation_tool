import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { useSearchParams } from 'react-router-dom';

const GmailAuth = () => {
  const [error, setError] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [email, setEmail] = useState(null);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const authStatus = localStorage.getItem('isGmailAuthenticated');
    const storedEmail = localStorage.getItem('gmailEmail');

    if (authStatus === 'true') {
      setIsAuthenticated(true);
      setEmail(storedEmail);
    }

    const errorParam = searchParams.get('error');
    if (errorParam) {
      setError(errorParam);
    }
  }, [searchParams]);

  const handleGmailAuth = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/google', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start authentication');
      }

      const data = await response.json();
      if (data.auth_url) {
        window.location.href = data.auth_url;
      } else {
        throw new Error('No authentication URL received');
      }
    } catch (err) {
      console.error('Auth error:', err);
      setError(err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('isGmailAuthenticated');
    localStorage.removeItem('gmailEmail');
    setIsAuthenticated(false);
    setEmail(null);
  };

  useEffect(() => {
    const storedEmail = localStorage.getItem('gmailEmail');
    if (storedEmail) {
      console.log('Authenticated email:', storedEmail);
      setEmail(storedEmail);
    } else {
      console.log('No email found in local storage');
    }
  }, []);

  const storeEmailInBackend = async (email) => {
    try {
      const response = await fetch('http://localhost:3000/api/store_email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        throw new Error('Failed to store email');
      }

      localStorage.setItem('gmailEmail', email);
    } catch (error) {
      console.error('Error storing email:', error);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Connect Gmail Account</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {!isAuthenticated ? (
            <Button onClick={handleGmailAuth} className="w-full">
              Connect Gmail
            </Button>
          ) : (
            <div className="space-y-4">
              <Alert>
                <AlertDescription>
                  Connected as {email}
                </AlertDescription>
              </Alert>
              <Button onClick={handleLogout} variant="outline" className="w-full">
                Disconnect Gmail
              </Button>
            </div>
          )}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default GmailAuth; 