import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000'
});

const DataUpload = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [preview, setPreview] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && !selectedFile.name.endsWith('.csv')) {
      setError('Please select a CSV file');
      return;
    }
    setFile(selectedFile);
    setError(null);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file first');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await api.post('/api/upload_csv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });

      if (response.data) {
        setSuccess(`Successfully uploaded ${response.data.total_records} records`);
        setFile(null);
        // Reset file input
        const fileInput = document.querySelector('input[type="file"]');
        if (fileInput) fileInput.value = '';
        await fetchPreview();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error uploading file');
    } finally {
      setLoading(false);
    }
  };

  const fetchPreview = async () => {
    try {
      const response = await api.get('/api/get_csv_preview');
      if (response.data) {
        setPreview(response.data.preview);
      }
    } catch (err) {
      setError('Failed to load preview');
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Upload Data</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleUpload} className="space-y-4">
          <input
            type="file"
            onChange={handleFileChange}
            accept=".csv"
            className="w-full"
          />
          
          {file && (
            <p className="text-sm text-gray-500">Selected file: {file.name}</p>
          )}
          
          <Button 
            type="submit" 
            disabled={!file || loading}
            className="w-full"
          >
            {loading ? 'Uploading...' : 'Upload'}
          </Button>

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

          {preview && (
            <div className="mt-6">
              <h3 className="text-sm font-medium mb-2">Data Preview:</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead>
                    <tr>
                      {Object.keys(preview[0]).map(header => (
                        <th key={header} className="px-4 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {preview.map((row, idx) => (
                      <tr key={idx}>
                        {Object.values(row).map((value, i) => (
                          <td key={i} className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                            {value}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
};

export default DataUpload;