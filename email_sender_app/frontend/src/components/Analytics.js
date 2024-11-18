import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Progress } from '../components/ui/progress';
import { BarChart, LineChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Bar, Line } from 'recharts';

const Analytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await fetch('/api/analytics');
        if (!response.ok) throw new Error('Failed to fetch analytics');
        const data = await response.json();
        setAnalytics(data);
      } catch (err) {
        setError(err.message);
      }
    };

    // Initial fetch
    fetchAnalytics();

    // Set up WebSocket connection
    const ws = new WebSocket('ws://localhost:8000/ws/analytics');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setAnalytics(data);
    };

    // Polling fallback
    const pollInterval = setInterval(fetchAnalytics, 30000);

    return () => {
      ws.close();
      clearInterval(pollInterval);
    };
  }, []);

  if (!analytics) return <div>Loading...</div>;

  const statusColors = {
    Pending: 'bg-yellow-200',
    Scheduled: 'bg-blue-200',
    Sent: 'bg-green-200',
    Failed: 'bg-red-200'
  };

  const deliveryColors = {
    'Not Sent': 'bg-gray-200',
    Delivered: 'bg-green-200',
    Opened: 'bg-blue-200',
    Bounced: 'bg-red-200',
    Failed: 'bg-red-400'
  };

  const DeliveryMetrics = ({ analytics }) => {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Delivery Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Delivery Rate</span>
              <Progress 
                value={(analytics.delivery_status.Delivered / analytics.total_emails) * 100} 
                className="w-1/2"
              />
            </div>
            <div className="flex justify-between items-center">
              <span>Open Rate</span>
              <Progress 
                value={(analytics.delivery_status.Opened / analytics.total_emails) * 100}
                className="w-1/2"
              />
            </div>
            <div className="flex justify-between items-center">
              <span>Bounce Rate</span>
              <Progress 
                value={(analytics.delivery_status.Bounced / analytics.total_emails) * 100}
                className="w-1/2 bg-red-200"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
      <Card>
        <CardHeader>
          <CardTitle>Email Status Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <p className="text-lg font-semibold">Total Emails: {analytics.total_emails}</p>
            {Object.entries(analytics.status_breakdown).map(([status, count]) => (
              <div key={status} className="flex items-center gap-2">
                <div className={`w-4 h-4 rounded ${statusColors[status]}`} />
                <span>{status}: {count}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Delivery Status</CardTitle>
        </CardHeader>
        <CardContent>
          <BarChart width={300} height={200} data={Object.entries(analytics.delivery_status).map(([status, count]) => ({
            status,
            count
          }))}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="status" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#8884d8" />
          </BarChart>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scheduled Emails</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <p>Past: {analytics.scheduled_breakdown.past}</p>
            <p>Upcoming: {analytics.scheduled_breakdown.upcoming}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Send Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <Progress 
            value={(analytics.total_sent / analytics.total_emails) * 100} 
            className="w-full"
          />
          <p className="text-sm text-gray-500 mt-2">
            {analytics.total_sent} of {analytics.total_emails} emails sent
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Hourly Send Rate</CardTitle>
        </CardHeader>
        <CardContent>
          <LineChart width={300} height={200} data={analytics.hourly_stats}>
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="sent" stroke="#8884d8" />
          </LineChart>
        </CardContent>
      </Card>

      <DeliveryMetrics analytics={analytics} />

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default Analytics;