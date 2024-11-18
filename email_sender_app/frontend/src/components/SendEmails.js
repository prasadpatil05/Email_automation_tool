// SendEmails.js
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';

const SendEmails = () => {
  const [emailConfig, setEmailConfig] = useState({
    promptTemplate: '',
    scheduleTime: '',
    batchSize: 50,
    intervalMinutes: 60,
    throttleRate: 'hourly',
    subject: ''
  });
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [availableFields, setAvailableFields] = useState([]);
  const [csvData, setCsvData] = useState(null);
  const [promptTemplate, setPromptTemplate] = useState('');

  useEffect(() => {
    fetchCSVFields();
    fetchCSVPreview();
  }, []);

  const fetchCSVFields = async () => {
    try {
      const response = await fetch('/api/get_csv_fields');
      if (!response.ok) throw new Error('Failed to fetch fields');
      const data = await response.json();
      setAvailableFields(data.fields);
    } catch (err) {
      setError('Failed to load template fields');
    }
  };

  const fetchCSVPreview = async () => {
    try {
      const response = await fetch('/api/get_csv_preview');
      if (!response.ok) throw new Error('Failed to fetch CSV preview');
      const data = await response.json();
      setCsvData(data.preview);
    } catch (err) {
      setError('Failed to load CSV preview');
    }
  };

  const handleConfigChange = (field, value) => {
    setEmailConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handlePromptChange = (e) => {
    setPromptTemplate(e.target.value);
  };

  const insertField = (field) => {
    const fieldPlaceholder = `{${field}}`;
    setPromptTemplate(prev => prev + fieldPlaceholder);
  };

  const generatePreview = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/generate_email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt_template: promptTemplate,
          subject: emailConfig.subject,
          sample_data: csvData && csvData.length > 0 ? csvData[0] : {}
        })
      });
      
      if (!response.ok) throw new Error('Failed to generate preview');
      const data = await response.json();
      setPreview(data.generated_content);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const response = await fetch('/api/schedule_emails', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt_template: promptTemplate,
          subject: emailConfig.subject,
          schedule_time: emailConfig.scheduleTime,
          batch_size: emailConfig.batchSize,
          interval_minutes: emailConfig.intervalMinutes,
        }),
      });

      if (!response.ok) throw new Error('Failed to schedule emails');
      const data = await response.json();
      setSuccess(`Successfully scheduled ${data.total_scheduled} emails`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Schedule Email Campaign</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            {/* Email Subject */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Email Subject</label>
              <Input
                value={emailConfig.subject}
                onChange={(e) => handleConfigChange('subject', e.target.value)}
                placeholder="Enter email subject"
              />
            </div>

            {/* Email Template */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Email Prompt Template</label>
              <textarea
                value={promptTemplate}
                onChange={handlePromptChange}
                className="w-full border rounded p-2"
                rows="4"
                placeholder="Enter your email template here..."
              />
            </div>

            <div>
              <h4 className="text-sm font-medium">Available Fields</h4>
              {availableFields.map(field => (
                <button
                  key={field}
                  onClick={() => insertField(field)}
                  className="mr-2 mb-2 bg-blue-500 text-white rounded px-2 py-1"
                >
                  {field}
                </button>
              ))}
            </div>

            {/* Schedule Options */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Schedule Time</label>
                <Input
                  type="datetime-local"
                  value={emailConfig.scheduleTime}
                  onChange={(e) => handleConfigChange('scheduleTime', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Batch Size</label>
                <Input
                  type="number"
                  value={emailConfig.batchSize}
                  onChange={(e) => handleConfigChange('batchSize', parseInt(e.target.value))}
                  min="1"
                />
              </div>
            </div>
          </div>

          {/* Preview Display Section */}
          {preview && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-sm font-medium mb-2">Email Preview:</h3>
              <div className="whitespace-pre-wrap text-sm text-gray-600">
                {preview}
              </div>
            </div>
          )}

          {/* Preview and Submit buttons */}
          <div className="space-y-4">
            <Button
              type="button"
              onClick={generatePreview}
              disabled={loading}
              variant="outline"
            >
              Generate Preview
            </Button>

            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Scheduling...' : 'Schedule Campaign'}
            </Button>
          </div>

          {/* Status messages */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {success && (
            <Alert>
              <AlertDescription>{success}</AlertDescription>
            </Alert>
          )}
        </form>
      </CardContent>
    </Card>
  );
};

export default SendEmails;