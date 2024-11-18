import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useSearchParams, Navigate } from 'react-router-dom';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './components/ui/tabs';
import DataUpload from './components/DataUpload';
import SendEmails from './components/SendEmails';
import Analytics from './components/Analytics';
import { Alert, AlertDescription } from './components/ui/alert';
import { fetchAnalytics } from './utils/api';
import GmailAuth from './components/GmailAuth';
import AuthCallback from './components/AuthCallback';

function MainApp() {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'gmail-auth';

  useEffect(() => {
    const fetchAnalyticsData = async () => {
      try {
        const data = await fetchAnalytics();
        setAnalytics(data);
      } catch (err) {
        setError(err.message);
      }
    };

    if (activeTab === 'analytics') {
      fetchAnalyticsData();
    }
  }, [activeTab]);

  const handleTabChange = (value) => {
    setSearchParams({ tab: value });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <h1 className="text-3xl font-bold text-gray-900">
            Email Campaign Dashboard
          </h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 px-4">
        <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-4">
          <TabsList>
            <TabsTrigger value="gmail-auth">Gmail Connection</TabsTrigger>
            <TabsTrigger value="upload">Upload Data</TabsTrigger>
            <TabsTrigger value="send">Send Emails</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="gmail-auth">
            <GmailAuth />
          </TabsContent>
          
          <TabsContent value="upload">
            <DataUpload />
          </TabsContent>

          <TabsContent value="send">
            <SendEmails />
          </TabsContent>

          <TabsContent value="analytics">
            <Analytics analytics={analytics} />
          </TabsContent>
        </Tabs>

        {error && (
          <Alert variant="destructive" className="mt-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/" element={<MainApp />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
