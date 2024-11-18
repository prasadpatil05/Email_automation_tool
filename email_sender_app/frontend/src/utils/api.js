const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api' 
  : 'http://localhost:8000/api';

export const fetchAnalytics = async () => {
  const response = await fetch(`${API_BASE_URL}/analytics`, {
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch analytics');
  }

  return response.json();
}; 